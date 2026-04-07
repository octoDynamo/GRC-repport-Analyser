"""Analysis service — orchestrates the full AI analysis pipeline."""
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
        # Step 1: Download document from MinIO and extract text
        file_bytes = await get_report_bytes(rapport.chemin)
        text = extract_text(file_bytes, rapport.format)
        logger.info(f"Extracted {len(text)} chars from {rapport.nom}")

        # Step 2: Index chunks in ChromaDB for RAG
        chunks = chunk_text(text)
        await index_document_chunks(str(analyse_id), chunks)
        logger.info(f"Indexed {len(chunks)} chunks into ChromaDB")

        # Step 3: Extract risks
        risk_system, risk_user = build_risk_prompt(text)
        risk_data = await call_mistral_json(risk_system, risk_user)
        risques_raw = risk_data.get("risques", [])

        saved_risques: list[Risque] = []
        risk_label_to_id: dict[str, uuid.UUID] = {}

        for r in risques_raw:
            try:
                prob = max(1, min(5, int(r.get("probabilite", 3))))
                impact = max(1, min(5, int(r.get("impact", 3))))
                score = float(prob * impact)
                risque = Risque(
                    id=uuid.uuid4(),
                    analyse_id=analyse_id,
                    libelle=str(r.get("libelle", "Risque inconnu"))[:500],
                    description=str(r.get("description", "")),
                    categorie=str(r.get("categorie", "OPERATIONNEL")).upper(),
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

        await db.flush()
        logger.info(f"Saved {len(saved_risques)} risks")

        # Step 4: Compliance checks — run all 3 frameworks
        compliance_scores: dict[str, float] = {}
        for framework in FRAMEWORKS:
            try:
                comp_system, comp_user = build_compliance_prompt(text, framework)
                comp_data = await call_mistral_json(comp_system, comp_user)
                global_rate = float(comp_data.get("taux_global", 0))
                compliance_scores[framework] = global_rate

                for domaine in comp_data.get("domaines", []):
                    conformite = ResultatConformite(
                        id=uuid.uuid4(),
                        analyse_id=analyse_id,
                        referentiel=framework,
                        domaine=str(domaine.get("nom", ""))[:500],
                        statut=str(domaine.get("statut", "PARTIEL")).upper(),
                        ecart=str(domaine.get("ecart", "")),
                        taux_conformite=float(domaine.get("taux", 0)),
                    )
                    db.add(conformite)
            except Exception as e:
                logger.error(f"Compliance check failed for {framework}: {e}")
                compliance_scores[framework] = 0.0

        await db.flush()

        # Step 5: Recommendations
        risks_summary = "\n".join(
            [f"- {r.libelle} (Sévérité: {r.severite}, Score: {r.score_risque})" for r in saved_risques[:20]]
        )
        rec_system, rec_user = build_recommendation_prompt(risks_summary)
        rec_data = await call_mistral_json(rec_system, rec_user)

        for rec in rec_data.get("recommandations", []):
            try:
                risque_libelle = rec.get("risque_lie", "")
                risque_id = risk_label_to_id.get(risque_libelle)
                # Try fuzzy match
                if not risque_id:
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

        await db.flush()

        # Step 6: Executive summary
        summary_system, summary_user = build_summary_prompt(
            text=text,
            risks_count=len(saved_risques),
            iso_score=compliance_scores.get("ISO27001", 0),
            rgpd_score=compliance_scores.get("RGPD", 0),
            loi_score=compliance_scores.get("LOI0908", 0),
        )
        summary = await call_mistral(summary_system, summary_user, temperature=0.3)

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
        logger.error(f"Analysis {analyse_id} failed: {exc}")
        analyse.statut = "erreur"
        rapport.statut = "erreur"
        await db.flush()
        raise


async def get_analyse(db: AsyncSession, analyse_id: uuid.UUID) -> Analyse | None:
    result = await db.execute(select(Analyse).where(Analyse.id == analyse_id))
    return result.scalar_one_or_none()


async def list_analyses_for_rapport(db: AsyncSession, rapport_id: uuid.UUID) -> list[Analyse]:
    result = await db.execute(
        select(Analyse).where(Analyse.rapport_id == rapport_id).order_by(Analyse.created_at.desc())
    )
    return list(result.scalars().all())
