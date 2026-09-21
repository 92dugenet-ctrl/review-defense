from main import build_gunicorn_command


def test_ecloudserv_entrypoint_binds_platform_port():
    command = build_gunicorn_command("43127")
    assert command[0].endswith("python")
    assert command[1:3] == ["-m", "gunicorn"]
    assert "--bind" in command
    assert "0.0.0.0:43127" in command
    assert command[-1] == "wsgi:app"


def test_ecloudserv_entrypoint_has_safe_local_default_port():
    command = build_gunicorn_command(None)
    assert "0.0.0.0:8080" in command
    assert command[-1] == "wsgi:app"
