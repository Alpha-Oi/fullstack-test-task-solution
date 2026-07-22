from io import BytesIO
from pathlib import Path

import pytest
from starlette.datastructures import UploadFile

from src.domain.errors import EmptyFileError
from src.infrastructure.storage import LocalFileStorage


async def test_upload_is_written_in_chunks(tmp_path: Path) -> None:
    storage = LocalFileStorage(tmp_path, chunk_size=3)
    upload = UploadFile(BytesIO(b"abcdefgh"), filename="source.txt")
    size = await storage.save(upload, "stored.txt")
    assert size == 8
    assert (tmp_path / "stored.txt").read_bytes() == b"abcdefgh"


async def test_empty_upload_leaves_no_file(tmp_path: Path) -> None:
    storage = LocalFileStorage(tmp_path)
    upload = UploadFile(BytesIO(b""), filename="empty.txt")
    with pytest.raises(EmptyFileError):
        await storage.save(upload, "stored.txt")
    assert not (tmp_path / "stored.txt").exists()


def test_storage_rejects_path_traversal(tmp_path: Path) -> None:
    storage = LocalFileStorage(tmp_path)
    with pytest.raises(ValueError):
        storage.path_for("../outside.txt")
