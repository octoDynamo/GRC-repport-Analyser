"""Report service — file storage and database management."""
import uuid
from pathlib import Path

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.models.rapport import Rapport
from app.models.utilisateur import Utilisateur

ALLOWED_FORMATS = {"pdf", "docx", "xlsx"}


def _upload_root() -> Path:
    root = Path(settings.upload_dir)
    if not root.is_absolute():
        root = Path(__file__).parent.parent.parent / root
    root.mkdir(parents=True, exist_ok=True)
    return root


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
    """Validate, save to disk, and create DB record."""
    fmt = validate_file_format(filename)
    object_name = f"reports/{uuid.uuid4()}/{filename}"

    dest = _upload_root() / object_name
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(file_bytes)

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
    """Read report bytes from disk."""
    path = _upload_root() / object_name
    if not path.exists():
        raise FileNotFoundError(f"Report file not found: {object_name}")
    return path.read_bytes()


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
    """Delete a report, its DB records, local file, and ChromaDB collections."""
    from app.ai.rag.vector_store import delete_collection
    from app.models.analyse import Analyse

    rapport = await get_rapport(db, rapport_id)
    if not rapport:
        return False

    # 1. Delete ChromaDB collections for all analyses linked to this report
    result = await db.execute(select(Analyse).where(Analyse.rapport_id == rapport_id))
    for analyse in result.scalars().all():
        try:
            await delete_collection(str(analyse.id))
        except Exception as e:
            logger.warning(f"ChromaDB collection deletion skipped (ChromaDB unavailable): {e}")

    # 2. Delete file from disk
    try:
        path = _upload_root() / rapport.chemin
        path.unlink(missing_ok=True)
        # Remove empty parent directory
        parent = path.parent
        if parent.exists() and not any(parent.iterdir()):
            parent.rmdir()
    except Exception as e:
        logger.warning(f"Could not delete file {rapport.chemin}: {e}")

    # 3. Delete from DB (cascade handles the rest)
    await db.delete(rapport)
    await db.commit()
    return True
