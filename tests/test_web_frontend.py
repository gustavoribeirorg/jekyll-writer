import pytest
from fastapi.testclient import TestClient
from jekyll_writer.web import app


@pytest.fixture
def client():
    return TestClient(app)


def test_root_serves_index_html(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    content = response.text
    # Header elements
    assert "Jekyll Writer" in content
    assert "saveStatus" in content
    assert "Novo Post" in content
    assert "Salvar" in content
    assert "Configurações" in content
    assert "Enviar Publicação" in content

    # Sidebar & Editor
    assert "postSearch" in content
    assert "postList" in content
    assert "postEditor" in content
    assert "imageFileInput" in content

    # Status Bar & Logs
    assert "wordCountDisplay" in content
    assert "logDrawer" in content
    assert "logOutput" in content

    # Modals
    assert "settingsModal" in content
    assert "cfgJekyllRoot" in content
    assert "btnClearCache" in content
    assert "publishModal" in content
    assert "pubSshPassword" in content
    assert "btnTestSsh" in content


def test_static_css_served(client):
    response = client.get("/static/style.css")
    assert response.status_code == 200
    assert "css" in response.headers.get("content-type", "") or "text/plain" in response.headers.get("content-type", "")
    css = response.text
    assert "--bg-primary" in css
    assert ".log-info" in css
    assert ".log-success" in css
    assert ".log-warning" in css
    assert ".log-error" in css
    assert ".modal-backdrop" in css
    assert ".post-item-filename" in css


def test_static_js_served(client):
    response = client.get("/static/app.js")
    assert response.status_code == 200
    assert "javascript" in response.headers.get("content-type", "") or "text/plain" in response.headers.get("content-type", "")
    js = response.text
    assert "/api/posts" in js
    assert "/api/config" in js
    assert "/api/publish" in js
    assert "/api/images/upload" in js
    assert "/api/ssh/test" in js
    assert "post-item-filename" in js
