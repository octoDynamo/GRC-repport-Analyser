"""Admin endpoints — users management, global stats, referentiel configuration."""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_admin
from app.core.security import hash_password
from app.database import get_db
from app.models.analyse import Analyse
from app.models.rapport import Rapport
from app.models.recommandation import Recommandation
from app.models.referentiel_config import ReferentielConfig
from app.models.risque import Risque
from app.models.utilisateur import Utilisateur

router = APIRouter(prefix="/admin", tags=["admin"])

REFERENTIELS = ("ISO27001", "RGPD", "LOI0908")


def api_response(data=None, message: str = "Success", success: bool = True):
    return {"data": data, "message": message, "success": success}


# ── Schemas ────────────────────────────────────────────────────────────────────

class CreateUserBody(BaseModel):
    nom: str
    email: EmailStr
    password: str
    role: str = "ANALYSTE"


class UpdateUserBody(BaseModel):
    nom: str | None = None
    role: str | None = None


class UpdateReferentielBody(BaseModel):
    actif: bool | None = None
    seuil_conformite: float | None = None
    description: str | None = None


# ── Stats ──────────────────────────────────────────────────────────────────────

@router.get("/stats")
async def global_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[Utilisateur, Depends(require_admin)],
):
    """Global platform statistics. Admin only."""
    total_users = await db.scalar(select(func.count()).select_from(Utilisateur))
    total_rapports = await db.scalar(select(func.count()).select_from(Rapport))
    total_analyses = await db.scalar(select(func.count()).select_from(Analyse))
    total_analyses_terminees = await db.scalar(
        select(func.count()).select_from(Analyse).where(Analyse.statut == "termine")
    )
    total_risques = await db.scalar(select(func.count()).select_from(Risque))
    total_recommandations = await db.scalar(select(func.count()).select_from(Recommandation))
    score_maturite_moyen = await db.scalar(
        select(func.avg(Analyse.score_maturite)).where(Analyse.score_maturite.isnot(None))
    )

    return api_response(data={
        "total_utilisateurs": total_users,
        "total_rapports": total_rapports,
        "total_analyses": total_analyses,
        "total_analyses_terminees": total_analyses_terminees,
        "total_risques": total_risques,
        "total_recommandations": total_recommandations,
        "score_maturite_moyen": round(float(score_maturite_moyen), 1) if score_maturite_moyen else None,
    })


# ── Users ──────────────────────────────────────────────────────────────────────

@router.get("/users")
async def list_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[Utilisateur, Depends(require_admin)],
):
    """List all users with their report count. Admin only."""
    result = await db.execute(
        select(
            Utilisateur.id,
            Utilisateur.nom,
            Utilisateur.email,
            Utilisateur.role,
            Utilisateur.created_at,
            func.count(Rapport.id).label("nb_rapports"),
        )
        .outerjoin(Rapport, Rapport.uploade_par == Utilisateur.id)
        .group_by(Utilisateur.id)
        .order_by(Utilisateur.created_at.desc())
    )
    rows = result.all()
    return api_response(data=[
        {
            "id": str(r.id),
            "nom": r.nom,
            "email": r.email,
            "role": r.role,
            "created_at": r.created_at.isoformat(),
            "nb_rapports": r.nb_rapports,
        }
        for r in rows
    ])


@router.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user(
    body: CreateUserBody,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[Utilisateur, Depends(require_admin)],
):
    """Create a new user. Admin only."""
    if body.role not in ("ADMIN", "ANALYSTE"):
        raise HTTPException(status_code=400, detail="role doit être ADMIN ou ANALYSTE")

    existing = await db.scalar(select(Utilisateur).where(Utilisateur.email == body.email))
    if existing:
        raise HTTPException(status_code=409, detail="Email déjà utilisé")

    user = Utilisateur(
        id=uuid.uuid4(),
        nom=body.nom,
        email=body.email,
        mot_de_passe=hash_password(body.password),
        role=body.role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return api_response(
        data={"id": str(user.id), "nom": user.nom, "email": user.email, "role": user.role},
        message="Utilisateur créé",
        success=True,
    )


@router.patch("/users/{user_id}")
async def update_user(
    user_id: uuid.UUID,
    body: UpdateUserBody,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[Utilisateur, Depends(require_admin)],
):
    """Update user nom or role. Admin only."""
    user = await db.scalar(select(Utilisateur).where(Utilisateur.id == user_id))
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    if body.role and body.role not in ("ADMIN", "ANALYSTE"):
        raise HTTPException(status_code=400, detail="role doit être ADMIN ou ANALYSTE")

    # Prevent admin from demoting themselves
    if str(user.id) == str(admin.id) and body.role and body.role != "ADMIN":
        raise HTTPException(status_code=400, detail="Vous ne pouvez pas changer votre propre rôle")

    if body.nom is not None:
        user.nom = body.nom
    if body.role is not None:
        user.role = body.role

    await db.commit()
    return api_response(
        data={"id": str(user.id), "nom": user.nom, "email": user.email, "role": user.role},
        message="Utilisateur mis à jour",
    )


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[Utilisateur, Depends(require_admin)],
):
    """Delete a user. Admin only. Cannot delete yourself."""
    if str(user_id) == str(admin.id):
        raise HTTPException(status_code=400, detail="Vous ne pouvez pas supprimer votre propre compte")

    user = await db.scalar(select(Utilisateur).where(Utilisateur.id == user_id))
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    await db.delete(user)
    await db.commit()
    return api_response(message="Utilisateur supprimé")


# ── Referentiels config ────────────────────────────────────────────────────────

@router.get("/referentiels")
async def list_referentiels(
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[Utilisateur, Depends(require_admin)],
):
    """List referentiel configuration. Admin only."""
    result = await db.execute(select(ReferentielConfig).order_by(ReferentielConfig.referentiel))
    configs = result.scalars().all()
    return api_response(data=[
        {
            "id": str(c.id),
            "referentiel": c.referentiel,
            "actif": c.actif,
            "seuil_conformite": c.seuil_conformite,
            "description": c.description,
            "updated_at": c.updated_at.isoformat(),
        }
        for c in configs
    ])


@router.patch("/referentiels/{referentiel}")
async def update_referentiel(
    referentiel: str,
    body: UpdateReferentielBody,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[Utilisateur, Depends(require_admin)],
):
    """Update a referentiel's activation or conformity threshold. Admin only."""
    if referentiel not in REFERENTIELS:
        raise HTTPException(status_code=404, detail=f"Référentiel inconnu. Valeurs: {REFERENTIELS}")

    config = await db.scalar(
        select(ReferentielConfig).where(ReferentielConfig.referentiel == referentiel)
    )
    if not config:
        raise HTTPException(status_code=404, detail="Configuration introuvable")

    if body.actif is not None:
        config.actif = body.actif
    if body.seuil_conformite is not None:
        if not (0 <= body.seuil_conformite <= 100):
            raise HTTPException(status_code=400, detail="seuil_conformite doit être entre 0 et 100")
        config.seuil_conformite = body.seuil_conformite
    if body.description is not None:
        config.description = body.description

    await db.commit()
    return api_response(
        data={
            "referentiel": config.referentiel,
            "actif": config.actif,
            "seuil_conformite": config.seuil_conformite,
            "description": config.description,
        },
        message=f"Référentiel {referentiel} mis à jour",
    )
