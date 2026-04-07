"""Recommandations PATCH endpoint — update action status."""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.database import get_db
from app.models.recommandation import Recommandation
from app.models.utilisateur import Utilisateur
from app.schemas.analyse import RecommandationStatutUpdate

router = APIRouter(prefix="/recommandations", tags=["recommandations"])

VALID_STATUTS = {"A_FAIRE", "EN_COURS", "CLOTURE"}


def api_response(data=None, message: str = "Success", success: bool = True):
    return {"data": data, "message": message, "success": success}


@router.patch("/{recommandation_id}/statut")
async def update_statut(
    recommandation_id: uuid.UUID,
    body: RecommandationStatutUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Utilisateur, Depends(get_current_user)],
):
    if body.statut not in VALID_STATUTS:
        raise HTTPException(status_code=400, detail=f"Invalid statut. Must be one of {VALID_STATUTS}")

    result = await db.execute(select(Recommandation).where(Recommandation.id == recommandation_id))
    rec = result.scalar_one_or_none()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommandation not found")

    rec.statut = body.statut
    await db.flush()

    return api_response(
        data={"id": str(rec.id), "statut": rec.statut},
        message="Status updated successfully",
    )
