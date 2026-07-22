import asyncio
from pathlib import Path

import aiofiles
from fastapi import UploadFile

from src.domain.errors import EmptyFileError


class LocalFileStorage:
    """Local storage adapter that writes uploads without loading them into RAM."""

    def __init__(self, root: Path, chunk_size: int = 1024 * 1024) -> None:
        self.root = root
        self.chunk_size = chunk_size
        self.root.mkdir(parents=True, exist_ok=True)

    def path_for(self, stored_name: str) -> Path:
        if Path(stored_name).name != stored_name:
            raise ValueError("stored_name must not contain a path")
        return self.root / stored_name

    async def save(self, upload_file: UploadFile, stored_name: str) -> int:
        path = self.path_for(stored_name)
        size = 0
        try:
            async with aiofiles.open(path, "wb") as destination:
                while chunk := await upload_file.read(self.chunk_size):
                    size += len(chunk)
                    await destination.write(chunk)
        except Exception:
            await self.delete(stored_name)
            raise
        finally:
            await upload_file.close()

        if size == 0:
            await self.delete(stored_name)
            raise EmptyFileError("File is empty")
        return size

    async def exists(self, stored_name: str) -> bool:
        return await asyncio.to_thread(self.path_for(stored_name).is_file)

    async def delete(self, stored_name: str) -> None:
        path = self.path_for(stored_name)

        def unlink_if_exists() -> None:
            path.unlink(missing_ok=True)

        await asyncio.to_thread(unlink_if_exists)
