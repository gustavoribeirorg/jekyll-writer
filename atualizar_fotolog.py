#!/usr/bin/env python3
"""
Script de automação para o Fotolog do Jekyll.
Varre a pasta assets/fotolog/ por imagens, opcionalmente converte para WebP,
atualiza a página fotolog.md e gera micro-posts em _posts/ para alimentar o feed RSS do blog.
"""

import os
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

# Tentativa de importar Pillow para otimização de imagens
try:
    from PIL import Image, ImageOps
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Caminhos do projeto
PROJECT_DIR = Path(__file__).resolve().parent.parent
ASSETS_FOTOLOG_DIR = PROJECT_DIR / "assets" / "fotolog"
POSTS_DIR = PROJECT_DIR / "_posts"
FOTOLOG_MD_PATH = PROJECT_DIR / "fotolog.md"
GITIGNORE_PATH = PROJECT_DIR / ".gitignore"

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".gif", ".avif", ".svg"}
CONVERTIBLE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".heic"}

# Placeholders padrão para simulação / fallback
DEFAULT_PLACEHOLDERS = [
    {"src": "https://placehold.co/600x400", "alt": "Placeholder 600x400"},
    {"src": "https://placehold.co/400x600", "alt": "Placeholder 400x600"},
    {"src": "https://placehold.co/500x500", "alt": "Placeholder 500x500"},
    {"src": "https://placehold.co/700x450", "alt": "Placeholder 700x450"},
    {"src": "https://placehold.co/450x700", "alt": "Placeholder 450x700"},
    {"src": "https://placehold.co/600x800", "alt": "Placeholder 600x800"},
    {"src": "https://placehold.co/800x600", "alt": "Placeholder 800x600"},
    {"src": "https://placehold.co/500x750", "alt": "Placeholder 500x750"},
    {"src": "https://placehold.co/600x600", "alt": "Placeholder 600x600"},
    {"src": "https://placehold.co/700x900", "alt": "Placeholder 700x900"},
    {"src": "https://placehold.co/400x400", "alt": "Placeholder 400x400"},
    {"src": "https://placehold.co/600x350", "alt": "Placeholder 600x350"},
    {"src": "https://placehold.co/350x500", "alt": "Placeholder 350x500"},
    {"src": "https://placehold.co/500x600", "alt": "Placeholder 500x600"},
    {"src": "https://placehold.co/800x500", "alt": "Placeholder 800x500"},
    {"src": "https://placehold.co/600x450", "alt": "Placeholder 600x450"},
    {"src": "https://placehold.co/450x600", "alt": "Placeholder 450x600"},
    {"src": "https://placehold.co/550x550", "alt": "Placeholder 550x550"},
    {"src": "https://placehold.co/700x500", "alt": "Placeholder 700x500"},
    {"src": "https://placehold.co/500x800", "alt": "Placeholder 500x800"},
    {"src": "https://placehold.co/650x450", "alt": "Placeholder 650x450"},
    {"src": "https://placehold.co/400x550", "alt": "Placeholder 400x550"},
    {"src": "https://placehold.co/600x500", "alt": "Placeholder 600x500"},
    {"src": "https://placehold.co/500x500", "alt": "Placeholder 500x500"},
    {"src": "https://placehold.co/700x600", "alt": "Placeholder 700x600"},
]


def normalize_filename(filename: str) -> str:
    """Normaliza o nome do arquivo removendo acentos e substituindo espacos por underline."""
    name, ext = os.path.splitext(filename)
    name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('utf-8')
    name = re.sub(r'[^a-zA-Z0-9_.-]', '_', name)
    name = re.sub(r'_+', '_', name).strip('_')
    if not name:
        name = "foto"
    return f"{name}{ext.lower()}"


def format_title_from_filename(filename: str) -> str:
    """Gera um título / texto alternativo amigável a partir do nome do arquivo."""
    name_no_ext = os.path.splitext(filename)[0]
    cleaned = re.sub(r'[_-]+', ' ', name_no_ext).strip()
    return cleaned.capitalize() if cleaned else "Foto"


def add_to_gitignore(rel_path: str):
    """Adiciona o caminho relativo de uma imagem original ao .gitignore se ainda não estiver."""
    try:
        if GITIGNORE_PATH.exists():
            with open(GITIGNORE_PATH, "r", encoding="utf-8") as f:
                content = f.read()
        else:
            content = ""

        if rel_path not in content:
            with open(GITIGNORE_PATH, "a", encoding="utf-8") as f:
                if not content.endswith("\n"):
                    f.write("\n")
                f.write(f"{rel_path}\n")
            print(f"  [GITIGNORE] Adicionado ao .gitignore: {rel_path}")
    except Exception as e:
        print(f"  [AVISO] Erro ao atualizar .gitignore: {e}")


