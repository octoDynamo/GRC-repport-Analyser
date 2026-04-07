"""Analyses API endpoints — launch, retrieve, sub-resources."""
import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.database import get_db, AsyncSessionLocal
from app.models.analyse import Analyse
from app.models.rapport import Rapport
from app.models.utilisateur import Utilisateur
from app.services.analysis_service import get_analyse, run_analysis

router = APIRouter(prefix="/analyses", tags=["analyses"])


def api_response(data=None, message: str = "Success", success: bool = True):
    return {"data": data, "message": message, "success": success}


async def _run_analysis_background(analyse_id: uuid.UUID, rapport_id: uuid.UUID) -> None:
    """Runs analysis in a separate DB session for background tasks."""
    async with AsyncSessionLocal() as db:
        async with db.begin():
            rapport_res = await db.execute(select(Rapport).where(Rapport.id == rapport_id))
            rapport = rapport_res.scalar_one()
            analyse_res = await db.execute(select(Analyse).where(Analyse.id == analyse_id))
            analyse = analyse_res.scalar_one()
            # Simulate a user object by loading lance_par user
            from app.models.utilisateur import Utilisateur as U
            user_res = await db.execute(select(U).where(U.id == analyse.lance_par))
            user = user_res.scalar_one()
            await run_analysis(db, rapport, user, analyse_id)


@router.post("/lancer/{rapport_id}", status_code=202)
async def lancer_analyse(
    rapport_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Utilisateur, Depends(get_current_user)],
):
    # Check rapport exists
    result = await db.execute(select(Rapport).where(Rapport.id == rapport_id))
    rapport = result.scalar_one_or_none()
    if not rapport:
        raise HTTPException(status_code=404, detail="Rapport not found")

    # Create analyse record
    analyse = Analyse(
        id=uuid.uuid4(),
        rapport_id=rapport_id,
        lance_par=current_user.id,
        statut="en_cours",
    )
    db.add(analyse)
    rapport.statut = "en_cours"
    await db.flush()

    analyse_id = analyse.id
    background_tasks.add_task(_run_analysis_background, analyse_id, rapport_id)

    return api_response(
        data={"analyse_id": str(analyse_id), "statut": "en_cours"},
        message="Analysis started",
    )


@router.get("/{analyse_id}")
async def get_one(
    analyse_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Utilisateur, Depends(get_current_user)],
):
    analyse = await get_analyse(db, analyse_id)
    if not analyse:
        raise HTTPException(status_code=404, detail="Analyse not found")
    return api_response(data={
        "id": str(analyse.id),
        "rapport_id": str(analyse.rapport_id),
        "resume_executif": analyse.resume_executif,
        "score_maturite": analyse.score_maturite,
        "statut": analyse.statut,
        "created_at": analyse.created_at.isoformat(),
    })


@router.get("/{analyse_id}/risks")
async def get_risks(
    analyse_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Utilisateur, Depends(get_current_user)],
):
    from app.models.risque import Risque
    result = await db.execute(select(Risque).where(Risque.analyse_id == analyse_id))
    risques = result.scalars().all()
    data = [
        {"id": str(r.id), "libelle": r.libelle, "description": r.description,
         "categorie": r.categorie, "probabilite": r.probabilite, "impact": r.impact,
         "score_risque": r.score_risque, "severite": r.severite, "section_source": r.section_source}
        for r in risques
    ]
    return api_response(data=data)


@router.get("/{analyse_id}/conformite")
async def get_conformite(
    analyse_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Utilisateur, Depends(get_current_user)],
):
    from app.models.conformite import ResultatConformite
    result = await db.execute(select(ResultatConformite).where(ResultatConformite.analyse_id == analyse_id))
    items = result.scalars().all()
    data = [
        {"id": str(c.id), "referentiel": c.referentiel, "domaine": c.domaine,
         "statut": c.statut, "ecart": c.ecart, "taux_conformite": c.taux_conformite}
        for c in items
    ]
    return api_response(data=data)


@router.get("/{analyse_id}/recommandations")
async def get_recommandations(
    analyse_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Utilisateur, Depends(get_current_user)],
):
    from app.models.recommandation import Recommandation
    result = await db.execute(select(Recommandation).where(Recommandation.analyse_id == analyse_id))
    items = result.scalars().all()
    data = [
        {"id": str(r.id), "libelle": r.libelle, "description": r.description,
         "priorite": r.priorite, "type_action": r.type_action, "effort_estime": r.effort_estime,
         "statut": r.statut, "risque_id": str(r.risque_id) if r.risque_id else None}
        for r in items
    ]
    return api_response(data=data)
