import os
import pytest
from fastapi.testclient import TestClient

from jekyll_writer.config import ConfigManager
from jekyll_writer.web import app, get_config_manager


@pytest.fixture
def client(tmp_path):
    config_file = tmp_path / "config.json"
    posts_dir = tmp_path / "_posts"
    posts_dir.mkdir(parents=True, exist_ok=True)

    cfg = ConfigManager(str(config_file))
    cfg.set("jekyll_root", str(tmp_path))
    cfg.save()

    app.dependency_overrides[get_config_manager] = lambda: ConfigManager(str(config_file))
    c = TestClient(app)
    yield c
    app.dependency_overrides.clear()


def test_list_posts(client, tmp_path):
    posts_dir = tmp_path / "_posts"

    # Create dummy posts with different dates
    post1 = posts_dir / "2026-01-01-post-one.md"
    post1.write_text(
        "---\ntitle: Post One\ndate: 2026-01-01 10:00 -0300\ncategories: [tech, python]\n---\nContent 1",
        encoding="utf-8",
    )

    post2 = posts_dir / "2026-02-01-post-two.markdown"
    post2.write_text(
        "---\ntitle: Post Two\ndate: 2026-02-01 12:00 -0300\ncategories: news\n---\nContent 2",
        encoding="utf-8",
    )

    # File without frontmatter
    post3 = posts_dir / "2025-12-01-raw-post.md"
    post3.write_text("No frontmatter here", encoding="utf-8")

    # Non-markdown file that should be ignored
    (posts_dir / "image.png").write_text("fake image", encoding="utf-8")

    response = client.get("/api/posts")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3

    # Verify chronological descending order (post2 first, post1 second, post3 last)
    assert data[0]["filename"] == "2026-02-01-post-two.markdown"
    assert data[0]["title"] == "Post Two"
    assert "2026-02-01" in str(data[0]["date"])
    assert "news" in str(data[0]["categories"])

    assert data[1]["filename"] == "2026-01-01-post-one.md"
    assert data[1]["title"] == "Post One"

    assert data[2]["filename"] == "2025-12-01-raw-post.md"
    assert data[2]["title"] == "2025-12-01-raw-post"


def test_list_posts_empty_or_unconfigured(client, tmp_path):
    # Empty posts dir
    response = client.get("/api/posts")
    assert response.status_code == 200
    assert response.json() == []

    # Unconfigured jekyll root
    config_file = tmp_path / "empty_config.json"
    cfg = ConfigManager(str(config_file))
    cfg.set("jekyll_root", "")
    cfg.save()
    app.dependency_overrides[get_config_manager] = lambda: ConfigManager(str(config_file))

    response = client.get("/api/posts")
    assert response.status_code == 200
    assert response.json() == []


def test_get_post(client, tmp_path):
    posts_dir = tmp_path / "_posts"
    post_file = posts_dir / "2026-09-02-hello-world.md"
    content = "---\ntitle: Hello World\ndate: 2026-09-02\n---\nHello from tests!"
    post_file.write_text(content, encoding="utf-8")

    # Success case
    response = client.get("/api/posts/2026-09-02-hello-world.md")
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "2026-09-02-hello-world.md"
    assert data["content"] == content

    # 404 for missing post
    res_404 = client.get("/api/posts/non-existent.md")
    assert res_404.status_code == 404
    assert res_404.json()["detail"] == "Post não encontrado"

    # Directory traversal attempt
    res_traversal = client.get("/api/posts/../../config.json")
    # Due to basename sanitization, it looks for config.json in _posts which doesn't exist -> 404
    assert res_traversal.status_code == 404


def test_save_post_new(client, tmp_path):
    post_content = "---\ntitle: Meu Novo Post\ndate: 2026-09-02 14:00 -0300\nlayout: post\n---\nTexto do post."
    payload = {"content": post_content}

    response = client.post("/api/posts", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["filename"] == "2026-09-02-meu-novo-post.md"
    assert os.path.exists(data["path"])

    saved_file = tmp_path / "_posts" / "2026-09-02-meu-novo-post.md"
    assert saved_file.exists()
    assert saved_file.read_text(encoding="utf-8") == post_content


def test_save_post_update(client, tmp_path):
    posts_dir = tmp_path / "_posts"
    initial_file = posts_dir / "2026-09-02-original.md"
    initial_file.write_text("Original content", encoding="utf-8")

    updated_content = "---\ntitle: Titulo Alterado\ndate: 2026-09-02\n---\nNovo conteudo"
    payload = {
        "content": updated_content,
        "current_filename": "2026-09-02-original.md",
    }

    response = client.post("/api/posts", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["filename"] == "2026-09-02-original.md"
    assert initial_file.read_text(encoding="utf-8") == updated_content


def test_save_post_unconfigured_root(client, tmp_path):
    config_file = tmp_path / "empty_config.json"
    cfg = ConfigManager(str(config_file))
    cfg.set("jekyll_root", "")
    cfg.save()
    app.dependency_overrides[get_config_manager] = lambda: ConfigManager(str(config_file))

    payload = {"content": "---\ntitle: Test\n---\nBody"}
    response = client.post("/api/posts", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Diretório do Jekyll não configurado"


def test_get_template(client):
    response = client.get("/api/posts/template/new")
    assert response.status_code == 200
    data = response.json()
    assert "template" in data
    assert "title:" in data["template"]
    assert "layout: post" in data["template"]

    # With client_date
    res_client = client.get("/api/posts/template/new?client_date=2026-09-04%2012:52%20-0300")
    assert res_client.status_code == 200
    assert "date: 2026-09-04 12:52 -0300" in res_client.json()["template"]


def test_save_post_with_custom_filename(client, tmp_path):
    post_content = "---\ntitle: Fazendo um sistema com IA\ndate: 2026-09-04 12:00:00 -0300\nlayout: post\n---\nCorpo."
    payload = {
        "content": post_content,
        "custom_filename": "sistema-com-ia"
    }

    response = client.post("/api/posts", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["filename"] == "2026-09-04-sistema-com-ia.md"
    assert os.path.exists(data["path"])

    saved_file = tmp_path / "_posts" / "2026-09-04-sistema-com-ia.md"
    assert saved_file.exists()


def test_save_post_rename_via_api(client, tmp_path):
    posts_dir = tmp_path / "_posts"
    initial_file = posts_dir / "2026-09-04-antigo.md"
    initial_file.write_text("Conteudo inicial", encoding="utf-8")

    updated_content = "---\ntitle: Titulo Renomeado\ndate: 2026-09-04\n---\nConteudo atualizado"
    payload = {
        "content": updated_content,
        "current_filename": "2026-09-04-antigo.md",
        "custom_filename": "2026-09-04-novo.md",
    }

    response = client.post("/api/posts", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["filename"] == "2026-09-04-novo.md"

    # New file exists, old file was removed
    assert (posts_dir / "2026-09-04-novo.md").exists()
    assert not (posts_dir / "2026-09-04-antigo.md").exists()
