"""Export API endpoints."""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.database import get_db
from app.models.utilisateur import Utilisateur
from app.services.export_service import export_to_excel, export_to_pdf

router = APIRouter(prefix="/export", tags=["export"])


@router.get("/{analyse_id}/pdf")
async def export_pdf(
    analyse_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Utilisateur, Depends(get_current_user)],
):
    try:
        pdf_bytes = await export_to_pdf(db, analyse_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="analyse_{analyse_id}.pdf"'},
    )


@router.get("/{analyse_id}/excel")
async def export_excel(
    analyse_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Utilisateur, Depends(get_current_user)],
):
    try:
        excel_bytes = await export_to_excel(db, analyse_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="analyse_{analyse_id}.xlsx"'},
    )
