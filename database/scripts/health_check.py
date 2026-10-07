"""
Database CLI Script: Health Check.
Checks MongoDB database connectivity and prints sanitized health diagnostics.
"""

import json
from database.connection import check_database_health, close_mongo_connection


def main():
    """Executes database ping health check and outputs sanitized JSON report."""
    health = check_database_health()
    print(json.dumps(health, indent=2))
    close_mongo_connection()
    if not health.get("is_connected", False):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
