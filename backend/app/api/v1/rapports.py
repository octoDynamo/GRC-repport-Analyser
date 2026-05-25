"""Rapports API endpoints — upload, list, get."""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.core.limiter import limiter
from app.database import get_db
from app.models.utilisateur import Utilisateur
from app.services.report_service import get_rapport, list_rapports, upload_report

router = APIRouter(prefix="/rapports", tags=["rapports"])

# FIX 3 — maximum file size accepted (20 MB)
_MAX_UPLOAD_SIZE = 20 * 1024 * 1024


def api_response(data=None, message: str = "Success", success: bool = True):
    return {"data": data, "message": message, "success": success}


@router.post("/upload", status_code=status.HTTP_201_CREATED)
@limiter.limit("20/hour")
async def upload(
    request: Request,
    file: Annotated[UploadFile, File(description="PDF, DOCX or XLSX file")],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Utilisateur, Depends(get_current_user)],
):
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Filename is missing")

    file_bytes = await file.read()

    # FIX 3 — reject oversized files before any processing
    if len(file_bytes) > _MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Fichier trop volumineux (max 20 Mo)",
        )

    try:
        rapport = await upload_report(db, file_bytes, file.filename, current_user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.exception(f"Upload failed for '{file.filename}': {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Upload failed: {str(e)}")

    return api_response(
        data={
            "id": str(rapport.id),
            "nom": rapport.nom,
            "format": rapport.format,
            "statut": rapport.statut,
            "created_at": rapport.created_at.isoformat(),
        },
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


@router.delete("/{rapport_id}")
async def delete_one(
    rapport_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Utilisateur, Depends(get_current_user)],
):
    # FIX 2 — verify existence and ownership before deletion
    rapport = await get_rapport(db, rapport_id)
    if not rapport:
        raise HTTPException(status_code=404, detail="Rapport not found")
    if rapport.uploade_par != current_user.id and current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès interdit — vous n'êtes pas le propriétaire de ce rapport",
        )

    from app.services.report_service import delete_rapport_complet
    await delete_rapport_complet(db, rapport_id)
    return api_response(message="Report deleted successfully")
