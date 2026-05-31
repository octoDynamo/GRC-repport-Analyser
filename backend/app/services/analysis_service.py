"""Analysis service — orchestrates the full AI analysis pipeline."""
import asyncio
import uuid

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.mistral_client import call_mistral_json, call_mistral
from app.ai.parsers.document_parser import extract_text, chunk_text
from app.ai.prompts.risk_prompts import build_risk_prompt
from app.ai.prompts.compliance_prompts import build_compliance_prompt, FRAMEWORKS
from app.ai.prompts.recommendation_prompts import build_recommendation_prompt
from app.ai.prompts.summary_prompts import build_summary_prompt
from app.ai.rag.vector_store import index_document_chunks
from app.models.analyse import Analyse
from app.models.risque import Risque
from app.models.conformite import ResultatConformite
from app.models.recommandation import Recommandation
from app.models.rapport import Rapport
from app.models.utilisateur import Utilisateur
from app.services.report_service import get_report_bytes


def _sample_text(text: str, max_chars: int = 20000) -> str:
    """Sample from beginning, middle, and end so large documents are covered evenly."""
    if len(text) <= max_chars:
        return text
    part = max_chars // 3
    mid_start = (len(text) - part) // 2
    return (
        text[:part]
        + "\n\n[... middle section ...]\n\n"
        + text[mid_start : mid_start + part]
        + "\n\n[... end section ...]\n\n"
        + text[-part:]
    )


def _full_or_sampled(text: str, max_chars: int = 30000) -> str:
    """Return full text if within limit, otherwise sample intelligently."""
    if len(text) <= max_chars:
        return text
    return _sample_text(text, max_chars)


VALID_CATEGORIES = {"CYBER", "OPERATIONNEL", "LEGAL", "FINANCIER", "RH"}
MIN_CONFIDENCE = 30  # lowered — explicit scanner findings are always trustworthy


def _as_dict(data: object) -> dict:
    """Normalize a Mistral JSON response to a dict.

    Mistral occasionally wraps the object in a list ([{...}]) even when
    json_object format is requested. This unwraps that case silently.
    """
    if isinstance(data, dict):
        return data
    if isinstance(data, list) and data and isinstance(data[0], dict):
        return data[0]
    return {}


def compute_severity(score: float) -> str:
    if score >= 20:
        return "CRITIQUE"
    elif score >= 12:
        return "ELEVE"
    elif score >= 6:
        return "MOYEN"
    return "FAIBLE"


async def run_analysis(
    db: AsyncSession,
    rapport: Rapport,
    user: Utilisateur,
    analyse_id: uuid.UUID,
) -> None:
    """
    Background task that runs the full AI analysis pipeline.
    Updates the analyse record in the database as it progresses.
    """
    # Retrieve the analyse record
    result = await db.execute(select(Analyse).where(Analyse.id == analyse_id))
    analyse = result.scalar_one()

    try:
        await asyncio.wait_for(_run_analysis_pipeline(db, rapport, analyse, analyse_id, user), timeout=600)
    except asyncio.TimeoutError:
        logger.error(f"Analysis {analyse_id} timed out after 10 minutes")
        analyse.statut = "erreur"
        rapport.statut = "erreur"
        await db.flush()
    except Exception as exc:
        logger.error(f"Analysis {analyse_id} failed: {exc}")
        analyse.statut = "erreur"
        rapport.statut = "erreur"
        await db.flush()


