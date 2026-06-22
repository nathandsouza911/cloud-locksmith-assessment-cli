import pytest
from unittest.mock import MagicMock, patch
from graph.client import GraphClient
from graph.provider import GraphDataProvider


def _make_client():
    return GraphClient({"access_token": "fake-token"})


def test_graph_client_satisfies_provider_protocol():
    client = _make_client()
    assert isinstance(client, GraphDataProvider)


def test_get_paginated_follows_next_link():
    client = _make_client()
    page1 = {"value": [{"id": "1"}], "@odata.nextLink": "https://graph.microsoft.com/v1.0/users?$skiptoken=abc"}
    page2 = {"value": [{"id": "2"}]}

    responses = [MagicMock(json=MagicMock(return_value=page1), status_code=200),
                 MagicMock(json=MagicMock(return_value=page2), status_code=200)]
    responses[0].raise_for_status = MagicMock()
    responses[1].raise_for_status = MagicMock()

    with patch.object(client._session, "get", side_effect=responses):
        result = client._get_paginated("https://graph.microsoft.com/v1.0/users")

    assert len(result) == 2
    assert result[0]["id"] == "1"
    assert result[1]["id"] == "2"


def test_request_retries_on_429():
    client = _make_client()
    rate_limited = MagicMock(status_code=429, headers={"Retry-After": "0"})
    success = MagicMock(status_code=200, json=MagicMock(return_value={"value": []}))
    success.raise_for_status = MagicMock()

    with patch.object(client._session, "get", side_effect=[rate_limited, success]):
        with patch("time.sleep"):
            resp = client._request_with_retry("https://example.com")
    assert resp.status_code == 200
