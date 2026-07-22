import asyncio

from celery import chain, group

from src.core.config import get_settings
from src.core.database import async_session_maker
from src.domain.statuses import AlertLevel, ProcessingStatus, ScanStatus
from src.models import Alert, StoredFile
from src.services.processing import extract_metadata, scan_file
from src.workers.celery import celery_app


_worker_loop: asyncio.AbstractEventLoop | None = None


def run_in_worker_loop(coroutine):
    global _worker_loop
    if _worker_loop is None or _worker_loop.is_closed():
        _worker_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_worker_loop)
    return _worker_loop.run_until_complete(coroutine)


def build_file_processing_workflow(file_id: str):
    """Build a workflow with scan and metadata extraction running in parallel."""

    return chain(
        mark_file_processing.si(file_id),
        group(
            scan_file_for_threats.si(file_id),
            extract_file_metadata.si(file_id),
        ),
        finalize_file_processing.si(file_id),
    )


def dispatch_file_processing(file_id: str) -> None:
    build_file_processing_workflow(file_id).apply_async()


async def _mark_file_processing(file_id: str) -> None:
    async with async_session_maker() as session:
        file_item = await session.get(StoredFile, file_id)
        if file_item is None:
            return
        file_item.processing_status = ProcessingStatus.PROCESSING
        await session.commit()


async def _scan_file_for_threats(file_id: str) -> None:
    async with async_session_maker() as session:
        file_item = await session.get(StoredFile, file_id)
        if file_item is None:
            return
        result = scan_file(file_item)
        file_item.scan_status = result.status
        file_item.scan_details = result.details
        file_item.requires_attention = result.requires_attention
        await session.commit()


async def _extract_file_metadata(file_id: str) -> None:
    async with async_session_maker() as session:
        file_item = await session.get(StoredFile, file_id)
        if file_item is None:
            return

        stored_path = get_settings().storage_dir / file_item.stored_name
        if not stored_path.is_file():
            file_item.processing_status = ProcessingStatus.FAILED
            file_item.metadata_json = {
                "processing_error": "stored file not found during metadata extraction"
            }
            await session.commit()
            return

        try:
            file_item.metadata_json = await asyncio.to_thread(
                extract_metadata,
                file_item,
                stored_path,
            )
        except OSError:
            file_item.processing_status = ProcessingStatus.FAILED
            file_item.metadata_json = {
                "processing_error": "stored file could not be read during metadata extraction"
            }
        await session.commit()


async def _finalize_file_processing(file_id: str) -> None:
    async with async_session_maker() as session:
        file_item = await session.get(StoredFile, file_id)
        if file_item is None:
            return

        if file_item.processing_status == ProcessingStatus.FAILED:
            processing_error = (file_item.metadata_json or {}).get("processing_error")
            file_item.metadata_json = None
            file_item.scan_status = file_item.scan_status or ScanStatus.FAILED
            if processing_error:
                file_item.scan_details = str(processing_error)
            alert = Alert(
                file_id=file_id,
                level=AlertLevel.CRITICAL,
                message="File processing failed",
            )
        elif file_item.requires_attention:
            file_item.processing_status = ProcessingStatus.PROCESSED
            alert = Alert(
                file_id=file_id,
                level=AlertLevel.WARNING,
                message=f"File requires attention: {file_item.scan_details}",
            )
        else:
            file_item.processing_status = ProcessingStatus.PROCESSED
            alert = Alert(
                file_id=file_id,
                level=AlertLevel.INFO,
                message="File processed successfully",
            )
        session.add(alert)
        await session.commit()


@celery_app.task(name="files.mark_processing")
def mark_file_processing(file_id: str) -> None:
    run_in_worker_loop(_mark_file_processing(file_id))


@celery_app.task(name="files.scan")
def scan_file_for_threats(file_id: str) -> None:
    run_in_worker_loop(_scan_file_for_threats(file_id))


@celery_app.task(name="files.extract_metadata")
def extract_file_metadata(file_id: str) -> None:
    run_in_worker_loop(_extract_file_metadata(file_id))


@celery_app.task(name="files.finalize")
def finalize_file_processing(file_id: str) -> None:
    run_in_worker_loop(_finalize_file_processing(file_id))
