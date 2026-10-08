"""
Unit tests for Database Configuration and Collection Name Constants.
"""

import pytest
from pydantic import ValidationError
from database.config.database_config import DatabaseSettings, get_db_settings
from database.config.collections_config import CollectionNames, COLLECTIONS


def test_default_database_settings():
    """Tests default database configuration values."""
    settings = DatabaseSettings(_env_file=None)
    assert settings.MONGODB_URI == "mongodb://localhost:27017"
    assert settings.MONGODB_DB_NAME == "nudgewaste_db"
    assert settings.MONGODB_TIMEOUT_MS == 1500
    assert settings.MONGODB_MAX_POOL_SIZE == 50


def test_valid_mongodb_uri_validation():
    """Tests valid MongoDB URI validation rules."""
    settings1 = DatabaseSettings(MONGODB_URI="mongodb://localhost:27017")
    assert settings1.MONGODB_URI == "mongodb://localhost:27017"

    settings2 = DatabaseSettings(MONGODB_URI="mongodb+srv://user:pass@cluster.mongodb.net/dbname")
    assert settings2.MONGODB_URI == "mongodb+srv://user:pass@cluster.mongodb.net/dbname"


def test_invalid_mongodb_uri_validation():
    """Tests validation error triggers for invalid MongoDB URIs."""
    with pytest.raises(ValidationError):
        DatabaseSettings(MONGODB_URI="http://invalid-scheme:27017")

    with pytest.raises(ValidationError):
        DatabaseSettings(MONGODB_URI="")


def test_invalid_database_name_validation():
    """Tests validation error triggers for empty database names."""
    with pytest.raises(ValidationError):
        DatabaseSettings(MONGODB_DB_NAME="  ")


def test_collection_names_enum_and_mapping():
    """Tests collection names enum and mapping dictionary completeness."""
    assert CollectionNames.USERS.value == "users"
    assert CollectionNames.DISPOSALS.value == "disposals"
    assert CollectionNames.NUDGES.value == "nudges"
    assert CollectionNames.CREDIT_TRANSACTIONS.value == "credit_transactions"
    assert CollectionNames.REWARDS.value == "rewards"
    assert CollectionNames.REWARD_REDEMPTIONS.value == "reward_redemptions"

    assert COLLECTIONS["users"] == "users"
    assert COLLECTIONS["disposals"] == "disposals"
    assert COLLECTIONS["nudges"] == "nudges"
    assert COLLECTIONS["credits"] == "credit_transactions"
    assert COLLECTIONS["rewards"] == "rewards"