def convert_image_to_webp(file_path: Path) -> Path:
    """Converte uma imagem para WebP com limite de até 1MB e adiciona original ao .gitignore."""
    if not PIL_AVAILABLE or file_path.suffix.lower() not in CONVERTIBLE_EXTENSIONS:
        return file_path

    normalized_name = normalize_filename(file_path.name)
    base_stem = os.path.splitext(normalized_name)[0]
    webp_path = file_path.parent / f"{base_stem}.webp"

    # Registrar arquivo original no .gitignore
    rel_path = os.path.relpath(file_path, PROJECT_DIR).replace("\\", "/")
    add_to_gitignore(rel_path)

    # Se já existir a versão webp, retornar diretamente
    if webp_path.exists() and webp_path != file_path:
        return webp_path

    try:
        with Image.open(file_path) as img:
            img = ImageOps.exif_transpose(img)
            if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                img = img.convert("RGBA")
            else:
                img = img.convert("RGB")
            
            # 1. Salvar inicial com qualidade padrão (80)
            img.save(webp_path, "WEBP", quality=80)
            
            # 2. Validar tamanho e forçar qualidade menor se passar de 1MB (1048576 bytes)
            if os.path.exists(webp_path) and os.path.getsize(webp_path) > 1048576:
                img.save(webp_path, "WEBP", quality=50)

            # 3. Se mesmo assim passar de 1MB, reduzir resolução gradativamente
            if os.path.exists(webp_path) and os.path.getsize(webp_path) > 1048576:
                max_width = 1800
                if img.width > max_width:
                    ratio = max_width / float(img.width)
                    new_height = int(float(img.height) * ratio)
                    resized_img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
                    resized_img.save(webp_path, "WEBP", quality=50)

            print(f"  [OK] Convertido para WebP (<= 1MB): {file_path.name} -> {webp_path.name}")
        return webp_path
    except Exception as e:
        print(f"  [AVISO] Nao foi possivel converter {file_path.name} para WebP: {e}")
        return file_path


def scan_fotolog_images(auto_convert: bool = True):
    """Varre a pasta assets/fotolog/ e retorna a lista de imagens ordenadas por data de modificacao."""
    if not ASSETS_FOTOLOG_DIR.exists():
        ASSETS_FOTOLOG_DIR.mkdir(parents=True, exist_ok=True)

    found_files = []
    for item in ASSETS_FOTOLOG_DIR.iterdir():
        if item.is_file() and item.suffix.lower() in SUPPORTED_EXTENSIONS:
            found_files.append(item)

    if not found_files:
        return []

    processed_images = []
    seen_stems = set()

    for file_path in found_files:
        if file_path.suffix.lower() in CONVERTIBLE_EXTENSIONS:
            rel_path = os.path.relpath(file_path, PROJECT_DIR).replace("\\", "/")
            add_to_gitignore(rel_path)

        webp_candidate = file_path.parent / f"{normalize_filename(file_path.name).rsplit('.', 1)[0]}.webp"
        
        if auto_convert and file_path.suffix.lower() in CONVERTIBLE_EXTENSIONS:
            if not webp_candidate.exists() or webp_candidate == file_path:
                final_path = convert_image_to_webp(file_path)
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

    # Ordenar por data de modificacao decrescente (mais recentes primeiro)
    processed_images.sort(key=lambda x: x["mtime"], reverse=True)
    return processed_images


def update_fotolog_md(images: list):
    """Gera e grava o conteudo atualizado em fotolog.md."""
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

    with open(FOTOLOG_MD_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"[SUCESSO] fotolog.md atualizado com {len(images)} foto(s)!")


def sync_posts_for_rss(images: list):
    """Cria micro-posts em _posts/ para cada imagem nova para alimentar o feed RSS do blog."""
    if not POSTS_DIR.exists():
        POSTS_DIR.mkdir(parents=True, exist_ok=True)

    # Obter lista de arquivos existentes em _posts/
    existing_posts = list(POSTS_DIR.glob("*.md"))
    existing_contents = {}
    for p in existing_posts:
        try:
            with open(p, "r", encoding="utf-8") as f:
                existing_contents[p.name] = f.read()
        except Exception:
            pass

    created_count = 0
    for img in images:
        # Se for placeholder externo, nao criar post
        if img["src"].startswith("http"):
            continue

        src = img["src"]
        alt = img.get("alt", "Foto")
        stem = img.get("stem", "foto")
        mtime = img.get("mtime", None)

        if mtime:
            dt = datetime.fromtimestamp(mtime)
        else:
            dt = datetime.now()

        date_str = dt.strftime("%Y-%m-%d %H:%M -0300")
        date_prefix = dt.strftime("%Y-%m-%d")
        post_filename = f"{date_prefix}-fotolog-{stem}.md"
        post_path = POSTS_DIR / post_filename

        # Verificar se ja existe algum post referenciando esta imagem
        already_exists = False
        for fname, content in existing_contents.items():
            if src in content:
                already_exists = True
                break

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
            print(f"  [RSS / NOVO POST] Criado _posts/{post_filename}")

    if created_count > 0:
        print(f"[RSS] {created_count} novo(s) micro-post(s) criado(s) em _posts/ para alimentar o feed!")
    else:
        print("[RSS] Todos os posts do RSS já estão sincronizados.")


def main():
    args = sys.argv[1:]

    if "--reset-placeholders" in args:
        print("Restaurando placeholders de demonstracao em fotolog.md...")
        update_fotolog_md(DEFAULT_PLACEHOLDERS)
        return

    auto_convert = "--no-convert" not in args
    generate_posts = "--no-posts" not in args

    print("Varrendo pasta assets/fotolog/...")
    images = scan_fotolog_images(auto_convert=auto_convert)

    if not images:
        print("[INFO] Nenhuma imagem encontrada em assets/fotolog/.")
        print("Dica: Copie suas fotos para a pasta 'assets/fotolog/' e execute este script novamente.")
        print("Mantendo os placeholders de demonstracao ativos para exibicao do layout.")
        if not FOTOLOG_MD_PATH.exists():
            update_fotolog_md(DEFAULT_PLACEHOLDERS)
    else:
        update_fotolog_md(images)
        if generate_posts:
            sync_posts_for_rss(images)


if __name__ == "__main__":
    main()
