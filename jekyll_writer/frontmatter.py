import os
import re
import unicodedata
from datetime import datetime
import yaml

def get_current_formatted_date(dt: datetime = None, timezone_str: str = "-0300") -> str:
    if dt is None:
        dt = datetime.now()
    return dt.strftime(f"%Y-%m-%d %H:%M {timezone_str}")

def generate_new_post_template(dt: datetime = None, timezone_str: str = "-0300") -> str:
    date_str = get_current_formatted_date(dt, timezone_str)
    return (
        "---\n"
        "title: \n"
        f"date: {date_str}\n"
        "layout: post\n"
        "excerpt_separator: <!--more-->\n"
        "categories: \n"
        "tags: \n"
        "---\n\n"
    )

def slugify(text: str) -> str:
    if not text:
        return ""
    # Normalize unicode to ASCII
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    # Replace non-alphanumeric with hyphen
    text = re.sub(r"[^\w\s-]", "", text.lower())
    text = re.sub(r"[-\s]+", "-", text).strip("-")
    return text

def parse_front_matter(content: str) -> dict:
    match = re.match(r"^---\s*\n(.*?)\n---\s*(?:\n|$)", content, re.DOTALL)
    if not match:
        return {}
    raw_yaml = match.group(1)
    try:
        data = yaml.safe_load(raw_yaml)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    # Fallback line-by-line parser for resilience while user is typing
    data = {}
    for line in raw_yaml.splitlines():
        line = line.strip()
        if ":" in line:
            k, v = line.split(":", 1)
            k = k.strip()
            v = v.strip()
            # Clean quotes if any
            if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                v = v[1:-1]
            data[k] = v
    return data

def generate_post_filename(title: str, date_str: str = None) -> str:
    date_prefix = ""
    if date_str:
        m = re.match(r"(\d{4}-\d{2}-\d{2})", str(date_str).strip())
        if m:
            date_prefix = m.group(1)
    if not date_prefix:
        date_prefix = datetime.now().strftime("%Y-%m-%d")

    slug = slugify(title) if title else "sem-titulo"
    if not slug:
        slug = "sem-titulo"
    return f"{date_prefix}-{slug}.md"

def save_post(content: str, posts_dir: str, current_filepath: str = None) -> str:
    os.makedirs(posts_dir, exist_ok=True)
    fm = parse_front_matter(content)
    title = fm.get("title", "")
    date_str = fm.get("date", "")

    if current_filepath and os.path.exists(current_filepath):
        # Check if it's already in the target posts dir
        same_dir = os.path.dirname(os.path.abspath(current_filepath)) == os.path.abspath(posts_dir)
        if same_dir:
            target_path = current_filepath
        else:
            filename = generate_post_filename(title, str(date_str))
            target_path = os.path.join(posts_dir, filename)
    else:
        filename = generate_post_filename(title, str(date_str))
        target_path = os.path.join(posts_dir, filename)

    with open(target_path, "w", encoding="utf-8") as f:
        f.write(content)

    return target_path
