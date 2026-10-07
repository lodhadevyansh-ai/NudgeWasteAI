"""
Unit Tests for Database Seeding and Reset Safeguards.
"""

from unittest.mock import MagicMock, patch
import pytest

from database.seed.waste_seed import seed_waste_streams
from database.seed.rewards_seed import seed_rewards_catalog
from database.seed.users_seed import seed_demo_users
from database.seed.run_seed import run_all_seeds
from database.scripts.reset_database import reset_database


@patch("database.seed.waste_seed.waste_collection")
def test_seed_waste_streams_idempotent(mock_waste_col):
    seeded1 = seed_waste_streams()
    assert len(seeded1) == 4
    assert set(seeded1) == {"Wet", "Dry", "Sanitary", "Special Care"}

    # Re-running seed must be idempotent
    seeded2 = seed_waste_streams()
    assert len(seeded2) == 4
    assert mock_waste_col.upsert_waste_stream.call_count == 8


@patch("database.seed.rewards_seed.rewards_collection")
def test_seed_rewards_catalog_idempotent(mock_rewards_col):
    seeded1 = seed_rewards_catalog()
    assert len(seeded1) == 4

    seeded2 = seed_rewards_catalog()
    assert len(seeded2) == 4
    assert mock_rewards_col.create_reward_catalog_item.call_count == 8


@patch("database.seed.users_seed.users_collection")
def test_seed_demo_users_existing_skips(mock_users_col):
    mock_existing_user = MagicMock()
    mock_existing_user.id = "user_existing_123"
    mock_users_col.get_user_by_email.return_value = mock_existing_user

    seeded = seed_demo_users()
    assert seeded == ["user_existing_123"]
    mock_users_col.create_user.assert_not_called()


@patch("database.seed.run_seed.seed_demo_users")
@patch("database.seed.run_seed.seed_rewards_catalog")
@patch("database.seed.run_seed.seed_waste_streams")
def test_run_all_seeds(mock_waste, mock_rewards, mock_users):
    mock_waste.return_value = ["Wet", "Dry", "Sanitary", "Special Care"]
    mock_rewards.return_value = ["reward_1", "reward_2"]
    mock_users.return_value = ["demo_user_1"]

    summary = run_all_seeds(include_demo_users=True)
    assert summary["waste_streams"] == ["Wet", "Dry", "Sanitary", "Special Care"]
    assert summary["rewards"] == ["reward_1", "reward_2"]
    assert summary["users"] == ["demo_user_1"]


def test_reset_database_safeguard_without_confirm():
    """Tests that reset_database blocks execution without explicit confirmation flag."""
    with pytest.raises(PermissionError, match="explicit confirmation"):
        reset_database(confirm=False)


@patch("database.scripts.reset_database.db_settings")
def test_reset_database_safeguard_production_blocked(mock_settings):
    """Tests that reset_database blocks execution when configured database name indicates production."""
    mock_settings.MONGODB_DB_NAME = "nudgewaste_prod"

    with pytest.raises(PermissionError, match="prohibited on production"):
        reset_database(confirm=True)
