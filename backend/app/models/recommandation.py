"""Recommandation ORM model."""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Recommandation(Base):
    __tablename__ = "recommandations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    analyse_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("analyses.id"), nullable=False
    )
    risque_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("risques.id"), nullable=True
    )
    libelle: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    priorite: Mapped[str] = mapped_column(
        Enum("CRITIQUE", "HAUTE", "MOYENNE", "FAIBLE", name="priorite_enum"),
        nullable=False,
    )
    type_action: Mapped[str] = mapped_column(
        Enum("QUICK_WIN", "LONG_TERME", name="type_action_enum"), nullable=False
    )
    effort_estime: Mapped[str] = mapped_column(
        Enum("FAIBLE", "MOYEN", "ELEVE", name="effort_enum"), nullable=False
    )
    statut: Mapped[str] = mapped_column(
        Enum("A_FAIRE", "EN_COURS", "CLOTURE", name="statut_recommandation_enum"),
        nullable=False,
        default="A_FAIRE",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    analyse = relationship("Analyse", back_populates="recommandations")
    risque = relationship("Risque", back_populates="recommandations")
