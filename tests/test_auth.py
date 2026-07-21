import os
import pytest
from unittest.mock import patch
from auth.device_code import acquire_token, resolve_client_id, SCOPES, CLIENT_ID_ENV


def test_scopes_are_exactly_the_five_documented_read_scopes():
    assert set(SCOPES) == {
        "Directory.Read.All", "Reports.Read.All", "Organization.Read.All",
        "AuditLog.Read.All", "Policy.Read.All",
    }


def test_no_write_or_mail_scopes_present():
    joined = " ".join(SCOPES).lower()
    for forbidden in ("readwrite", "write", "mail", "exchange", ".all.all"):
        assert forbidden not in joined
    # Every scope is a read scope.
    assert all(s.endswith(".Read.All") for s in SCOPES)


def test_user_read_not_in_scopes():
    assert "User.Read" not in SCOPES


def test_missing_client_id_raises():
    with patch.dict(os.environ, {}, clear=True):
        os.environ.pop(CLIENT_ID_ENV, None)
        with pytest.raises(RuntimeError, match=CLIENT_ID_ENV):
            acquire_token()


def test_client_id_argument_overrides_env():
    with patch.dict(os.environ, {CLIENT_ID_ENV: "env-id"}, clear=True):
        assert resolve_client_id("arg-id") == "arg-id"


def test_client_id_falls_back_to_env():
    with patch.dict(os.environ, {CLIENT_ID_ENV: "env-id"}, clear=True):
        assert resolve_client_id(None) == "env-id"


def test_resolve_client_id_missing_raises_helpful_error():
    with patch.dict(os.environ, {}, clear=True):
        os.environ.pop(CLIENT_ID_ENV, None)
        with pytest.raises(RuntimeError, match="--client-id"):
            resolve_client_id(None)
