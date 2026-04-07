"""Rapports API endpoints — upload, list, get."""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.database import get_db
from app.models.utilisateur import Utilisateur
from app.services.report_service import get_rapport, list_rapports, upload_report

router = APIRouter(prefix="/rapports", tags=["rapports"])


def api_response(data=None, message: str = "Success", success: bool = True):
    return {"data": data, "message": message, "success": success}


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload(
    file: Annotated[UploadFile, File(description="PDF, DOCX or XLSX file")],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Utilisateur, Depends(get_current_user)],
):
    file_bytes = await file.read()
    try:
        rapport = await upload_report(db, file_bytes, file.filename, current_user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return api_response(
        data={"id": str(rapport.id), "nom": rapport.nom, "statut": rapport.statut},
        message="Report uploaded successfully",
    )


@router.get("")
async def list_all(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Utilisateur, Depends(get_current_user)],
):
    rapports = await list_rapports(db, current_user)
    data = [
        {"id": str(r.id), "nom": r.nom, "format": r.format, "statut": r.statut, "created_at": r.created_at.isoformat()}
        for r in rapports
    ]
    return api_response(data=data)


@router.get("/{rapport_id}")
async def get_one(
    rapport_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Utilisateur, Depends(get_current_user)],
):
    rapport = await get_rapport(db, rapport_id)
    if not rapport:
        raise HTTPException(status_code=404, detail="Rapport not found")
    return api_response(
        data={"id": str(rapport.id), "nom": rapport.nom, "format": rapport.format, "statut": rapport.statut, "created_at": rapport.created_at.isoformat()}
    )
