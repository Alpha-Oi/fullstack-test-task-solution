from typing import Annotated

from fastapi import APIRouter, File, Form, Response, UploadFile, status
from fastapi.responses import FileResponse

from src.api.dependencies import FileServiceDep
from src.schemas import FileItem, FileUpdate
from src.workers.tasks import dispatch_file_processing


router = APIRouter(prefix="/files", tags=["files"])


@router.get("", response_model=list[FileItem])
async def list_files(service: FileServiceDep):
    return await service.list_files()


@router.post("", response_model=FileItem, status_code=status.HTTP_201_CREATED)
async def create_file(
    service: FileServiceDep,
    title: Annotated[str, Form(min_length=1, max_length=255)],
    file: Annotated[UploadFile, File()],
):
    file_item = await service.create_file(title=title, upload_file=file)
    dispatch_file_processing(file_item.id)
    return file_item


@router.get("/{file_id}", response_model=FileItem)
async def get_file(file_id: str, service: FileServiceDep):
    return await service.get_file(file_id)


@router.patch("/{file_id}", response_model=FileItem)
async def update_file(file_id: str, payload: FileUpdate, service: FileServiceDep):
    return await service.update_file(file_id=file_id, title=payload.title)


@router.get("/{file_id}/download")
async def download_file(file_id: str, service: FileServiceDep):
    file_item, stored_path = await service.get_download(file_id)
    return FileResponse(
        path=stored_path,
        media_type=file_item.mime_type,
        filename=file_item.original_name,
    )


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(file_id: str, service: FileServiceDep) -> Response:
    await service.delete_file(file_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