async def _run_analysis_pipeline(
    db: AsyncSession,
    rapport: Rapport,
    analyse: Analyse,
    analyse_id: uuid.UUID,
    user: Utilisateur,
) -> None:
    try:
        # Step 1: Download document from MinIO and extract text
        file_bytes = await get_report_bytes(rapport.chemin)
        text = await asyncio.to_thread(extract_text, file_bytes, rapport.format)
        logger.info(f"Extracted {len(text)} chars from {rapport.nom}")

        # Phase 1: Parallelize ChromaDB index, Risk extraction, and all Compliance checks
        chunks = await asyncio.to_thread(chunk_text, text)

        risk_text = _full_or_sampled(text, max_chars=20000)
        comp_text = _full_or_sampled(text, max_chars=15000)

        task_chroma = index_document_chunks(str(analyse_id), chunks)

        risk_system, risk_user = build_risk_prompt(risk_text)
        task_risk = call_mistral_json(risk_system, risk_user)

        tasks_comp = []
        for framework in FRAMEWORKS:
            comp_system, comp_user = build_compliance_prompt(comp_text, framework)
            tasks_comp.append(call_mistral_json(comp_system, comp_user))
            
        phase1_results = await asyncio.gather(task_chroma, task_risk, *tasks_comp, return_exceptions=True)
        
        # Handle Chroma result
        if isinstance(phase1_results[0], Exception):
            logger.error(f"ChromaDB indexing failed: {phase1_results[0]}")
        else:
            logger.info(f"Indexed {len(chunks)} chunks into ChromaDB")

        # Handle Risk result
        if isinstance(phase1_results[1], Exception):
            logger.error(f"Risk extraction failed: {phase1_results[1]}")
            risques_raw = []
        else:
            risques_raw = _as_dict(phase1_results[1]).get("risques") or []

        saved_risques: list[Risque] = []
        risk_label_to_id: dict[str, uuid.UUID] = {}
        seen_libelles: set[str] = set()

        for r in risques_raw:
            try:
                confiance = int(r.get("confiance", 100))
                if confiance < MIN_CONFIDENCE:
                    logger.debug(f"Skipping low-confidence risk (confiance={confiance}): {r.get('libelle')}")
                    continue

                libelle = str(r.get("libelle", "Risque inconnu"))[:500].strip()
                libelle_key = libelle.lower()
                if libelle_key in seen_libelles:
                    logger.debug(f"Skipping duplicate risk: {libelle}")
                    continue
                seen_libelles.add(libelle_key)

                prob = max(1, min(5, int(r.get("probabilite", 3))))
                impact = max(1, min(5, int(r.get("impact", 3))))
                score = float(prob * impact)

                categorie = str(r.get("categorie", "OPERATIONNEL")).upper()
                if categorie not in VALID_CATEGORIES:
                    categorie = "OPERATIONNEL"

                risque = Risque(
                    id=uuid.uuid4(),
                    analyse_id=analyse_id,
                    libelle=libelle,
                    description=str(r.get("description", "")),
                    categorie=categorie,
                    probabilite=prob,
                    impact=impact,
                    score_risque=score,
                    severite=compute_severity(score),
                    section_source=str(r.get("section_source", ""))[:500],
                )
                db.add(risque)
                saved_risques.append(risque)
                risk_label_to_id[risque.libelle] = risque.id
            except Exception as e:
                logger.warning(f"Skipping malformed risk: {e}")

        logger.info(f"Saved {len(saved_risques)} risks")

        # Handle Compliance results
        compliance_scores: dict[str, float] = {}
        for i, framework in enumerate(FRAMEWORKS):
            comp_res = phase1_results[i + 2]
            if isinstance(comp_res, Exception):
                logger.error(f"Compliance check failed for {framework}: {comp_res}")
                compliance_scores[framework] = 0.0
                continue
                
            comp_data = _as_dict(comp_res)
            try:
                global_rate = float(comp_data.get("taux_global", 0))
                compliance_scores[framework] = global_rate

                for domaine in (comp_data.get("domaines") or []):
                    raw_statut = str(domaine.get("statut", "PARTIEL")).upper()
                    if raw_statut not in ["CONFORME", "NON_CONFORME", "PARTIEL"]:
                        raw_statut = "PARTIEL"

                    conformite = ResultatConformite(
                        id=uuid.uuid4(),
                        analyse_id=analyse_id,
                        referentiel=framework,
                        domaine=str(domaine.get("nom", ""))[:500],
                        statut=raw_statut,
                        ecart=str(domaine.get("ecart", "")),
                        taux_conformite=float(domaine.get("taux", 0)),
                    )
                    db.add(conformite)
            except Exception as e:
                logger.error(f"Compliance check post-processing failed for {framework}: {e}")
                compliance_scores[framework] = 0.0

        await db.flush()

        # Phase 2: Parallelize Recommendations and Executive summary
        risks_summary = "\n".join([
            f"- [{r.severite}] {r.libelle} (Score: {r.score_risque}, Catégorie: {r.categorie})\n"
            f"  Description: {r.description[:200] if r.description else 'N/A'}"
            for r in saved_risques
        ])
        rec_system, rec_user = build_recommendation_prompt(
            risks_summary, text_excerpt=_full_or_sampled(text, max_chars=4000)
        )
        task_rec = call_mistral_json(rec_system, rec_user)

        # Build severity breakdown and top risks for richer summary
        risks_by_severity = {}
        for r in saved_risques:
            risks_by_severity[r.severite] = risks_by_severity.get(r.severite, 0) + 1

        top_risks = [
            {"libelle": r.libelle, "severite": r.severite, "score": r.score_risque}
            for r in sorted(saved_risques, key=lambda x: x.score_risque, reverse=True)[:5]
        ]

        summary_system, summary_user = build_summary_prompt(
            text=text,
            risks_count=len(saved_risques),
            iso_score=compliance_scores.get("ISO27001", 0),
            rgpd_score=compliance_scores.get("RGPD", 0),
            loi_score=compliance_scores.get("LOI0908", 0),
            risks_by_severity=risks_by_severity,
            top_risks=top_risks,
            recs_count=len(saved_risques),  # one recommendation generated per risk
        )
        task_summary = call_mistral(summary_system, summary_user, temperature=0.2)

        phase2_results = await asyncio.gather(task_rec, task_summary, return_exceptions=True)

        if isinstance(phase2_results[0], Exception):
            logger.error(f"Recommendations mapping failed: {phase2_results[0]}")
            rec_data = {"recommandations": []}
        else:
            rec_data = _as_dict(phase2_results[0])

        summary = phase2_results[1] if not isinstance(phase2_results[1], Exception) else "Résumé exécutif indisponible suite à une erreur."

        for rec in (rec_data.get("recommandations") or []):
            try:
                risque_libelle = rec.get("risque_lie", "")
                risque_id = risk_label_to_id.get(risque_libelle)
                if not risque_id and risque_libelle:
                    for label, rid in risk_label_to_id.items():
                        if risque_libelle.lower() in label.lower() or label.lower() in risque_libelle.lower():
                            risque_id = rid
                            break

                recommandation = Recommandation(
                    id=uuid.uuid4(),
                    analyse_id=analyse_id,
                    risque_id=risque_id,
                    libelle=str(rec.get("libelle", ""))[:500],
                    description=str(rec.get("description", "")),
                    priorite=str(rec.get("priorite", "MOYENNE")).upper(),
                    type_action=str(rec.get("type_action", "LONG_TERME")).upper(),
                    effort_estime=str(rec.get("effort_estime", "MOYEN")).upper(),
                    statut="A_FAIRE",
                )
                db.add(recommandation)
            except Exception as e:
                logger.warning(f"Skipping malformed recommendation: {e}")

        # Step 7: Compute maturity score (average of compliance scores)
        all_scores = list(compliance_scores.values())
        maturity = sum(all_scores) / len(all_scores) if all_scores else 0.0

        # Update analyse record
        analyse.resume_executif = summary
        analyse.score_maturite = round(maturity, 2)
        analyse.statut = "termine"
        await db.flush()

        # Update rapport status
        rapport.statut = "termine"
        await db.flush()

        logger.info(f"Analysis {analyse_id} completed successfully")

    except Exception as exc:
        logger.error(f"Analysis pipeline error: {exc}")
        analyse.statut = "erreur"
        rapport.statut = "erreur"
        await db.flush()
        raise  # re-raise so the outer wait_for can catch it


async def get_analyse(db: AsyncSession, analyse_id: uuid.UUID) -> Analyse | None:
    result = await db.execute(select(Analyse).where(Analyse.id == analyse_id))
    return result.scalar_one_or_none()


async def list_analyses_for_rapport(db: AsyncSession, rapport_id: uuid.UUID) -> list[Analyse]:
    result = await db.execute(
        select(Analyse).where(Analyse.rapport_id == rapport_id).order_by(Analyse.created_at.desc())
    )
    return list(result.scalars().all())
