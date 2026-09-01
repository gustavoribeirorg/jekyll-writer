import os
import pytest
from PIL import Image
from jekyll_writer.fotolog import update_fotolog

def test_update_fotolog(tmp_path):
    # Setup mock jekyll project
    fotolog_assets = tmp_path / "assets" / "fotolog"
    fotolog_assets.mkdir(parents=True)
    posts_dir = tmp_path / "_posts"
    posts_dir.mkdir(parents=True)

    # Create a test image
    img_path = fotolog_assets / "viagem praia.jpg"
    img = Image.new("RGB", (100, 100), color="green")
    img.save(img_path)

    logs = []
    success = update_fotolog(str(tmp_path), log_callback=lambda msg, lvl: logs.append((msg, lvl)))

    assert success is True
    # Check that webp was generated
    webp_path = fotolog_assets / "viagem_praia.webp"
    assert webp_path.exists()

    # Check fotolog.md was created
    fotolog_md = tmp_path / "fotolog.md"
    assert fotolog_md.exists()
    content = fotolog_md.read_text(encoding="utf-8")
    assert "/assets/fotolog/viagem_praia.webp" in content
    assert "layout: fotolog" in content

    # Check that micro-post was created in _posts
    created_posts = list(posts_dir.glob("*-fotolog-viagem_praia.md"))
    assert len(created_posts) == 1
    post_content = created_posts[0].read_text(encoding="utf-8")
    assert "layout: post" in post_content
    assert "categories: [Fotolog]" in post_content
