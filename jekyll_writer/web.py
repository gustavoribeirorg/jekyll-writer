import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from jekyll_writer.config import ConfigManager
from jekyll_writer.frontmatter import (
    generate_new_post_template,
    parse_front_matter,
    save_post,
)
from jekyll_writer.publisher import PublisherEngine

app = FastAPI(title="Jekyll Writer Web", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PostPayload(BaseModel):
    content: str
    current_filename: Optional[str] = None


def get_config_manager() -> ConfigManager:
    return ConfigManager()


def _sanitize_config(data: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in data.items() if k != "ssh_password"}


@app.get("/api/config")
def get_config(cfg: ConfigManager = Depends(get_config_manager)) -> Dict[str, Any]:
    return _sanitize_config(cfg.data)


@app.post("/api/config")
def save_config(
    payload: Dict[str, Any],
    cfg: ConfigManager = Depends(get_config_manager),
) -> Dict[str, Any]:
    allowed_keys = [
        "jekyll_root",
        "jekyll_command",
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
    return _sanitize_config(cfg.data)


@app.post("/api/config/clear-cache")
def clear_cache(
    cfg: ConfigManager = Depends(get_config_manager),
) -> Dict[str, Any]:
    root = cfg.get("jekyll_root", "")
    engine = PublisherEngine()
    engine.clear_sync_cache(root)
    return {"success": True, "message": "Cache limpo com sucesso!"}


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
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            fm = parse_front_matter(content)
        except Exception:
            fm = {}

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
    jekyll_root = cfg.get("jekyll_root", "")
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

