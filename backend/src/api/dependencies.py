from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import get_settings
from src.core.database import get_session
from src.infrastructure.storage import LocalFileStorage
from src.services.files import AlertService, FileService


@lru_cache
def get_storage() -> LocalFileStorage:
    return LocalFileStorage(get_settings().storage_dir)


def get_file_service(
    session: Annotated[AsyncSession, Depends(get_session)],
    storage: Annotated[LocalFileStorage, Depends(get_storage)],
) -> FileService:
    return FileService(session, storage)


def get_alert_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AlertService:
    return AlertService(session)


FileServiceDep = Annotated[FileService, Depends(get_file_service)]
AlertServiceDep = Annotated[AlertService, Depends(get_alert_service)]
