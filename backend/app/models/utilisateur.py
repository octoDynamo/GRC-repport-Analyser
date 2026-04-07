"""Utilisateur (User) ORM model."""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Utilisateur(Base):
    __tablename__ = "utilisateurs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    nom: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    mot_de_passe: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        Enum("ADMIN", "ANALYSTE", name="role_enum"), nullable=False, default="ANALYSTE"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    rapports = relationship("Rapport", back_populates="uploade_par_user", lazy="select")
    analyses = relationship("Analyse", back_populates="lance_par_user", lazy="select")
