"""
Database Configuration Settings.
Loads MongoDB connection configuration from environment variables or .env file using pydantic-settings.
"""

from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database settings configuration model."""

    MONGODB_URI: str = Field(
        default="mongodb://localhost:27017",
        description="MongoDB connection string URI",
    )
    MONGODB_DB_NAME: str = Field(
        default="nudgewaste_db",
        description="MongoDB target database name",
    )
    MONGODB_TIMEOUT_MS: int = Field(
        default=1500,
        description="MongoDB server selection timeout in milliseconds",
    )
    MONGODB_MAX_POOL_SIZE: int = Field(
        default=50,
        description="Maximum connection pool size",
    )

    @field_validator("MONGODB_URI")
    @classmethod
    def validate_mongodb_uri(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("MONGODB_URI cannot be empty")
        if not (v.startswith("mongodb://") or v.startswith("mongodb+srv://")):
            raise ValueError("MONGODB_URI must start with 'mongodb://' or 'mongodb+srv://'")
        return v

    @field_validator("MONGODB_DB_NAME")
    @classmethod
    def validate_mongodb_db_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("MONGODB_DB_NAME cannot be empty")
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


def get_db_settings() -> DatabaseSettings:
    """Factory function to get DatabaseSettings instance."""
    return DatabaseSettings()


db_settings = get_db_settings()
