import logging
import mimetypes
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.errors import FileNotFoundError, InvalidTitleError, StoredFileNotFoundError
from src.domain.statuses import ProcessingStatus
from src.infrastructure.repositories import AlertRepository, FileRepository
from src.infrastructure.storage import LocalFileStorage
from src.models import Alert, StoredFile


logger = logging.getLogger(__name__)


class FileService:
    def __init__(self, session: AsyncSession, storage: LocalFileStorage) -> None:
        self.session = session
        self.storage = storage
        self.files = FileRepository(session)

    async def list_files(self) -> list[StoredFile]:
        return await self.files.list()

    async def get_file(self, file_id: str) -> StoredFile:
        file_item = await self.files.get(file_id)
        if file_item is None:
            raise FileNotFoundError("File not found")
        return file_item

    async def create_file(self, title: str, upload_file: UploadFile) -> StoredFile:
        normalized_title = _normalize_title(title)
        file_id = str(uuid4())
        suffix = Path(upload_file.filename or "").suffix
        stored_name = f"{file_id}{suffix}"
        size = await self.storage.save(upload_file, stored_name)

        file_item = StoredFile(
            id=file_id,
            title=normalized_title,
            original_name=upload_file.filename or stored_name,
            stored_name=stored_name,
            mime_type=(
                upload_file.content_type
                or mimetypes.guess_type(stored_name)[0]
                or "application/octet-stream"
            ),
            size=size,
            processing_status=ProcessingStatus.UPLOADED,
        )
        try:
            self.files.add(file_item)
            await self.session.commit()
            await self.session.refresh(file_item)
        except Exception:
            await self.session.rollback()
            await self.storage.delete(stored_name)
            raise
        return file_item

    async def update_file(self, file_id: str, title: str) -> StoredFile:
        file_item = await self.get_file(file_id)
        file_item.title = _normalize_title(title)
        await self.session.commit()
        await self.session.refresh(file_item)
        return file_item

    async def delete_file(self, file_id: str) -> None:
        file_item = await self.get_file(file_id)
        stored_name = file_item.stored_name
        await self.files.delete(file_item)
        await self.session.commit()
        try:
            await self.storage.delete(stored_name)
        except OSError:
            logger.exception("Could not remove orphaned stored file %s", stored_name)

    async def get_download(self, file_id: str) -> tuple[StoredFile, Path]:
        file_item = await self.get_file(file_id)
        if not await self.storage.exists(file_item.stored_name):
            raise StoredFileNotFoundError("Stored file not found")
        return file_item, self.storage.path_for(file_item.stored_name)


class AlertService:
    def __init__(self, session: AsyncSession) -> None:
        self.alerts = AlertRepository(session)

    async def list_alerts(self) -> list[Alert]:
        return await self.alerts.list()


def _normalize_title(title: str) -> str:
    normalized = title.strip()
    if not normalized or len(normalized) > 255:
        raise InvalidTitleError("Title must contain from 1 to 255 characters")
    return normalized
