"""
CORS Middleware Configuration.
Configures FastAPI CORS using application settings.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings  # pyrefly: ignore [missing-import]


def setup_cors(app: FastAPI) -> None:
    """
    Configures and registers Cross-Origin Resource Sharing (CORS) middleware.

    Args:
        app: The FastAPI application instance.
    """
    origins = settings.CORS_ORIGINS
    if isinstance(origins, str):
        origins = [origins]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins if origins != ["*"] else ["*"],
        allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
