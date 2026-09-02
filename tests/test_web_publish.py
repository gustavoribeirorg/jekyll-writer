import json
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from jekyll_writer.config import ConfigManager
from jekyll_writer.web import app, get_config_manager


@pytest.fixture
def client(tmp_path):
    config_file = tmp_path / "config.json"
    cfg = ConfigManager(str(config_file))
    cfg.set("jekyll_root", str(tmp_path))
    cfg.set("jekyll_command", "bundle exec jekyll build")
    cfg.set("ssh_remote_path", "/var/www/html/_site")
    cfg.save()

    app.dependency_overrides[get_config_manager] = lambda: ConfigManager(str(config_file))
    c = TestClient(app)
    yield c
    app.dependency_overrides.clear()


def test_ssh_test_success(client):
    with patch("jekyll_writer.web.PublisherEngine") as mock_engine_cls:
        mock_instance = MagicMock()
        mock_instance.test_ssh_connection.return_value = (True, "Conexão ok")
        mock_engine_cls.return_value = mock_instance

        payload = {
            "ssh_host": "example.com",
            "ssh_port": 22,
            "ssh_user": "deploy_user",
            "ssh_password": "secretpassword",
        }
        response = client.post("/api/ssh/test", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Conexão ok"


def test_ssh_test_failure(client):
    with patch("jekyll_writer.web.PublisherEngine") as mock_engine_cls:
        mock_instance = MagicMock()
        mock_instance.test_ssh_connection.return_value = (False, "Falha na senha")
        mock_engine_cls.return_value = mock_instance

        payload = {
            "ssh_host": "example.com",
            "ssh_port": 22,
            "ssh_user": "deploy_user",
            "ssh_password": "wrongpassword",
        }
        response = client.post("/api/ssh/test", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["message"] == "Falha na senha"


def test_publish_sse_stream(client, tmp_path):
    with patch("jekyll_writer.web.PublisherEngine") as mock_engine_cls:
        mock_instance = MagicMock()

        def fake_run_pipeline(**kwargs):
            # simulate logging via log_callback passed during instantiation
            log_cb = mock_engine_cls.call_args[1].get("log_callback")
            if log_cb:
                log_cb("Compilando blog...", "info")
                log_cb("Transferindo arquivos...", "info")
            return True

        mock_instance.run_pipeline.side_effect = fake_run_pipeline
        mock_engine_cls.return_value = mock_instance

        payload = {
            "ssh_host": "example.com",
            "ssh_port": 22,
            "ssh_user": "deploy_user",
            "ssh_password": "secretpassword",
        }
        response = client.post("/api/publish", json=payload)
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")
        assert response.headers.get("x-accel-buffering") == "no"
        assert response.headers.get("cache-control") == "no-cache"

        # Check stream content
        body = response.text
        assert "Compilando blog..." in body
        assert "Transferindo arquivos..." in body
        assert '"event": "done"' in body
        assert '"success": true' in body


def test_publish_missing_root(client, tmp_path):
    config_file = tmp_path / "empty_config.json"
    cfg = ConfigManager(str(config_file))
    cfg.set("jekyll_root", "")
    cfg.save()
    app.dependency_overrides[get_config_manager] = lambda: ConfigManager(str(config_file))

    payload = {
        "ssh_host": "example.com",
        "ssh_port": 22,
        "ssh_user": "deploy_user",
        "ssh_password": "secretpassword",
    }
    response = client.post("/api/publish", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Diretório do Jekyll não configurado"
