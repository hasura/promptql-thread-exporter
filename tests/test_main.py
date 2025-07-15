import pytest
from unittest.mock import patch, MagicMock
from typing import Dict, Any

import requests

from main import fetch_thread


@pytest.fixture
def mock_response() -> MagicMock:
    response = MagicMock()
    response.json.return_value = {"key": "value"}
    response.status_code = 200
    return response


def test_fetch_thread_success(mock_response: MagicMock) -> None:
    """Test successful API fetch."""
    with patch("requests.get", return_value=mock_response) as mock_get:
        result = fetch_thread("test_id", "test_token",
                              "https://promptql.ddn.hasura.app")
        assert result == {"key": "value"}
        mock_get.assert_called_once_with(
            "https://promptql.ddn.hasura.app/playground/threads/test_id",
            headers={"Authorization": "api-key test_token",
                     "Content-Type": "application/json"}
        )


def test_fetch_thread_invalid_input() -> None:
    """Test input validation."""
    with pytest.raises(ValueError):
        fetch_thread("", "token", "https://promptql.ddn.hasura.app")

    with pytest.raises(ValueError):
        fetch_thread("id", " ", "https://promptql.ddn.hasura.app")


def test_fetch_thread_http_error() -> None:
    """Test HTTP error handling."""
    mock_error_response = MagicMock()
    mock_error_response.status_code = 404
    mock_error_response.raise_for_status.side_effect = requests.HTTPError(
        "Not found")

    with patch("requests.get", return_value=mock_error_response):
        with pytest.raises(requests.HTTPError):
            fetch_thread("test_id", "test_token",
                         "https://promptql.ddn.hasura.app")
