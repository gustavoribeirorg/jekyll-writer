import os
import pytest
from jekyll_writer.images import (
    is_fotolog_category,
    format_caption_from_filename,
    generate_figure_html,
    process_and_copy_image
)

def test_is_fotolog_category():
    assert is_fotolog_category("Fotolog") is True
    assert is_fotolog_category(["Fotolog", "Tecnologia"]) is True
    assert is_fotolog_category("fotolog") is True
    assert is_fotolog_category("Geral") is False
    assert is_fotolog_category(None) is False

def test_format_caption_from_filename():
    assert format_caption_from_filename("servidor-rodando.png") == "Servidor rodando"
    assert format_caption_from_filename("minha_foto_de_ferias.jpeg") == "Minha foto de ferias"

def test_generate_figure_html():
    html = generate_figure_html("/assets/imagens/servidor-rodando.webp", "Servidor rodando")
    expected = (
        '<figure>\n'
        '    <img src="/assets/imagens/servidor-rodando.webp" alt="Servidor rodando">\n'
        '        <figcaption>Servidor rodando</figcaption>\n'
        '</figure>'
    )
    assert html == expected

def test_process_and_copy_image_standard(tmp_path):
    jekyll_root = tmp_path / "blog"
    jekyll_root.mkdir()
    source_img = tmp_path / "minha-foto.png"
    source_img.write_text("fake image content")

    html_snippet, dest_path = process_and_copy_image(
        source_image_path=str(source_img),
        jekyll_root=str(jekyll_root),
        is_fotolog=False
    )

    assert os.path.exists(dest_path)
    assert '<img src="/assets/imagens/minha-foto.webp" alt="Minha foto">' in html_snippet
    assert '<figcaption>Minha foto</figcaption>' in html_snippet
    assert dest_path == str(jekyll_root / "assets" / "imagens" / "minha-foto.png")

def test_process_and_copy_image_fotolog(tmp_path):
    jekyll_root = tmp_path / "blog"
    jekyll_root.mkdir()
    source_img = tmp_path / "foto-camera.jpg"
    source_img.write_text("fake image content")

    html_snippet, dest_path = process_and_copy_image(
        source_image_path=str(source_img),
        jekyll_root=str(jekyll_root),
        is_fotolog=True
    )

    assert os.path.exists(dest_path)
    assert '<img src="/assets/fotolog/foto-camera.webp" alt="Foto camera">' in html_snippet
    assert '<figcaption>Foto camera</figcaption>' in html_snippet
    assert dest_path == str(jekyll_root / "assets" / "fotolog" / "foto-camera.jpg")
