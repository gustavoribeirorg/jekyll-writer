import os
from datetime import datetime
import pytest
from jekyll_writer.frontmatter import (
    generate_new_post_template,
    slugify,
    parse_front_matter,
    generate_post_filename,
    sanitize_custom_filename,
    save_post
)

def test_generate_new_post_template():
    dt = datetime(2026, 9, 1, 12, 30)
    template = generate_new_post_template(dt, timezone_str="-0300")
    assert "layout: post" in template
    assert "date: 2026-09-01 12:30 -0300" in template
    assert "excerpt_separator: <!--more-->" in template
    assert "title: " in template
    assert "categories: " in template
    assert "tags: " in template

def test_slugify():
    assert slugify("Servidor Rodando no Termux!") == "servidor-rodando-no-termux"
    assert slugify("Olá Mundo, Teste 123") == "ola-mundo-teste-123"
    assert slugify("Viagens: Minha Viagem & Fotos") == "viagens-minha-viagem-fotos"

def test_parse_front_matter():
    text = """---
title: Teste de Post
date: 2026-09-01 12:30 -0300
layout: post
categories: Viagens
tags: [jekyll, blog]
---
Conteudo aqui
"""
    fm = parse_front_matter(text)
    assert fm.get("title") == "Teste de Post"
    assert fm.get("categories") == "Viagens"
    assert fm.get("layout") == "post"

def test_generate_post_filename():
    filename = generate_post_filename("Meu Primeiro Post", "2026-09-01 12:30 -0300")
    assert filename == "2026-09-01-meu-primeiro-post.md"

    # With explicit slug
    filename_slug = generate_post_filename("Meu Titulo Muito Longo", "2026-09-01", slug="titulo-curto")
    assert filename_slug == "2026-09-01-titulo-curto.md"

def test_sanitize_custom_filename():
    # Only slug
    assert sanitize_custom_filename("sistema-com-ia", date_str="2026-09-04") == "2026-09-04-sistema-com-ia.md"
    # Full filename with date and .md
    assert sanitize_custom_filename("2026-09-04-sistema-com-ia.md") == "2026-09-04-sistema-com-ia.md"
    # Full filename with date without .md
    assert sanitize_custom_filename("2026-09-04-sistema-com-ia") == "2026-09-04-sistema-com-ia.md"
    # With spaces and accents
    assert sanitize_custom_filename("sistema com inteligência", date_str="2026-09-04") == "2026-09-04-sistema-com-inteligencia.md"
    # Path traversal attempt is sanitized
    assert sanitize_custom_filename("../../etc/sistema.md", date_str="2026-09-04") == "2026-09-04-sistema.md"

def test_save_post(tmp_path):
    posts_dir = tmp_path / "_posts"
    posts_dir.mkdir()
    content = """---
title: Post Incrivel
date: 2026-09-01 12:30 -0300
layout: post
---
Texto legal
"""
    saved_path = save_post(content, str(posts_dir))
    assert os.path.exists(saved_path)
    assert os.path.basename(saved_path) == "2026-09-01-post-incrivel.md"

    # Saving again with same path should update in place
    updated_content = content + "\nNova linha"
    saved_path_again = save_post(updated_content, str(posts_dir), current_filepath=saved_path)
    assert saved_path_again == saved_path
    with open(saved_path, "r", encoding="utf-8") as f:
        assert "Nova linha" in f.read()

def test_save_post_custom_filename_and_rename(tmp_path):
    posts_dir = tmp_path / "_posts"
    posts_dir.mkdir()
    content = """---
title: Fazendo um sistema com IA
date: 2026-09-04 10:00:00 -0300
layout: post
---
Conteudo
"""
    # 1. Save with custom filename (short slug)
    saved_path = save_post(
        content,
        str(posts_dir),
        custom_filename="sistema-com-ia"
    )
    assert os.path.basename(saved_path) == "2026-09-04-sistema-com-ia.md"
    assert os.path.exists(saved_path)

    # 2. Rename existing post by changing custom_filename
    renamed_path = save_post(
        content,
        str(posts_dir),
        current_filepath=saved_path,
        custom_filename="2026-09-04-sistema-ia-v2.md"
    )
    assert os.path.basename(renamed_path) == "2026-09-04-sistema-ia-v2.md"
    assert os.path.exists(renamed_path)
    # Old file should have been removed
    assert not os.path.exists(saved_path)
