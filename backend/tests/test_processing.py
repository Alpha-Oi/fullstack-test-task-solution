from pathlib import Path

import pytest

from src.domain.statuses import ScanStatus
from src.models import StoredFile
from src.services.processing import extract_metadata, scan_file


def make_file(**overrides) -> StoredFile:
    values = {
        "id": "file-id",
        "title": "File",
        "original_name": "document.txt",
        "stored_name": "file-id.txt",
        "mime_type": "text/plain",
        "size": 10,
        "processing_status": "uploaded",
    }
    values.update(overrides)
    return StoredFile(**values)


def test_clean_file_scan() -> None:
    result = scan_file(make_file())
    assert result.status == ScanStatus.CLEAN
    assert result.details == "no threats found"
    assert result.requires_attention is False


@pytest.mark.parametrize("extension", ["exe", "bat", "cmd", "sh", "js"])
def test_suspicious_extension(extension: str) -> None:
    result = scan_file(make_file(original_name=f"script.{extension}"))
    assert result.status == ScanStatus.SUSPICIOUS
    assert f"suspicious extension .{extension}" in result.details


def test_large_file_and_mime_mismatch_reasons_are_combined() -> None:
    result = scan_file(
        make_file(
            original_name="document.pdf",
            mime_type="text/plain",
            size=11 * 1024 * 1024,
        )
    )
    assert result.status == ScanStatus.SUSPICIOUS
    assert "larger than 10 MB" in result.details
    assert "does not match mime type" in result.details


def test_text_metadata_is_streamed(tmp_path: Path) -> None:
    path = tmp_path / "document.txt"
    path.write_text("first\nsecond", encoding="utf-8")
    metadata = extract_metadata(make_file(size=12), path)
    assert metadata["line_count"] == 2
    assert metadata["char_count"] == 12


def test_pdf_page_marker_across_chunk_boundary(tmp_path: Path) -> None:
    path = tmp_path / "document.pdf"
    prefix = b"x" * (1024 * 1024 - 5)
    path.write_bytes(prefix + b"/Type /Page" + b"/Type /Page")
    item = make_file(
        original_name="document.pdf",
        stored_name="file-id.pdf",
        mime_type="application/pdf",
        size=path.stat().st_size,
    )
    metadata = extract_metadata(item, path)
    assert metadata["approx_page_count"] == 2
