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
    cfg.set("ssh_host", "example.com")
    cfg.set("ssh_port", 22)
    cfg.set("ssh_user", "deploy_user")
    cfg.set("ssh_remote_path", "/var/www/blog")
    cfg.set("ssh_password", "secret123")  # should never be exposed
    cfg.save()

    app.dependency_overrides[get_config_manager] = lambda: ConfigManager(str(config_file))
    c = TestClient(app)
    yield c
    app.dependency_overrides.clear()


def test_get_config(client):
    response = client.get("/api/config")
    assert response.status_code == 200
    data = response.json()
    assert data["jekyll_command"] == "bundle exec jekyll build"
    assert data["ssh_remote_path"] == "/var/www/blog"
    assert data["ssh_user"] == "deploy_user"
    assert data["ssh_host"] == "example.com"
    assert data["ssh_port"] == 22
    assert "ssh_password" not in data


def test_save_config(client, tmp_path):
    payload = {
        "jekyll_root": str(tmp_path / "new_root"),
        "jekyll_command": "jekyll build",
        "ssh_host": "newhost.com",
        "ssh_user": "newuser",
        "ssh_remote_path": "/var/www/html",
        "ssh_port": 2222,
        "ssh_password": "should_never_be_saved",
    }
    response = client.post("/api/config", json=payload)
    assert response.status_code == 200
    res_data = response.json()
    assert "ssh_password" not in res_data
    assert res_data["ssh_user"] == "newuser"
    assert res_data["ssh_port"] == 2222
    assert res_data["ssh_remote_path"] == "/var/www/html"

    # Verify persisted config file does not contain ssh_password
    config_file = tmp_path / "config.json"
    saved_cfg = ConfigManager(str(config_file))
    assert saved_cfg.get("ssh_user") == "newuser"
    assert saved_cfg.get("ssh_port") == 2222
    assert saved_cfg.get("ssh_password") == ""


def test_clear_cache(client, tmp_path):
    with patch("jekyll_writer.web.PublisherEngine") as mock_engine_cls:
        mock_instance = MagicMock()
        mock_instance.clear_sync_cache.return_value = True
        mock_engine_cls.return_value = mock_instance

        response = client.post("/api/config/clear-cache")
        assert response.status_code == 200
        res = response.json()
        assert res["success"] is True
        assert res["message"] == "Cache limpo com sucesso!"
        mock_instance.clear_sync_cache.assert_called_once_with(str(tmp_path))
