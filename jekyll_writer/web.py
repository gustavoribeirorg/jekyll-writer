import json
import os
import queue
import re
import shutil
import tempfile
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from fastapi import FastAPI, Depends, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from jekyll_writer.config import ConfigManager
from jekyll_writer.frontmatter import (
    generate_new_post_template,
    parse_front_matter,
    save_post,
)
from jekyll_writer.images import process_and_copy_image
from jekyll_writer.image_optimizer import optimize_images
from jekyll_writer.publisher import PublisherEngine

app = FastAPI(title="Jekyll Writer Web", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

@app.middleware("http")
async def add_no_cache_headers(request, call_next):
    response = await call_next(request)
    path = request.url.path
    if path == "/" or path.startswith("/static/"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)


@app.get("/", response_class=FileResponse)
def serve_index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if not os.path.isfile(index_path):
        raise HTTPException(status_code=404, detail="Index file not found")
    return FileResponse(index_path, media_type="text/html")


class PostPayload(BaseModel):
    content: str
    current_filename: Optional[str] = None


class SSHCredentials(BaseModel):
    ssh_host: str
    ssh_port: int = 22
    ssh_user: str
    ssh_password: str


class CheckPathPayload(BaseModel):
    path: str


class PublishPayload(BaseModel):
    deploy_mode: Optional[str] = "local"
    ssh_host: Optional[str] = None
    ssh_port: Optional[int] = 22
    ssh_user: Optional[str] = None
    ssh_password: Optional[str] = None


def get_config_manager() -> ConfigManager:
    return ConfigManager()


def _sanitize_config(data: Dict[str, Any], cfg: Optional[ConfigManager] = None) -> Dict[str, Any]:
    sanitized = {k: v for k, v in data.items() if k != "ssh_password"}
    if cfg is not None:
        val = cfg.validate_jekyll_root()
        sanitized["resolved_jekyll_root"] = val["resolved_root"]
        sanitized["root_exists"] = val["root_exists"]
        sanitized["posts_dir_exists"] = val["posts_dir_exists"]
        sanitized["posts_count"] = val["posts_count"]
        sanitized["detected_candidates"] = val["detected_candidates"]
        sanitized["server_home"] = val["server_home"]
        sanitized["server_user"] = val["server_user"]
    return sanitized


@app.get("/api/config")
def get_config(cfg: ConfigManager = Depends(get_config_manager)) -> Dict[str, Any]:
    return _sanitize_config(cfg.data, cfg)


@app.post("/api/config/check-path")
def check_path(
    payload: CheckPathPayload,
    cfg: ConfigManager = Depends(get_config_manager),
) -> Dict[str, Any]:
    return cfg.validate_jekyll_root(test_path=payload.path)


@app.post("/api/config")
def save_config(
    payload: Dict[str, Any],
    cfg: ConfigManager = Depends(get_config_manager),
):
    allowed_keys = [
        "jekyll_root",
        "jekyll_command",
        "deploy_mode",
        "ssh_host",
        "ssh_port",
        "ssh_user",
        "ssh_remote_path",
    ]
    for key in allowed_keys:
        if key in payload:
            cfg.set(key, payload[key])

    # Never persist ssh_password
    cfg.set("ssh_password", "")
    cfg.save()
    return _sanitize_config(cfg.data, cfg)


@app.post("/api/config/clear-cache")
def clear_cache(
    cfg: ConfigManager = Depends(get_config_manager),
) -> Dict[str, Any]:
    root = cfg.get_jekyll_root()
    engine = PublisherEngine()
    engine.clear_sync_cache(root)
    return {"success": True, "message": "Cache limpo com sucesso!"}


_posts_metadata_cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}


def _get_cached_post_front_matter(filepath: str) -> Dict[str, Any]:
    try:
        mtime = os.path.getmtime(filepath)
        cached = _posts_metadata_cache.get(filepath)
        if cached and cached[0] == mtime:
            return cached[1]
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        fm = parse_front_matter(content)
        _posts_metadata_cache[filepath] = (mtime, fm)
        return fm
    except Exception:
        return {}


@app.get("/api/posts")
def list_posts(cfg: ConfigManager = Depends(get_config_manager)) -> List[Dict[str, Any]]:
    posts_dir = cfg.get_posts_dir()
    if not posts_dir or not os.path.isdir(posts_dir):
        return []

    posts: List[Dict[str, Any]] = []
    for entry in os.listdir(posts_dir):
        if not (entry.endswith(".md") or entry.endswith(".markdown")):
            continue
        filepath = os.path.join(posts_dir, entry)
        if not os.path.isfile(filepath):
            continue
        fm = _get_cached_post_front_matter(filepath)

        title = fm.get("title")
        if not title:
            title = os.path.splitext(entry)[0]
        else:
            title = str(title)

        date_val = fm.get("date")
        if date_val:
            date_str = str(date_val)
        else:
            m = re.match(r"^(\d{4}-\d{2}-\d{2})", entry)
            if m:
                date_str = m.group(1)
            else:
                try:
                    mtime = os.path.getmtime(filepath)
                    date_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
                except Exception:
                    date_str = ""

        cats = fm.get("categories")
        if isinstance(cats, list):
            cats_str = ", ".join(str(c) for c in cats)
        elif cats:
            cats_str = str(cats)
        else:
            cats_str = ""

        posts.append({
            "filename": entry,
            "title": title,
            "date": date_str,
            "categories": cats_str,
        })

    posts.sort(key=lambda p: (str(p.get("date") or ""), str(p.get("filename") or "")), reverse=True)
    return posts


