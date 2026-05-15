from instagram_personal_mcp import server
from instagram_personal_mcp.client import IGClientError


def test_module_imports():
    assert hasattr(server, "mcp")
    assert hasattr(server, "run")


def test_error_decorator_serializes_ig_client_error():
    @server.tool
    def boom():
        raise IGClientError("nope", code="X")

    result = boom()
    assert result == {"error": True, "message": "nope", "code": "X"}


def test_error_decorator_catches_value_error():
    @server.tool
    def boom():
        raise ValueError("bad arg")

    result = boom()
    assert result["error"] is True
    assert result["type"] == "ValueError"
    assert result["message"] == "bad arg"


def test_login_without_credentials_errors_cleanly():
    result = server.instagram_login()
    assert result == {
        "error": True,
        "message": (
            "Username and password required (pass args or set IG_USERNAME / IG_PASSWORD)."
        ),
        "code": "MISSING_CREDENTIALS",
    }


def test_session_status_when_not_logged_in():
    result = server.instagram_session_status()
    assert result["logged_in"] is False
    assert "session_file" in result
