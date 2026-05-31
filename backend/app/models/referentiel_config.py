"""ReferentielConfig — per-framework activation and threshold settings."""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ReferentielConfig(Base):
    __tablename__ = "referentiels_config"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    referentiel: Mapped[str] = mapped_column(
        Enum("ISO27001", "RGPD", "LOI0908", name="referentiel_enum"),
        nullable=False,
        unique=True,
    )
    actif: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    seuil_conformite: Mapped[float] = mapped_column(
        Float, nullable=False, default=80.0
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
