"""
Unit Tests for Database Index Creation and Repeatability.
"""

from unittest.mock import MagicMock, patch
from database.indexes.users_indexes import create_users_indexes
from database.indexes.waste_indexes import create_waste_indexes
from database.indexes.predictions_indexes import create_predictions_indexes
from database.indexes.disposals_indexes import create_disposals_indexes
from database.indexes.nudges_indexes import create_nudges_indexes
from database.indexes.credits_indexes import create_credits_indexes
from database.indexes.rewards_indexes import create_rewards_indexes
from database.indexes import create_all_indexes


@patch("database.indexes.users_indexes.get_collection")
def test_create_users_indexes(mock_get_col):
    mock_col = MagicMock()
    mock_get_col.return_value = mock_col
    mock_col.create_index.side_effect = ["idx_email", "idx_id"]

    created = create_users_indexes()
    assert len(created) == 2
    assert mock_col.create_index.call_count == 2


@patch("database.indexes.disposals_indexes.get_collection")
def test_create_disposals_indexes(mock_get_col):
    mock_col = MagicMock()
    mock_get_col.return_value = mock_col
    mock_col.create_index.side_effect = ["idx_id", "idx_user_ts", "idx_pred", "idx_status_cat"]

    created = create_disposals_indexes()
    assert len(created) == 4
    assert mock_col.create_index.call_count == 4


@patch("database.indexes.credits_indexes.get_collection")
def test_create_credits_indexes(mock_get_col):
    mock_col = MagicMock()
    mock_get_col.return_value = mock_col
    mock_col.create_index.side_effect = ["idx_tx_id", "idx_disp_id", "idx_user_ts"]

    created = create_credits_indexes()
    assert len(created) == 3


@patch("database.indexes.users_indexes.get_collection")
@patch("database.indexes.waste_indexes.get_collection")
@patch("database.indexes.predictions_indexes.get_collection")
@patch("database.indexes.disposals_indexes.get_collection")
@patch("database.indexes.nudges_indexes.get_collection")
@patch("database.indexes.credits_indexes.get_collection")
@patch("database.indexes.rewards_indexes.get_collection")
def test_create_all_indexes_repeatable(
    mock_rew_col, mock_cred_col, mock_nudge_col, mock_disp_col, mock_pred_col, mock_waste_col, mock_user_col
):
    mock_user_col.return_value = MagicMock()
    mock_waste_col.return_value = MagicMock()
    mock_pred_col.return_value = MagicMock()
    mock_disp_col.return_value = MagicMock()
    mock_nudge_col.return_value = MagicMock()
    mock_cred_col.return_value = MagicMock()
    mock_rew_col.return_value = MagicMock()

    # First run
    res1 = create_all_indexes()
    assert isinstance(res1, dict)

    # Second run (verifies idempotency / repeatability)
    res2 = create_all_indexes()
    assert isinstance(res2, dict)
    assert set(res1.keys()) == set(res2.keys())
