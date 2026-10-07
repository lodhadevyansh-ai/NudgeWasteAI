import sys
from pathlib import Path

# Ensure root directory and backend directory are in sys.path
APP_DIR = Path(__file__).resolve().parent
BACKEND_DIR = APP_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent
for p in [str(PROJECT_ROOT), str(BACKEND_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI


from app.core.config import settings  # pyrefly: ignore [missing-import]
from app.core.constants import APP_DESCRIPTION  # pyrefly: ignore [missing-import]
from app.utils.logger import logger  # pyrefly: ignore [missing-import]
from app.middleware.cors import setup_cors  # pyrefly: ignore [missing-import]
from app.middleware.error_handler import setup_exception_handlers  # pyrefly: ignore [missing-import]
from app.api.routes.health import router as health_router  # pyrefly: ignore [missing-import]
from app.api.routes.users import router as users_router  # pyrefly: ignore [missing-import]
from app.api.routes.prediction import router as prediction_router  # pyrefly: ignore [missing-import]
from app.api.routes.disposal import router as disposal_router  # pyrefly: ignore [missing-import]
from app.api.routes.nudges import router as nudges_router  # pyrefly: ignore [missing-import]
from app.api.routes.credits import router as credits_router  # pyrefly: ignore [missing-import]
from app.api.routes.rewards import router as rewards_router  # pyrefly: ignore [missing-import]
from app.api.routes.analytics import router as analytics_router  # pyrefly: ignore [missing-import]

from database.connection import init_mongo_connection, close_mongo_connection  # pyrefly: ignore [missing-import]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events context manager for startup and shutdown hooks."""
    logger.info(f"Starting {settings.APP_NAME} in '{settings.ENVIRONMENT}' environment...")
    try:
        init_mongo_connection(uri=settings.MONGODB_URI, db_name=settings.MONGODB_DB_NAME)
        logger.info(f"Initialized database connection for '{settings.MONGODB_DB_NAME}'")
    except Exception as exc:
        logger.warning(f"Database startup connection warning: {exc}")
    yield
    logger.info(f"Shutting down {settings.APP_NAME}...")
    try:
        close_mongo_connection()
        logger.info("Closed database connection pool.")
    except Exception as exc:
        logger.warning(f"Database shutdown connection warning: {exc}")


def create_application() -> FastAPI:
    """Factory function to build and configure the FastAPI application."""
    application = FastAPI(
        title=settings.APP_NAME,
        description=APP_DESCRIPTION,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        lifespan=lifespan,
    )

    # Register CORS Middleware
    setup_cors(application)

    # Register Global Exception Handlers
    setup_exception_handlers(application)

    # Register Health Router
    application.include_router(health_router)
    application.include_router(health_router, prefix=settings.API_PREFIX)

    # Register User Router (at root level and API prefix)
    application.include_router(users_router)
    application.include_router(users_router, prefix=settings.API_PREFIX)

    # Register Prediction Router (at root level and API prefix)
    application.include_router(prediction_router)
    application.include_router(prediction_router, prefix=settings.API_PREFIX)

    # Register Disposal Router (at root level and API prefix)
    application.include_router(disposal_router)
    application.include_router(disposal_router, prefix=settings.API_PREFIX)

    # Register Nudge Router (at root level and API prefix)
    application.include_router(nudges_router)
    application.include_router(nudges_router, prefix=settings.API_PREFIX)

    # Register Credits Router (at root level and API prefix)
    application.include_router(credits_router)
    application.include_router(credits_router, prefix=settings.API_PREFIX)

    # Register Rewards Router (at root level and API prefix)
    application.include_router(rewards_router)
    application.include_router(rewards_router, prefix=settings.API_PREFIX)

    # Register Analytics Router (at root level and API prefix)
    application.include_router(analytics_router)
    application.include_router(analytics_router, prefix=settings.API_PREFIX)

    return application


app = create_application()

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
