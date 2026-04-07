"""Auth service — login and registration logic."""
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password, create_access_token
from app.models.utilisateur import Utilisateur


async def register_user(
    db: AsyncSession, nom: str, email: str, password: str, role: str = "ANALYSTE"
) -> Utilisateur:
    # Check if email already exists
    result = await db.execute(select(Utilisateur).where(Utilisateur.email == email))
    if result.scalar_one_or_none():
        raise ValueError("Email already registered")

    user = Utilisateur(
        id=uuid.uuid4(),
        nom=nom,
        email=email,
        mot_de_passe=hash_password(password),
        role=role.upper(),
    )
    db.add(user)
    await db.flush()
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> Utilisateur:
    result = await db.execute(select(Utilisateur).where(Utilisateur.email == email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.mot_de_passe):
        raise ValueError("Invalid email or password")
    return user


def generate_token(user: Utilisateur) -> str:
    return create_access_token(
        data={
            "user_id": str(user.id),
            "email": user.email,
            "role": user.role,
        }
    )