@app.get("/api/posts/template/new")
def get_template() -> Dict[str, str]:
    template = generate_new_post_template()
    return {"template": template}


@app.get("/api/posts/{filename}")
def get_post(filename: str, cfg: ConfigManager = Depends(get_config_manager)) -> Dict[str, Any]:
    posts_dir = cfg.get_posts_dir()
    if not posts_dir or not os.path.isdir(posts_dir):
        raise HTTPException(status_code=404, detail="Post não encontrado")

    safe_filename = os.path.basename(filename)
    filepath = os.path.join(posts_dir, safe_filename)

    if not os.path.isfile(filepath):
        raise HTTPException(status_code=404, detail="Post não encontrado")

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao ler post: {e}")

    return {"filename": safe_filename, "content": content}


@app.post("/api/posts")
def save_post_endpoint(
    payload: PostPayload,
    cfg: ConfigManager = Depends(get_config_manager),
) -> Dict[str, Any]:
    jekyll_root = cfg.get_jekyll_root()
    posts_dir = cfg.get_posts_dir()
    if not jekyll_root or not os.path.isdir(jekyll_root) or not posts_dir:
        raise HTTPException(status_code=400, detail="Diretório do Jekyll não configurado")

    current_filepath = None
    if payload.current_filename and payload.current_filename.strip():
        current_filepath = os.path.join(posts_dir, os.path.basename(payload.current_filename.strip()))

    try:
        saved_path = save_post(
            content=payload.content,
            posts_dir=posts_dir,
            current_filepath=current_filepath,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar post: {e}")

    return {
        "success": True,
        "filename": os.path.basename(saved_path),
        "path": saved_path,
    }


@app.post("/api/images/upload")
def upload_image(
    file: UploadFile = File(...),
    cfg: ConfigManager = Depends(get_config_manager),
) -> Dict[str, Any]:
    jekyll_root = cfg.get_jekyll_root()
    if not jekyll_root or not os.path.isdir(jekyll_root):
        raise HTTPException(status_code=400, detail="Diretório do Jekyll não configurado")

    temp_dir = tempfile.mkdtemp()
    try:
        filename = file.filename or "image.png"
        temp_path = os.path.join(temp_dir, os.path.basename(filename))
        with open(temp_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        html_snippet, dest_path = process_and_copy_image(temp_path, jekyll_root)
        optimize_images(jekyll_root)

        return {
            "success": True,
            "html_snippet": html_snippet,
            "filename": os.path.basename(dest_path),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar imagem: {e}")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@app.post("/api/ssh/test")
def test_ssh(data: SSHCredentials) -> Dict[str, Any]:
    engine = PublisherEngine()
    ssh_config = {
        "ssh_host": data.ssh_host.strip(),
        "ssh_port": data.ssh_port,
        "ssh_user": data.ssh_user.strip(),
        "ssh_password": data.ssh_password,
    }
    success, message = engine.test_ssh_connection(ssh_config)
    return {"success": success, "message": message}


@app.post("/api/publish")
def publish_post(
    data: PublishPayload = PublishPayload(),
    cfg: ConfigManager = Depends(get_config_manager),
):
    jekyll_root = cfg.get_jekyll_root()
    jekyll_cmd = cfg.get("jekyll_command", "bundle exec jekyll build")
    if not jekyll_root or not os.path.isdir(jekyll_root):
        raise HTTPException(status_code=400, detail="Diretório do Jekyll não configurado")

    ssh_config = None
    if (data.deploy_mode == "ssh") or (data.ssh_host and data.ssh_host.strip()):
        ssh_config = {
            "ssh_host": (data.ssh_host or "").strip(),
            "ssh_port": data.ssh_port or 22,
            "ssh_user": (data.ssh_user or "").strip(),
            "ssh_password": data.ssh_password or "",
            "ssh_remote_path": cfg.get("ssh_remote_path", "").strip() or "~/blog/_site",
        }

    def event_stream():
        q: queue.Queue = queue.Queue()
        done_sentinel = object()

        def log_callback(message: str, level: str = "info"):
            q.put({"level": level, "message": message})

        def worker():
            try:
                engine = PublisherEngine(log_callback=log_callback)
                success = engine.run_pipeline(
                    jekyll_root=jekyll_root,
                    has_images=True,
                    jekyll_cmd=jekyll_cmd,
                    ssh_config=ssh_config,
                )
            except Exception as e:
                log_callback(f"Erro inesperado: {e}", "error")
                success = False
            finally:
                q.put({"event": "done", "success": bool(success)})
                q.put(done_sentinel)

        t = threading.Thread(target=worker, daemon=True)
        t.start()

        while True:
            item = q.get()
            if item is done_sentinel:
                break
            yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"

    headers = {
        "X-Accel-Buffering": "no",
        "Cache-Control": "no-cache",
    }
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers=headers,
    )



