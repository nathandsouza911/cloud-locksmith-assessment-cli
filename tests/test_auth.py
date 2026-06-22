import os
import pytest
from unittest.mock import patch
from auth.device_code import acquire_token, SCOPES


def test_scopes_contains_required_permissions():
    required = {"User.Read", "Directory.Read.All", "Reports.Read.All", "AuditLog.Read.All"}
    assert required.issubset(set(SCOPES))


def test_missing_client_id_raises():
    with patch.dict(os.environ, {}, clear=True):
        os.environ.pop("CLOUDLOCKSMITH_CLIENT_ID", None)
        with pytest.raises(RuntimeError, match="CLOUDLOCKSMITH_CLIENT_ID"):
            acquire_token()
