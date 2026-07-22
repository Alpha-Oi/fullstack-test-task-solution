from dataclasses import dataclass
from pathlib import Path

from src.domain.statuses import ScanStatus
from src.models import StoredFile


SUSPICIOUS_EXTENSIONS = {".exe", ".bat", ".cmd", ".sh", ".js"}
LARGE_FILE_THRESHOLD = 10 * 1024 * 1024


@dataclass(frozen=True)
class ScanResult:
    status: ScanStatus
    details: str
    requires_attention: bool


def scan_file(file_item: StoredFile) -> ScanResult:
    reasons: list[str] = []
    extension = Path(file_item.original_name).suffix.lower()

    if extension in SUSPICIOUS_EXTENSIONS:
        reasons.append(f"suspicious extension {extension}")
    if file_item.size > LARGE_FILE_THRESHOLD:
        reasons.append("file is larger than 10 MB")
    if extension == ".pdf" and file_item.mime_type not in {
        "application/pdf",
        "application/octet-stream",
    }:
        reasons.append("pdf extension does not match mime type")

    return ScanResult(
        status=ScanStatus.SUSPICIOUS if reasons else ScanStatus.CLEAN,
        details=", ".join(reasons) if reasons else "no threats found",
        requires_attention=bool(reasons),
    )


def extract_metadata(file_item: StoredFile, stored_path: Path) -> dict[str, object]:
    metadata: dict[str, object] = {
        "extension": Path(file_item.original_name).suffix.lower(),
        "size_bytes": file_item.size,
        "mime_type": file_item.mime_type,
    }

    if file_item.mime_type.startswith("text/"):
        line_count = 0
        char_count = 0
        with stored_path.open("r", encoding="utf-8", errors="ignore") as source:
            for line in source:
                line_count += 1
                char_count += len(line)
        metadata["line_count"] = line_count
        metadata["char_count"] = char_count
    elif file_item.mime_type == "application/pdf":
        metadata["approx_page_count"] = max(_count_pdf_pages(stored_path), 1)

    return metadata


def _count_pdf_pages(path: Path) -> int:
    marker = b"/Type /Page"
    overlap = b""
    count = 0
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            data = overlap + chunk
            count += data.count(marker)
            overlap = data[-(len(marker) - 1) :]
    return count
