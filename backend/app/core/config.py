"""
Application Configuration Settings.
Loads configuration from environment variables or .env file using pydantic-settings.
"""

import json
from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """System settings configuration class."""

    # Application Settings
    APP_NAME: str = Field(default="NudgeWasteAI Backend", description="Application Name")
    APP_VERSION: str = Field(default="1.0.0", description="Application Version")
    ENVIRONMENT: str = Field(default="development", description="Execution environment (development, staging, production)")
    DEBUG: bool = Field(default=True, description="Debug mode flag")
    API_PREFIX: str = Field(default="/api/v1", description="API Route Prefix")
    HOST: str = Field(default="0.0.0.0", description="Server host address")
    PORT: int = Field(default=8000, description="Server port number")

    # CORS Settings
    CORS_ORIGINS: Union[List[str], str] = Field(
        default=["*"],
        description="Allowed CORS origins"
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if not v.startswith("["):
                return [i.strip() for i in v.split(",") if i.strip()]
            return json.loads(v)
        elif isinstance(v, list):
            return v
        raise ValueError(v)

    # Database Settings (Placeholders for future database integration)
    MONGODB_URI: str = Field(
        default="mongodb://localhost:27017",
        description="MongoDB connection string placeholder"
    )
    MONGODB_DB_NAME: str = Field(
        default="nudgewaste_db",
        description="MongoDB database name placeholder"
    )

    # Machine Learning Settings
    ML_MODEL_ENABLED: bool = Field(
        default=True,
        description="Flag to enable Machine Learning inference integration",
    )
    ML_CHECKPOINT_PATH: str = Field(
        default="Machine_Learning/models/trained/nudgewaste_mobilenetv3_small_best.pt",
        description="Project-relative path to ML model checkpoint",
    )
    ML_MODEL_VERSION: str = Field(
        default="v1.0.0-mobilenetv3-small",
        description="ML classification model version tag",
    )

    # Security & JWT Settings (Placeholders for future authentication integration)
    JWT_SECRET_KEY: str = Field(
        default="CHANGE_THIS_SECRET_KEY_IN_PRODUCTION_ENV",
        description="JWT Secret Key placeholder"
    )
    JWT_ALGORITHM: str = Field(
        default="HS256",
        description="JWT Hashing Algorithm"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=60,
        description="JWT Access Token expiration time in minutes"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
