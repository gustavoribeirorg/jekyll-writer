import io
import os
import pytest
from PIL import Image
from fastapi.testclient import TestClient

from jekyll_writer.config import ConfigManager
from jekyll_writer.web import app, get_config_manager


@pytest.fixture
def client(tmp_path):
    config_file = tmp_path / "config.json"
    cfg = ConfigManager(str(config_file))
    cfg.set("jekyll_root", str(tmp_path))
    cfg.save()

    app.dependency_overrides[get_config_manager] = lambda: ConfigManager(str(config_file))
    c = TestClient(app)
    yield c
    app.dependency_overrides.clear()


def _create_dummy_image_bytes() -> bytes:
    buf = io.BytesIO()
    img = Image.new("RGB", (50, 50), color="blue")
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_upload_image_success(client, tmp_path):
    img_bytes = _create_dummy_image_bytes()
    response = client.post(
        "/api/images/upload",
        files={"file": ("foto teste de ferias.png", io.BytesIO(img_bytes), "image/png")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["filename"] == "foto-teste-de-ferias.png"
    assert "<figure>" in data["html_snippet"]
    assert "</figure>" in data["html_snippet"]
    assert "/assets/imagens/foto-teste-de-ferias.webp" in data["html_snippet"]
    assert "<figcaption>Foto teste de ferias</figcaption>" in data["html_snippet"]

    # Verify original file and webp file exist in assets/imagens
    dest_dir = tmp_path / "assets" / "imagens"
    assert (dest_dir / "foto-teste-de-ferias.png").exists()
    assert (dest_dir / "foto-teste-de-ferias.webp").exists()


def test_upload_image_missing_root(tmp_path):
    config_file = tmp_path / "empty_config.json"
    cfg = ConfigManager(str(config_file))
    cfg.set("jekyll_root", "")
    cfg.save()

    app.dependency_overrides[get_config_manager] = lambda: ConfigManager(str(config_file))
    client = TestClient(app)

    img_bytes = _create_dummy_image_bytes()
    response = client.post(
        "/api/images/upload",
        files={"file": ("test.png", io.BytesIO(img_bytes), "image/png")},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json()["detail"] == "Diretório do Jekyll não configurado"
