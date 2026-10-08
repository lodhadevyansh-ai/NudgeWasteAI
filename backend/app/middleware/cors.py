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

    configured_origins = [o.strip() for o in origins if isinstance(o, str) and o.strip()]

    is_production = settings.ENVIRONMENT.lower() == "production"

    if is_production:
        # In production, filter out wildcard "*" to prevent insecure wildcard CORS with credentials
        configured_origins = [o for o in configured_origins if o != "*"]
        allow_origin_regex = None
    else:
        # In development, support localhost origins with dynamic ports
        allow_origin_regex = r"https?://(localhost|127\.0\.0\.1)(:\d+)?"

    app.add_middleware(
        CORSMiddleware,
        allow_origins=configured_origins if configured_origins else (["*"] if not is_production else []),
        allow_origin_regex=allow_origin_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

