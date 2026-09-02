import os
import shutil
from pathlib import Path
from typing import Tuple
from jekyll_writer.frontmatter import slugify

def format_caption_from_filename(filename: str) -> str:
    stem = Path(filename).stem
    # Replace dashes/underscores with spaces and capitalize
    words = stem.replace("-", " ").replace("_", " ").split()
    if not words:
        return "Imagem"
    return " ".join(words).capitalize()

def generate_figure_html(web_path: str, caption: str) -> str:
    return (
        '<figure>\n'
        f'    <img src="{web_path}" alt="{caption}">\n'
        f'        <figcaption>{caption}</figcaption>\n'
        '</figure>'
    )

def process_and_copy_image(source_image_path: str, jekyll_root: str) -> Tuple[str, str]:
    source = Path(source_image_path)
    stem_slug = slugify(source.stem)
    ext = source.suffix.lower()

    dest_folder_rel = "assets/imagens"
    dest_dir = os.path.join(jekyll_root, dest_folder_rel.replace("/", os.sep))
    os.makedirs(dest_dir, exist_ok=True)

    dest_filename = f"{stem_slug}{ext}"
    dest_path = os.path.join(dest_dir, dest_filename)
    shutil.copy2(source_image_path, dest_path)

    # Web URL always uses forward slashes and always ends in .webp
    web_url = f"/{dest_folder_rel}/{stem_slug}.webp"
    caption = format_caption_from_filename(source.name)
    html_snippet = generate_figure_html(web_url, caption)

    return html_snippet, dest_path
