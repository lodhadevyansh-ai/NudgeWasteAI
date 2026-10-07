"""
Global Exception Handlers Middleware.
Ensures consistent JSON error responses across the application.
"""

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.utils.logger import logger  # pyrefly: ignore [missing-import]


def setup_exception_handlers(app: FastAPI) -> None:
    """
    Registers custom global exception handlers to the FastAPI app.

    Args:
        app: The FastAPI application instance.
    """

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        """Handles HTTP standard exceptions."""
        logger.warning(f"HTTP Exception {exc.status_code} at {request.url.path}: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": exc.status_code,
                    "message": exc.detail,
                },
                "path": request.url.path,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        """Handles request validation failure exceptions."""
        logger.warning(f"Validation Error at {request.url.path}: {exc.errors()}")
        return JSONResponse(
            status_code=getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422),
            content=jsonable_encoder({
                "success": False,
                "error": {
                    "code": getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422),
                    "message": "Validation error",
                    "details": exc.errors(),
                },
                "path": request.url.path,
            }),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handles uncaught server error exceptions."""
        logger.error(f"Unhandled Exception at {request.url.path}: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": {
                    "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "message": "An unexpected internal server error occurred.",
                },
                "path": request.url.path,
            },
        )
