"""add_referentiels_config

Revision ID: c431bbe5c5b0
Revises: dca8bfccda56
Create Date: 2026-05-30 15:20:27.452172

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'c431bbe5c5b0'
down_revision: Union[str, None] = 'dca8bfccda56'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Use raw SQL so we reference the existing referentiel_enum without re-creating it
    op.execute("""
        CREATE TABLE referentiels_config (
            id                UUID        NOT NULL DEFAULT gen_random_uuid(),
            referentiel       referentiel_enum NOT NULL,
            actif             BOOLEAN     NOT NULL DEFAULT TRUE,
            seuil_conformite  FLOAT       NOT NULL DEFAULT 80.0,
            description       TEXT,
            updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY (id),
            UNIQUE (referentiel)
        )
    """)
    # Seed the three frameworks as active by default
    op.execute("""
        INSERT INTO referentiels_config (referentiel, actif, seuil_conformite, description) VALUES
        ('ISO27001', TRUE, 80.0, 'Norme internationale de management de la sécurité de l''information'),
        ('RGPD',     TRUE, 80.0, 'Règlement Général sur la Protection des Données (UE 2016/679)'),
        ('LOI0908',  TRUE, 80.0, 'Loi marocaine 09-08 relative à la protection des personnes physiques')
    """)


def downgrade() -> None:
    op.drop_table('referentiels_config')
