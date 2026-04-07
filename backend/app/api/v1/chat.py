"""Chat API endpoint — RAG-powered Q&A on report content."""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.database import get_db
from app.models.analyse import Analyse
from app.models.utilisateur import Utilisateur
from app.services.chat_service import chat_with_report

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    question: str


def api_response(data=None, message: str = "Success", success: bool = True):
    return {"data": data, "message": message, "success": success}


@router.post("/{analyse_id}")
async def chat(
    analyse_id: uuid.UUID,
    body: ChatRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Utilisateur, Depends(get_current_user)],
):
    # Verify analyse exists
    result = await db.execute(select(Analyse).where(Analyse.id == analyse_id))
    analyse = result.scalar_one_or_none()
    if not analyse:
        raise HTTPException(status_code=404, detail="Analyse not found")
    if analyse.statut != "termine":
        raise HTTPException(status_code=400, detail="Analysis not yet complete")

    answer = await chat_with_report(str(analyse_id), body.question)
    return api_response(data=answer)
