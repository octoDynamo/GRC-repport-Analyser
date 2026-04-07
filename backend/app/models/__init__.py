"""Models package — import all models here for Alembic autodiscovery."""
from app.models.utilisateur import Utilisateur
from app.models.rapport import Rapport
from app.models.analyse import Analyse
from app.models.risque import Risque
from app.models.conformite import ResultatConformite
from app.models.recommandation import Recommandation

__all__ = [
    "Utilisateur",
    "Rapport",
    "Analyse",
    "Risque",
    "ResultatConformite",
    "Recommandation",
]
