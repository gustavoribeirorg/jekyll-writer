# Jekyll Writer Web (Self-Hosted) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform the Jekyll Writer desktop tool into a modern, self-hosted web application built with FastAPI and a responsive Vanilla HTML/CSS/JS frontend, featuring a posts browser, Markdown textarea editor, automatic WebP image upload, Server-Sent Events (SSE) real-time log streaming, and zero-persistence SSH credential security.

**Architecture:** A lightweight asynchronous Python web server (`jekyll_writer/web.py`) exposes REST endpoints and SSE streams to a static single-page frontend (`jekyll_writer/static/`). The web layer reuses 100% of the proven core logic (`config`, `frontmatter`, `images`, `image_optimizer`, `publisher`). The web server runs via `python web.py` or `run_web.bat`, listening on `0.0.0.0:8000` to allow both local access and remote access over Cloudflare Tunnel with `X-Accel-Buffering: no` SSE streaming.

**Tech Stack:** Python 3.10+, FastAPI, Uvicorn, Python-Multipart, Paramiko, Pillow, Vanilla HTML5/CSS3/JavaScript.

**Spec:** [`docs/superpowers/specs/2026-09-02-jekyll-writer-web-design.md`](file:///c:/Users/Gustavo%20Ribeiro.DESKTOP-MQL7L2R/Desktop/jekyll-writer/docs/superpowers/specs/2026-09-02-jekyll-writer-web-design.md)

## Global Constraints
- **Zero-Persistence SSH Credentials**: SSH password is NEVER stored on disk in `config.json`. Host, port, user, and password are provided ephemerally in the publish dialog and kept strictly in memory for the duration of the request.
- **Cloudflare Tunnel Optimization**: All Server-Sent Event (SSE) responses must send headers `X-Accel-Buffering: no` and `Cache-Control: no-cache` to ensure real-time chunk streaming through Cloudflare proxy without buffering.
- **Reusability**: No duplication of Markdown/Frontmatter parsing, image handling, or publisher pipeline logic. All web routes call existing `jekyll_writer` modules directly.
- **Dependency Hygiene**: Frontend is built with clean vanilla HTML, CSS, and JS — zero Node.js/npm dependencies.
- **Test Coverage**: Every endpoint must have automated tests using `fastapi.testclient.TestClient`. Existing 31 unit tests must remain 100% passing.

---

### Task 1: Web Dependencies & FastAPI App Scaffolding

**Files:**
- Create: `jekyll_writer/web.py`
- Create: `web.py`
- Modify: `requirements.txt`
- Test: `tests/test_web_config.py`

**Interfaces:**
- Consumes: `ConfigManager` from `jekyll_writer/config.py`, `PublisherEngine.clear_sync_cache` from `jekyll_writer/publisher.py`.
- Produces: FastAPI `app` instance with `/api/config` (GET / POST) and `/api/config/clear-cache` (POST).

- [ ] **Step 1: Install web dependencies and update requirements.txt**
Install `fastapi`, `uvicorn`, `python-multipart` and update `requirements.txt`.

- [ ] **Step 2: Write failing test in tests/test_web_config.py**
Write tests for `/api/config` GET, POST, and `/api/config/clear-cache`:
```python
from fastapi.testclient import TestClient
from jekyll_writer.web import app
from jekyll_writer.config import ConfigManager

def test_get_config(tmp_path, monkeypatch):
    cfg_file = tmp_path / "config.json"
    cfg = ConfigManager(str(cfg_file))
    cfg.set("jekyll_root", "/test/blog")
    monkeypatch.setattr("jekyll_writer.web.get_config_manager", lambda: cfg)
    
    client = TestClient(app)
    response = client.get("/api/config")
    assert response.status_code == 200
    data = response.json()
    assert data["jekyll_root"] == "/test/blog"
    assert "ssh_password" not in data
```

- [ ] **Step 3: Run test to verify it fails**
Run: `python -m pytest tests/test_web_config.py -v`
Expected: FAIL (ModuleNotFoundError: No module named 'jekyll_writer.web')

- [ ] **Step 4: Implement jekyll_writer/web.py and web.py**
Implement FastAPI app with CORS, `ConfigManager` integration, `/api/config` GET/POST (sanitizing and removing passwords), and `/api/config/clear-cache`. Create entry point `web.py`.

- [ ] **Step 5: Run test to verify it passes**
Run: `python -m pytest tests/test_web_config.py -v`
Expected: PASS

- [ ] **Step 6: Commit**
`git add requirements.txt jekyll_writer/web.py web.py tests/test_web_config.py && git commit -m "feat: scaffold FastAPI web server and config endpoints"`

---

### Task 2: Posts Management API (`/api/posts`)

**Files:**
- Modify: `jekyll_writer/web.py`
- Test: `tests/test_web_posts.py`

**Interfaces:**
- Consumes: `parse_front_matter`, `generate_new_post_template`, `save_post` from `jekyll_writer/frontmatter.py`.
- Produces:
  - `GET /api/posts` -> list of `{ filename, title, date, categories }`
  - `GET /api/posts/{filename}` -> `{ filename, content }`
  - `POST /api/posts` -> `{ filename, path, success }`
  - `GET /api/posts/template/new` -> `{ template }`

- [ ] **Step 1: Write failing test in tests/test_web_posts.py**
Test listing posts, reading a single post, saving a post, and getting a new template:
```python
from fastapi.testclient import TestClient
from jekyll_writer.web import app
from jekyll_writer.config import ConfigManager

def test_posts_crud(tmp_path, monkeypatch):
    blog_dir = tmp_path / "my-blog"
    posts_dir = blog_dir / "_posts"
    posts_dir.mkdir(parents=True)
    post_file = posts_dir / "2026-09-01-primeiro-post.md"
    post_file.write_text("---\ntitle: Primeiro Post\ndate: 2026-09-01 12:00 -0300\n---\nOla mundo!", encoding="utf-8")
    
    cfg_file = tmp_path / "config.json"
    cfg = ConfigManager(str(cfg_file))
    cfg.set("jekyll_root", str(blog_dir))
    monkeypatch.setattr("jekyll_writer.web.get_config_manager", lambda: cfg)
    
    client = TestClient(app)
    # List
    res_list = client.get("/api/posts")
    assert res_list.status_code == 200
    posts = res_list.json()
    assert len(posts) == 1
    assert posts[0]["title"] == "Primeiro Post"
    
    # Read
    res_get = client.get(f"/api/posts/{post_file.name}")
    assert res_get.status_code == 200
    assert "Ola mundo!" in res_get.json()["content"]
    
    # New template
    res_tpl = client.get("/api/posts/template/new")
    assert res_tpl.status_code == 200
    assert "layout: post" in res_tpl.json()["template"]
```

- [ ] **Step 2: Run test to verify it fails**
Run: `python -m pytest tests/test_web_posts.py -v`
Expected: FAIL (404 Not Found)

- [ ] **Step 3: Implement posts endpoints in jekyll_writer/web.py**
Add routes `GET /api/posts`, `GET /api/posts/{filename}`, `POST /api/posts`, and `GET /api/posts/template/new`.

- [ ] **Step 4: Run test to verify it passes**
Run: `python -m pytest tests/test_web_posts.py -v`
Expected: PASS

- [ ] **Step 5: Commit**
`git add jekyll_writer/web.py tests/test_web_posts.py && git commit -m "feat: implement posts CRUD endpoints in web API"`

---

### Task 3: Media Upload & Image Optimization API (`/api/images/upload`)

**Files:**
- Modify: `jekyll_writer/web.py`
- Test: `tests/test_web_images.py`

**Interfaces:**
- Consumes: `process_and_copy_image` from `jekyll_writer/images.py`, `optimize_images` from `jekyll_writer/image_optimizer.py`.
- Produces: `POST /api/images/upload` returning `{ html_snippet, filename, web_url }`.

- [ ] **Step 1: Write failing test in tests/test_web_images.py**
```python
import io
from fastapi.testclient import TestClient
from jekyll_writer.web import app
from jekyll_writer.config import ConfigManager

def test_upload_image(tmp_path, monkeypatch):
    blog_dir = tmp_path / "blog"
    blog_dir.mkdir()
    cfg = ConfigManager(str(tmp_path / "config.json"))
    cfg.set("jekyll_root", str(blog_dir))
    monkeypatch.setattr("jekyll_writer.web.get_config_manager", lambda: cfg)
    
    client = TestClient(app)
    file_bytes = b"fake image bytes"
    files = {"file": ("minha foto ferias.png", io.BytesIO(file_bytes), "image/png")}
    
    res = client.post("/api/images/upload", files=files)
    assert res.status_code == 200
    data = res.json()
    assert "<figure>" in data["html_snippet"]
    assert "/assets/imagens/minha-foto-ferias.webp" in data["html_snippet"]
    assert (blog_dir / "assets" / "imagens" / "minha-foto-ferias.png").exists()
```

- [ ] **Step 2: Run test to verify it fails**
Run: `python -m pytest tests/test_web_images.py -v`
Expected: FAIL (404 Not Found)

- [ ] **Step 3: Implement image upload route in jekyll_writer/web.py**
Implement `POST /api/images/upload` using `UploadFile`, saving to a temp file, processing with `process_and_copy_image(temp_path, jekyll_root)`, running `optimize_images(jekyll_root)`, and returning HTML snippet.

- [ ] **Step 4: Run test to verify it passes**
Run: `python -m pytest tests/test_web_images.py -v`
Expected: PASS

- [ ] **Step 5: Commit**
`git add jekyll_writer/web.py tests/test_web_images.py && git commit -m "feat: implement image upload and optimization endpoint"`

---

### Task 4: Zero-Persistence SSH Test & SSE Real-Time Publishing API

**Files:**
- Modify: `jekyll_writer/web.py`
- Test: `tests/test_web_publish.py`

**Interfaces:**
- Consumes: `PublisherEngine` from `jekyll_writer/publisher.py`.
- Produces:
  - `POST /api/ssh/test` -> tests SSH connection with ephemeral credentials in body.
  - `POST /api/publish` -> receives `{ ssh_host, ssh_port, ssh_user, ssh_password }`, triggers pipeline, and returns `StreamingResponse` with `media_type="text/event-stream"` and headers `X-Accel-Buffering: no`, `Cache-Control: no-cache`.

- [ ] **Step 1: Write failing test in tests/test_web_publish.py**
Test SSH test endpoint and SSE streaming publish endpoint with mock pipeline:
```python
from unittest.mock import patch
from fastapi.testclient import TestClient
from jekyll_writer.web import app
from jekyll_writer.config import ConfigManager

def test_ssh_test_endpoint(tmp_path, monkeypatch):
    client = TestClient(app)
    with patch("jekyll_writer.web.PublisherEngine.test_ssh_connection", return_value=(True, "Conectado!")):
        res = client.post("/api/ssh/test", json={"ssh_host": "test.com", "ssh_port": 22, "ssh_user": "u", "ssh_password": "p"})
        assert res.status_code == 200
        assert res.json()["success"] is True

def test_publish_sse_stream(tmp_path, monkeypatch):
    blog_dir = tmp_path / "blog"
    blog_dir.mkdir()
    cfg = ConfigManager(str(tmp_path / "config.json"))
    cfg.set("jekyll_root", str(blog_dir))
    monkeypatch.setattr("jekyll_writer.web.get_config_manager", lambda: cfg)
    
    client = TestClient(app)
    with patch("jekyll_writer.web.PublisherEngine.run_pipeline", return_value=True):
        res = client.post("/api/publish", json={"ssh_host": "test.com", "ssh_port": 22, "ssh_user": "u", "ssh_password": "p"})
        assert res.status_code == 200
        assert "text/event-stream" in res.headers["content-type"]
        assert res.headers["x-accel-buffering"] == "no"
        assert res.headers["cache-control"] == "no-cache"
```

- [ ] **Step 2: Run test to verify it fails**
Run: `python -m pytest tests/test_web_publish.py -v`
Expected: FAIL (404 Not Found)

- [ ] **Step 3: Implement SSH test and SSE publishing in jekyll_writer/web.py**
Implement `POST /api/ssh/test` and `POST /api/publish` streaming generator using `asyncio.Queue` or thread-safe queue communicating between `PublisherEngine.log_callback` and FastAPI `StreamingResponse`.

- [ ] **Step 4: Run test to verify it passes**
Run: `python -m pytest tests/test_web_publish.py -v`
Expected: PASS

- [ ] **Step 5: Commit**
`git add jekyll_writer/web.py tests/test_web_publish.py && git commit -m "feat: implement ssh test and sse publish streaming endpoints"`

---

### Task 5: Frontend Single-Page Interface

**Files:**
- Create: `jekyll_writer/static/index.html`
- Create: `jekyll_writer/static/style.css`
- Create: `jekyll_writer/static/app.js`
- Modify: `jekyll_writer/web.py` (mount static directory at `/static` and serve `index.html` at `/`)
- Test: `tests/test_web_frontend.py`

**Interfaces:**
- Consumes: REST and SSE endpoints from `jekyll_writer/web.py`.
- Produces: Complete, responsive browser-based UI matching the Jekyll Writer design.

- [ ] **Step 1: Write failing test in tests/test_web_frontend.py**
Verify `/` serves the HTML index and `/static/style.css` / `/static/app.js` return 200 OK:
```python
from fastapi.testclient import TestClient
from jekyll_writer.web import app

def test_frontend_routes():
    client = TestClient(app)
    res_index = client.get("/")
    assert res_index.status_code == 200
    assert "Jekyll Writer" in res_index.text
    
    res_css = client.get("/static/style.css")
    assert res_css.status_code == 200
    
    res_js = client.get("/static/app.js")
    assert res_js.status_code == 200
```

- [ ] **Step 2: Run test to verify it fails**
Run: `python -m pytest tests/test_web_frontend.py -v`
Expected: FAIL (404 Not Found)

- [ ] **Step 3: Build index.html, style.css, and app.js in jekyll_writer/static/**
  - `index.html`: Header, Sidebar with posts filter list, formatting toolbar, Markdown textarea, footer status bar, terminal drawer for logs, Settings Modal, and Publish Modal.
  - `style.css`: Clean modern dark theme with CSS custom properties, responsive grid/flex layout, mobile drawer toggle.
  - `app.js`: Functions for:
    - Loading and rendering posts in sidebar.
    - Creating a new post (fetching `/api/posts/template/new`).
    - Saving post (`Ctrl+S` or button).
    - Toolbar wrap helpers (bold, italic, list, etc.).
    - File upload handling with automatic figure insertion.
    - Opening Publish Modal, submitting credentials via fetch, and connecting to SSE stream to display logs live in the terminal drawer.
    - Settings modal save and cache clear.

- [ ] **Step 4: Mount static files and root route in jekyll_writer/web.py**
Mount `StaticFiles(directory=..., html=True)` and root `FileResponse`.

- [ ] **Step 5: Run test to verify it passes**
Run: `python -m pytest tests/test_web_frontend.py -v`
Expected: PASS

- [ ] **Step 6: Commit**
`git add jekyll_writer/static/ jekyll_writer/web.py tests/test_web_frontend.py && git commit -m "feat: implement responsive single-page web interface"`

---

### Task 6: Windows Batch Runner, Documentation & End-to-End Verification

**Files:**
- Create: `run_web.bat`
- Modify: `README.md`

- [ ] **Step 1: Create run_web.bat**
Windows 1-click launcher starting `python web.py` and opening the browser at `http://localhost:8000`.

- [ ] **Step 2: Update README.md**
Document how to run the web version locally, how to access via mobile/tablet on LAN, and how to route via Cloudflare Tunnel.

- [ ] **Step 3: Run full pytest suite across desktop and web**
Run: `python -m pytest -v`
Ensure all 31 existing tests + new web tests pass with 100% success rate.

- [ ] **Step 4: Commit**
`git add run_web.bat README.md && git commit -m "docs: add web launcher and setup documentation"`
