"""
MongoDB Client Connection Manager.
Provides reusable connection pool management, database accessor, and lifecycle hooks using PyMongo.
"""

from typing import Optional
import pymongo
from pymongo.database import Database
from pymongo.collection import Collection
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from database.config.database_config import db_settings


class MongoDBManager:
    """
    Singleton connection manager for PyMongo client pool.
    Manages single shared client lifecycle across backend services.
    """

    _instance: Optional["MongoDBManager"] = None
    _client: Optional[pymongo.MongoClient] = None
    _db: Optional[Database] = None

    def __new__(cls) -> "MongoDBManager":
        if cls._instance is None:
            cls._instance = super(MongoDBManager, cls).__new__(cls)
        return cls._instance

    def connect(
        self,
        uri: Optional[str] = None,
        db_name: Optional[str] = None,
        timeout_ms: Optional[int] = None,
    ) -> Database:
        """
        Initializes or retrieves the shared MongoDB client connection pool.

        Args:
            uri: Optional MongoDB connection URI override.
            db_name: Optional database name override.
            timeout_ms: Optional server selection timeout override in milliseconds.

        Returns:
            pymongo.database.Database instance.
        """
        target_uri = uri or db_settings.MONGODB_URI
        target_db_name = db_name or db_settings.MONGODB_DB_NAME
        target_timeout = timeout_ms if timeout_ms is not None else db_settings.MONGODB_TIMEOUT_MS

        if self._client is None:
            self._client = pymongo.MongoClient(
                target_uri,
                serverSelectionTimeoutMS=target_timeout,
                maxPoolSize=db_settings.MONGODB_MAX_POOL_SIZE,
            )
            self._db = self._client[target_db_name]

        return self._db

    def close(self) -> None:
        """Closes active PyMongo client connection pool and clears state."""
        if self._client is not None:
            try:
                self._client.close()
            except Exception:
                pass
            finally:
                self._client = None
                self._db = None

    def is_connected(self) -> bool:
        """
        Executes a ping command to verify active database connectivity.

        Returns:
            bool: True if connection is responsive, False otherwise.
        """
        if self._client is None or self._db is None:
            return False
        try:
            self._client.admin.command("ping")
            return True
        except (ConnectionFailure, ServerSelectionTimeoutError, Exception):
            return False

    def get_client(self) -> pymongo.MongoClient:
        """Returns active pymongo.MongoClient instance, connecting if needed."""
        if self._client is None:
            self.connect()
        return self._client

    def get_database(self) -> Database:
        """Returns active pymongo.database.Database instance, connecting if needed."""
        if self._db is None:
            self.connect()
        return self._db

    def get_collection(self, collection_name: str) -> Collection:
        """
        Retrieves a PyMongo Collection object from the active database.

        Args:
            collection_name: Name of MongoDB collection.

        Returns:
            pymongo.collection.Collection instance.
        """
        db = self.get_database()
        return db[collection_name]


# Shared singleton instance
db_manager = MongoDBManager()


def init_mongo_connection(uri: Optional[str] = None, db_name: Optional[str] = None) -> Database:
    """Lifecycle helper to initialize MongoDB connection pool."""
    return db_manager.connect(uri=uri, db_name=db_name)


def close_mongo_connection() -> None:
    """Lifecycle helper to close active MongoDB connection pool."""
    db_manager.close()


def get_mongo_client() -> pymongo.MongoClient:
    """Accessor helper to get active pymongo.MongoClient."""
    return db_manager.get_client()


def get_db() -> Database:
    """Accessor helper to get active pymongo.database.Database."""
    return db_manager.get_database()


def get_collection(name: str) -> Collection:
    """Accessor helper to get a PyMongo collection."""
    return db_manager.get_collection(name)
