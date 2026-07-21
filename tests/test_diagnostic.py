"""Privacy tests for the internal diagnostic utility."""
import json
import importlib.util
import pathlib

# scripts/ is not a package; load the module directly.
_SPEC = importlib.util.spec_from_file_location(
    "diagnostic", pathlib.Path(__file__).resolve().parents[1] / "scripts" / "diagnostic.py"
)
diagnostic = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(diagnostic)


def test_scrub_removes_credential_fields_at_any_depth():
    payload = {
        "access_token": "SECRET",
        "Authorization": "Bearer SECRET",
        "sections": {
            "mfa": {"http_status": 403, "refresh_token": "SECRET"},
            "list": [{"client_secret": "SECRET", "ok": True}],
        },
        "safe": "keep-me",
    }
    scrubbed = diagnostic._scrub(payload)
    blob = json.dumps(scrubbed).lower()
    for term in ("secret", "bearer", "access_token", "refresh_token", "authorization", "client_secret"):
        assert term not in blob
    assert scrubbed["safe"] == "keep-me"
    assert scrubbed["sections"]["mfa"]["http_status"] == 403
    assert scrubbed["sections"]["list"][0]["ok"] is True


def test_privacy_notice_and_warning_present():
    assert "NEVER automatically transmitted" in diagnostic._PRIVACY_WARNING
    assert "No access tokens" in diagnostic._PRIVACY_WARNING
