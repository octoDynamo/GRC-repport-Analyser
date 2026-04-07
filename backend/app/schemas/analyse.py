"""Analyse, Risque, Conformite, and Recommandation Pydantic schemas."""
import uuid
from datetime import datetime
from pydantic import BaseModel


class RisqueResponse(BaseModel):
    id: uuid.UUID
    libelle: str
    description: str | None
    categorie: str
    probabilite: int
    impact: int
    score_risque: float
    severite: str
    section_source: str | None

    model_config = {"from_attributes": True}


class ConformiteResponse(BaseModel):
    id: uuid.UUID
    referentiel: str
    domaine: str | None
    statut: str
    ecart: str | None
    taux_conformite: float

    model_config = {"from_attributes": True}


class RecommandationResponse(BaseModel):
    id: uuid.UUID
    libelle: str
    description: str | None
    priorite: str
    type_action: str
    effort_estime: str
    statut: str
    created_at: datetime
    risque_id: uuid.UUID | None

    model_config = {"from_attributes": True}


class RecommandationStatutUpdate(BaseModel):
    statut: str  # A_FAIRE | EN_COURS | CLOTURE


class AnalyseResponse(BaseModel):
    id: uuid.UUID
    rapport_id: uuid.UUID
    resume_executif: str | None
    score_maturite: float | None
    statut: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AnalyseFullResponse(AnalyseResponse):
    risques: list[RisqueResponse] = []
    conformites: list[ConformiteResponse] = []
    recommandations: list[RecommandationResponse] = []
