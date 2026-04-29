"""Report service — file upload to MinIO and database management."""
import io
import uuid
import asyncio
from pathlib import Path

from loguru import logger
from minio import Minio
from minio.error import S3Error
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.models.rapport import Rapport
from app.models.utilisateur import Utilisateur

ALLOWED_FORMATS = {"pdf", "docx", "xlsx"}

_minio_client: Minio | None = None


async def get_minio_client() -> Minio:
    global _minio_client
    if _minio_client is None:
        _minio_client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
        # Ensure bucket exists
        try:
            exists = await asyncio.to_thread(_minio_client.bucket_exists, settings.minio_bucket)
            if not exists:
                await asyncio.to_thread(_minio_client.make_bucket, settings.minio_bucket)
        except Exception as e:
            logger.warning(f"MinIO bucket check failed: {e}")
    return _minio_client


def validate_file_format(filename: str) -> str:
    ext = Path(filename).suffix.lower().strip(".")
    if ext not in ALLOWED_FORMATS:
        raise ValueError(f"Unsupported format '{ext}'. Allowed: {ALLOWED_FORMATS}")
    return ext


async def upload_report(
    db: AsyncSession,
    file_bytes: bytes,
    filename: str,
    user: Utilisateur,
) -> Rapport:
    """Validate, upload to MinIO, and create DB record."""
    fmt = validate_file_format(filename)
    object_name = f"reports/{uuid.uuid4()}/{filename}"

    # Upload to MinIO
    client = await get_minio_client()
    content_types = {"pdf": "application/pdf", "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}
    
    await asyncio.to_thread(
        client.put_object,
        settings.minio_bucket,
        object_name,
        io.BytesIO(file_bytes),
        length=len(file_bytes),
        content_type=content_types.get(fmt, "application/octet-stream"),
    )

    rapport = Rapport(
        id=uuid.uuid4(),
        nom=filename,
        format=fmt,
        chemin=object_name,
        statut="en_attente",
        uploade_par=user.id,
    )
    db.add(rapport)
    await db.flush()
    return rapport


async def get_report_bytes(object_name: str) -> bytes:
    """Download report bytes from MinIO."""
    client = await get_minio_client()
    response = await asyncio.to_thread(client.get_object, settings.minio_bucket, object_name)
    data = response.read()
    response.close()
    return data


async def list_rapports(db: AsyncSession, user: Utilisateur) -> list[Rapport]:
    query = select(Rapport).order_by(Rapport.created_at.desc())
    if user.role != "ADMIN":
        query = query.where(Rapport.uploade_par == user.id)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_rapport(db: AsyncSession, rapport_id: uuid.UUID) -> Rapport | None:
    result = await db.execute(select(Rapport).where(Rapport.id == rapport_id))
    return result.scalar_one_or_none()

async def delete_rapport_complet(db: AsyncSession, rapport_id: uuid.UUID) -> bool:
    """Delete a report, its DB records, MinIO file, and ChromaDB collections."""
    from app.ai.rag.vector_store import delete_collection
    from app.models.analyse import Analyse
    
    rapport = await get_rapport(db, rapport_id)
    if not rapport:
        return False
        
    # 1. Delete ChromaDB collections for all analyses linked to this report
    result = await db.execute(select(Analyse).where(Analyse.rapport_id == rapport_id))
    for analyse in result.scalars().all():
        await delete_collection(str(analyse.id))
        
    # 2. Delete file from MinIO
    try:
        client = await get_minio_client()
        await asyncio.to_thread(client.remove_object, settings.minio_bucket, rapport.chemin)
    except Exception as e:
        logger.warning(f"Could not delete MinIO object {rapport.chemin}: {e}")
        
    # 3. Delete from DB (cascade handles the rest)
    await db.delete(rapport)
    await db.commit()
    return True
