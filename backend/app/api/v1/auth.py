"""Auth API endpoints."""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.auth import LoginRequest, RegisterRequest
from app.services.auth_service import authenticate_user, register_user, generate_token

router = APIRouter(prefix="/auth", tags=["auth"])


def api_response(data=None, message: str = "Success", success: bool = True):
    return {"data": data, "message": message, "success": success}


@router.post("/login")
async def login(body: LoginRequest, db: Annotated[AsyncSession, Depends(get_db)]):
    try:
        user = await authenticate_user(db, body.email, body.password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    token = generate_token(user)
    return api_response(
        data={
            "access_token": token,
            "token_type": "bearer",
            "user": {"id": str(user.id), "nom": user.nom, "email": user.email, "role": user.role},
        },
        message="Login successful",
    )


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: Annotated[AsyncSession, Depends(get_db)]):
    try:
        user = await register_user(db, body.nom, body.email, body.password, body.role)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    return api_response(
        data={"id": str(user.id), "email": user.email, "role": user.role},
        message="User registered successfully",
    )
