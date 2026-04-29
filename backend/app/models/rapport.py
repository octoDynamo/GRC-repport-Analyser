"""Rapport (Report) ORM model."""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Rapport(Base):
    __tablename__ = "rapports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    nom: Mapped[str] = mapped_column(String(500), nullable=False)
    format: Mapped[str] = mapped_column(
        Enum("pdf", "docx", "xlsx", name="format_enum"), nullable=False
    )
    chemin: Mapped[str] = mapped_column(String(1000), nullable=False)
    statut: Mapped[str] = mapped_column(
        Enum("en_attente", "en_cours", "termine", "erreur", name="statut_rapport_enum"),
        nullable=False,
        default="en_attente",
    )
    uploade_par: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("utilisateurs.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    uploade_par_user = relationship("Utilisateur", back_populates="rapports")
    analyses = relationship("Analyse", back_populates="rapport", lazy="select", cascade="all, delete-orphan")
