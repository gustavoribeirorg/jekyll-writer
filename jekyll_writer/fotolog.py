import os
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional, List, Dict, Any

from PIL import Image, ImageOps

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".gif", ".avif", ".svg"}
CONVERTIBLE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".heic"}

def normalize_filename(filename: str) -> str:
    name, ext = os.path.splitext(filename)
    name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('utf-8')
    name = re.sub(r'[^a-zA-Z0-9_.-]', '_', name)
    name = re.sub(r'_+', '_', name).strip('_')
    if not name:
        name = "foto"
    return f"{name}{ext.lower()}"

def format_title_from_filename(filename: str) -> str:
    name_no_ext = os.path.splitext(filename)[0]
    cleaned = re.sub(r'[_-]+', ' ', name_no_ext).strip()
    return cleaned.capitalize() if cleaned else "Foto"

def add_to_gitignore(gitignore_path: Path, rel_path: str, log_fn: Callable):
    try:
        content = gitignore_path.read_text(encoding="utf-8") if gitignore_path.exists() else ""
        if rel_path not in content:
            with open(gitignore_path, "a", encoding="utf-8") as f:
                if content and not content.endswith("\n"):
                    f.write("\n")
                f.write(f"{rel_path}\n")
            log_fn(f"Adicionado ao .gitignore: {rel_path}", "info")
    except Exception as e:
        log_fn(f"Erro ao atualizar .gitignore: {e}", "warning")

def convert_image_to_webp(file_path: Path, project_dir: Path, gitignore_path: Path, log_fn: Callable) -> Path:
    if file_path.suffix.lower() not in CONVERTIBLE_EXTENSIONS:
        return file_path

    normalized_name = normalize_filename(file_path.name)
    base_stem = os.path.splitext(normalized_name)[0]
    webp_path = file_path.parent / f"{base_stem}.webp"

    rel_path = os.path.relpath(file_path, project_dir).replace("\\", "/")
    add_to_gitignore(gitignore_path, rel_path, log_fn)

    if webp_path.exists() and webp_path != file_path:
        return webp_path

    try:
        with Image.open(file_path) as img:
            img = ImageOps.exif_transpose(img)
            if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                img = img.convert("RGBA")
            else:
                img = img.convert("RGB")

            img.save(webp_path, "WEBP", quality=80)

            if os.path.exists(webp_path) and os.path.getsize(webp_path) > 1048576:
                img.save(webp_path, "WEBP", quality=50)

            if os.path.exists(webp_path) and os.path.getsize(webp_path) > 1048576:
                max_width = 1800
                if img.width > max_width:
                    ratio = max_width / float(img.width)
                    new_height = int(float(img.height) * ratio)
                    resized_img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
                    resized_img.save(webp_path, "WEBP", quality=50)

            log_fn(f"Convertido para WebP: {file_path.name} -> {webp_path.name}", "info")
        return webp_path
    except Exception as e:
        log_fn(f"Não foi possível converter {file_path.name} para WebP: {e}", "warning")
        return file_path

def scan_fotolog_images(fotolog_dir: Path, project_dir: Path, gitignore_path: Path, log_fn: Callable) -> List[Dict[str, Any]]:
    if not fotolog_dir.exists():
        fotolog_dir.mkdir(parents=True, exist_ok=True)

    found_files = [item for item in fotolog_dir.iterdir() if item.is_file() and item.suffix.lower() in SUPPORTED_EXTENSIONS]
    if not found_files:
        return []

    processed_images = []
    seen_stems = set()

    for file_path in found_files:
        if file_path.suffix.lower() in CONVERTIBLE_EXTENSIONS:
            rel_path = os.path.relpath(file_path, project_dir).replace("\\", "/")
            add_to_gitignore(gitignore_path, rel_path, log_fn)

        webp_candidate = file_path.parent / f"{normalize_filename(file_path.name).rsplit('.', 1)[0]}.webp"
        if file_path.suffix.lower() in CONVERTIBLE_EXTENSIONS:
            if not webp_candidate.exists() or webp_candidate == file_path:
                final_path = convert_image_to_webp(file_path, project_dir, gitignore_path, log_fn)
            else:
                final_path = webp_candidate
        else:
            final_path = file_path

        if final_path.exists():
            rel_src = f"/assets/fotolog/{final_path.name}"
            mtime = final_path.stat().st_mtime
            if rel_src not in seen_stems:
                seen_stems.add(rel_src)
                processed_images.append({
                    "src": rel_src,
                    "filename": final_path.name,
                    "stem": final_path.stem,
                    "alt": format_title_from_filename(final_path.name),
                    "mtime": mtime
                })

    processed_images.sort(key=lambda x: x["mtime"], reverse=True)
    return processed_images

