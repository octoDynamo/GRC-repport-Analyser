"""Risque (Risk) ORM model."""
import uuid

from sqlalchemy import Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Risque(Base):
    __tablename__ = "risques"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    analyse_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("analyses.id"), nullable=False
    )
    libelle: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    categorie: Mapped[str] = mapped_column(
        Enum("CYBER", "OPERATIONNEL", "LEGAL", "FINANCIER", "RH", name="categorie_risque_enum"),
        nullable=False,
    )
    probabilite: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5
    impact: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5
    score_risque: Mapped[float] = mapped_column(Float, nullable=False)  # probabilite * impact
    severite: Mapped[str] = mapped_column(
        Enum("CRITIQUE", "ELEVE", "MOYEN", "FAIBLE", name="severite_enum"),
        nullable=False,
    )
    section_source: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relationships
    analyse = relationship("Analyse", back_populates="risques")
    recommandations = relationship("Recommandation", back_populates="risque", lazy="select")
