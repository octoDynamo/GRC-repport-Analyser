"""Rapport Pydantic schemas."""
import uuid
from datetime import datetime
from pydantic import BaseModel


class RapportResponse(BaseModel):
    id: uuid.UUID
    nom: str
    format: str
    statut: str
    created_at: datetime

    model_config = {"from_attributes": True}


class RapportUploadResponse(BaseModel):
    id: uuid.UUID
    nom: str
    statut: str