def update_fotolog_md(fotolog_md_path: Path, images: List[Dict[str, Any]], log_fn: Callable):
    lines = [
        "---",
        "layout: fotolog",
        "title: Fotolog",
        "permalink: /fotolog/",
        "images:"
    ]
    for img in images:
        lines.append(f'  - src: "{img["src"]}"')
        lines.append(f'    alt: "{img["alt"]}"')
    lines.append("---")
    lines.append("")

    with open(fotolog_md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    log_fn(f"fotolog.md atualizado com {len(images)} foto(s)!", "success")

def sync_posts_for_rss(posts_dir: Path, images: List[Dict[str, Any]], log_fn: Callable):
    if not posts_dir.exists():
        posts_dir.mkdir(parents=True, exist_ok=True)

    existing_posts = list(posts_dir.glob("*.md"))
    existing_contents = {}
    for p in existing_posts:
        try:
            with open(p, "r", encoding="utf-8") as f:
                existing_contents[p.name] = f.read()
        except Exception:
            pass

    created_count = 0
    for img in images:
        if img["src"].startswith("http"):
            continue

        src = img["src"]
        alt = img.get("alt", "Foto")
        stem = img.get("stem", "foto")
        mtime = img.get("mtime", None)

        dt = datetime.fromtimestamp(mtime) if mtime else datetime.now()
        date_str = dt.strftime("%Y-%m-%d %H:%M -0300")
        date_prefix = dt.strftime("%Y-%m-%d")
        post_filename = f"{date_prefix}-fotolog-{stem}.md"
        post_path = posts_dir / post_filename

        already_exists = any(src in content for content in existing_contents.values())
        if not already_exists and not post_path.exists():
            post_title = f"Foto: {alt}" if not alt.lower().startswith("foto") else alt
            post_content = f"""---
title: "{post_title}"
date: {date_str}
layout: post
categories: [Fotolog]
tags: [fotolog]
---

<figure>
  <img src="{src}" alt="{alt}">
  <figcaption>Publicado no <a href="/fotolog/">Fotolog</a></figcaption>
</figure>
"""
            with open(post_path, "w", encoding="utf-8") as f:
                f.write(post_content)
            created_count += 1
            log_fn(f"Criado micro-post para feed RSS: _posts/{post_filename}", "info")

    if created_count > 0:
        log_fn(f"{created_count} micro-posts criados em _posts/ para o RSS!", "success")
    else:
        log_fn("Posts do RSS já sincronizados.", "info")

def update_fotolog(jekyll_root: str, log_callback: Optional[Callable[[str, str], None]] = None) -> bool:
    """
    Executa a atualização completa do Fotolog:
    Varre assets/fotolog/, converte para WebP, atualiza fotolog.md e sincroniza micro-posts para RSS.
    """
    def log(msg: str, lvl: str = "info"):
        if log_callback:
            log_callback(msg, lvl)
        else:
            print(f"[{lvl.upper()}] {msg}")

    project_dir = Path(jekyll_root)
    if not project_dir.is_dir():
        log(f"Pasta raiz do Jekyll não encontrada: {jekyll_root}", "error")
        return False

    fotolog_dir = project_dir / "assets" / "fotolog"
    posts_dir = project_dir / "_posts" if (project_dir / "_posts").exists() else project_dir / "posts"
    fotolog_md_path = project_dir / "fotolog.md"
    gitignore_path = project_dir / ".gitignore"

    log("Varrendo fotos do Fotolog...", "info")
    images = scan_fotolog_images(fotolog_dir, project_dir, gitignore_path, log)

    if not images:
        log("Nenhuma imagem encontrada em assets/fotolog/.", "warning")
    else:
        update_fotolog_md(fotolog_md_path, images, log)
        sync_posts_for_rss(posts_dir, images, log)

    return True
