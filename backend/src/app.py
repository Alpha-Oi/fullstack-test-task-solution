from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.routers import alerts, files
from src.core.config import get_settings
from src.domain.errors import (
    EmptyFileError,
    FileNotFoundError,
    InvalidTitleError,
    StoredFileNotFoundError,
)


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(title="File Exchange API", version="1.0.0")
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(files.router)
    application.include_router(alerts.router)

    @application.exception_handler(FileNotFoundError)
    @application.exception_handler(StoredFileNotFoundError)
    async def not_found_handler(_request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": str(exc)},
        )

    @application.exception_handler(EmptyFileError)
    @application.exception_handler(InvalidTitleError)
    async def bad_request_handler(_request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc)},
        )

    return application


app = create_app()
