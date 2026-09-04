import os
import pytest
from PIL import Image
from jekyll_writer.image_optimizer import optimize_images

def test_optimize_images_deletes_original_by_default(tmp_path):
    # Setup mock jekyll project
    assets_dir = tmp_path / "assets" / "imagens"
    assets_dir.mkdir(parents=True)
    
    # Create test png
    img_path = assets_dir / "foto teste.png"
    img = Image.new("RGB", (100, 100), color="blue")
    img.save(img_path)

    # Create test markdown file referencing the image
    posts_dir = tmp_path / "_posts"
    posts_dir.mkdir(parents=True)
    post_file = posts_dir / "2026-09-01-meu-post.md"
    post_file.write_text('Veja a imagem: src="assets/imagens/foto teste.png"', encoding="utf-8")

    logs = []
    converted = optimize_images(str(tmp_path), log_callback=lambda msg, lvl: logs.append((msg, lvl)))

    assert converted == 1
    # Check that webp exists
    webp_path = assets_dir / "foto_teste.webp"
    assert webp_path.exists()

    # Check that original png was removed to save disk space
    assert not img_path.exists()

    # Check that post was updated
    updated_content = post_file.read_text(encoding="utf-8")
    assert "foto_teste.webp" in updated_content
    assert 'src="/assets/imagens/' in updated_content

    # Check log message
    assert any("Original excluído para economizar espaço" in msg for msg, lvl in logs)


def test_optimize_images_keeps_original_when_delete_originals_false(tmp_path):
    assets_dir = tmp_path / "assets" / "imagens"
    assets_dir.mkdir(parents=True)

    img_path = assets_dir / "foto teste.png"
    img = Image.new("RGB", (100, 100), color="blue")
    img.save(img_path)

    logs = []
    converted = optimize_images(str(tmp_path), log_callback=lambda msg, lvl: logs.append((msg, lvl)), delete_originals=False)

    assert converted == 1
    webp_path = assets_dir / "foto_teste.webp"
    assert webp_path.exists()
    # Original should be kept
    assert img_path.exists()

    # Check gitignore
    gitignore_path = tmp_path / ".gitignore"
    assert gitignore_path.exists()
    assert "assets/imagens/foto teste.png" in gitignore_path.read_text(encoding="utf-8").replace("\\", "/")


def test_optimize_images_deletes_orphan_original_when_webp_already_exists(tmp_path):
    assets_dir = tmp_path / "assets" / "imagens"
    assets_dir.mkdir(parents=True)

    img_path = assets_dir / "foto.png"
    img = Image.new("RGB", (100, 100), color="green")
    img.save(img_path)

    webp_path = assets_dir / "foto.webp"
    img.save(webp_path, "WEBP")

    assert img_path.exists()
    assert webp_path.exists()

    logs = []
    converted = optimize_images(str(tmp_path), log_callback=lambda msg, lvl: logs.append((msg, lvl)), delete_originals=True)

    assert converted == 0
    assert webp_path.exists()
    # Original should be deleted even if WebP was already present
    assert not img_path.exists()
    assert any("WebP já existe" in msg for msg, lvl in logs)
