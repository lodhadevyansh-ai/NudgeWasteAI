"""
Database Health Check Utility.
Provides lightweight ping connectivity diagnostics for MongoDB without exposing sensitive URI credentials.
"""

import re
import time
from typing import Dict, Any, Optional

from database.connection.mongodb import db_manager
from database.config.database_config import db_settings


def sanitize_mongodb_uri(uri: str) -> str:
    """
    Sanitizes MongoDB connection URI string by obfuscating credentials.

    Args:
        uri: Raw MongoDB URI.

    Returns:
        str: Sanitized URI safe for logs and health check outputs.
    """
    if not uri:
        return ""
    # Pattern to match username:password@ in URIs
    pattern = r"://([^:]+):([^@]+)@"
    return re.sub(pattern, r"://\1:****@", uri)


def check_database_health(
    timeout_ms: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Executes a lightweight ping check to ascertain MongoDB connectivity and latency.

    Args:
        timeout_ms: Optional server ping timeout in milliseconds.

    Returns:
        Dict[str, Any] diagnostic object containing status, latency_ms, database_name, and error message.
    """
    db_name = db_settings.MONGODB_DB_NAME
    sanitized_uri = sanitize_mongodb_uri(db_settings.MONGODB_URI)
    start_time = time.perf_counter()

    try:
        # Ensure client is initialized
        client = db_manager.get_client()
        # Execute lightweight ping command against admin database
        client.admin.command("ping")
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return {
            "status": "healthy",
            "is_connected": True,
            "database_name": db_name,
            "sanitized_uri": sanitized_uri,
            "latency_ms": elapsed_ms,
            "error": None,
        }
    except Exception as exc:
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return {
            "status": "unhealthy",
            "is_connected": False,
            "database_name": db_name,
            "sanitized_uri": sanitized_uri,
            "latency_ms": elapsed_ms,
            "error": f"MongoDB connectivity ping failed: {str(exc)}",
        }
