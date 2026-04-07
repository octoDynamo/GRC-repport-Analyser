"""Analyse ORM model."""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Analyse(Base):
    __tablename__ = "analyses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    rapport_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rapports.id"), nullable=False
    )
    lance_par: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("utilisateurs.id"), nullable=False
    )
    resume_executif: Mapped[str | None] = mapped_column(Text, nullable=True)
    score_maturite: Mapped[float | None] = mapped_column(Float, nullable=True)
    statut: Mapped[str] = mapped_column(
        Enum("en_cours", "termine", "erreur", name="statut_analyse_enum"),
        nullable=False,
        default="en_cours",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    rapport = relationship("Rapport", back_populates="analyses")
    lance_par_user = relationship("Utilisateur", back_populates="analyses")
    risques = relationship("Risque", back_populates="analyse", lazy="select", cascade="all, delete-orphan")
    conformites = relationship("ResultatConformite", back_populates="analyse", lazy="select", cascade="all, delete-orphan")
    recommandations = relationship("Recommandation", back_populates="analyse", lazy="select", cascade="all, delete-orphan")
