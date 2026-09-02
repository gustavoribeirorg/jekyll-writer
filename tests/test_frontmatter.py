import os
from datetime import datetime
import pytest
from jekyll_writer.frontmatter import (
    generate_new_post_template,
    slugify,
    parse_front_matter,
    generate_post_filename,
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
