import pytest
from unittest.mock import MagicMock, patch
from graph.client import GraphClient
from graph.errors import GraphAPIError
from graph.provider import GraphDataProvider


def _make_client():
    return GraphClient({"access_token": "fake-token"})


def _ok_response(json_body: dict) -> MagicMock:
    r = MagicMock(status_code=200, ok=True)
    r.json.return_value = json_body
    return r


def _error_response(status: int, code: str, message: str) -> MagicMock:
    r = MagicMock(status_code=status, ok=False, reason=message)
    r.json.return_value = {"error": {"code": code, "message": message}}
    return r


def test_graph_client_satisfies_provider_protocol():
    client = _make_client()
    assert isinstance(client, GraphDataProvider)


def test_get_paginated_follows_next_link():
    client = _make_client()
    page1 = {"value": [{"id": "1"}], "@odata.nextLink": "https://graph.microsoft.com/v1.0/users?$skiptoken=abc"}
    page2 = {"value": [{"id": "2"}]}

    responses = [_ok_response(page1), _ok_response(page2)]
    with patch.object(client._session, "get", side_effect=responses):
        result = client._get_paginated("https://graph.microsoft.com/v1.0/users")

    assert len(result) == 2
    assert result[0]["id"] == "1"
    assert result[1]["id"] == "2"


def test_request_retries_on_429():
    client = _make_client()
    rate_limited = MagicMock(status_code=429, ok=False, headers={"Retry-After": "0"})
    success = _ok_response({"value": []})

    with patch.object(client._session, "get", side_effect=[rate_limited, success]):
        with patch("time.sleep"):
            resp = client._request_with_retry("https://example.com")
    assert resp.status_code == 200


def test_raises_graph_api_error_on_403():
    client = _make_client()
    resp = _error_response(403, "Authorization_RequestDenied", "Insufficient privileges.")

    with patch.object(client._session, "get", return_value=resp):
        with pytest.raises(GraphAPIError) as exc_info:
            client._request_with_retry("https://example.com")

    err = exc_info.value
    assert err.status_code == 403
    assert err.error_code == "Authorization_RequestDenied"
    assert "Insufficient privileges" in err.graph_message


def test_raises_graph_api_error_on_400():
    client = _make_client()
    resp = _error_response(400, "BadRequest", "Invalid query.")

    with patch.object(client._session, "get", return_value=resp):
        with pytest.raises(GraphAPIError) as exc_info:
            client._request_with_retry("https://example.com")

    assert exc_info.value.status_code == 400
    assert exc_info.value.error_code == "BadRequest"


def test_graph_api_error_falls_back_on_non_json_body():
    client = _make_client()
    resp = MagicMock(status_code=500, ok=False, reason="Internal Server Error")
    resp.json.side_effect = ValueError("not json")

    with patch.object(client._session, "get", return_value=resp):
        with pytest.raises(GraphAPIError) as exc_info:
            client._request_with_retry("https://example.com")

    err = exc_info.value
    assert err.status_code == 500
    assert err.error_code == "UnknownError"
