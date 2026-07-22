from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Alert, StoredFile


class FileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list(self) -> list[StoredFile]:
        result = await self.session.execute(
            select(StoredFile).order_by(StoredFile.created_at.desc())
        )
        return list(result.scalars().all())

    async def get(self, file_id: str) -> StoredFile | None:
        return await self.session.get(StoredFile, file_id)

    def add(self, file_item: StoredFile) -> None:
        self.session.add(file_item)

    async def delete(self, file_item: StoredFile) -> None:
        await self.session.delete(file_item)


class AlertRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list(self) -> list[Alert]:
        result = await self.session.execute(select(Alert).order_by(Alert.created_at.desc()))
        return list(result.scalars().all())

    def add(self, alert: Alert) -> None:
        self.session.add(alert)
