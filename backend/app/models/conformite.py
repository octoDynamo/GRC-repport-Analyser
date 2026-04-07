"""ResultatConformite (Compliance Result) ORM model."""
import uuid

from sqlalchemy import Enum, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ResultatConformite(Base):
    __tablename__ = "resultats_conformite"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    analyse_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("analyses.id"), nullable=False
    )
    referentiel: Mapped[str] = mapped_column(
        Enum("ISO27001", "RGPD", "LOI0908", name="referentiel_enum"), nullable=False
    )
    domaine: Mapped[str | None] = mapped_column(String(500), nullable=True)
    statut: Mapped[str] = mapped_column(
        Enum("CONFORME", "NON_CONFORME", "PARTIEL", name="statut_conformite_enum"),
        nullable=False,
    )
    ecart: Mapped[str | None] = mapped_column(Text, nullable=True)
    taux_conformite: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Relationships
    analyse = relationship("Analyse", back_populates="conformites")
