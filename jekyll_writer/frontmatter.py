import os
import re
import unicodedata
from datetime import datetime, timezone, timedelta
import yaml

def parse_timezone_str(tz_str: str) -> timezone:
    """Parses offset string like '-0300', '+02:00', '-03:00', 'Z' into datetime.timezone."""
    if not tz_str:
        return timezone(timedelta(hours=-3))
    cleaned = str(tz_str).strip()
    if cleaned.upper() == "Z":
        return timezone.utc
    m = re.match(r"^([+-])(\d{2}):?(\d{2})$", cleaned)
    if m:
        sign = 1 if m.group(1) == "+" else -1
        hours = int(m.group(2))
        minutes = int(m.group(3))
        return timezone(sign * timedelta(hours=hours, minutes=minutes))
    return timezone(timedelta(hours=-3))

def get_current_formatted_date(
    dt: datetime = None,
    timezone_str: str = "-0300",
    client_date: str = None,
) -> str:
    if client_date and str(client_date).strip():
        return str(client_date).strip()

    target_tz = parse_timezone_str(timezone_str)
    if dt is None:
        dt = datetime.now(timezone.utc).astimezone(target_tz)
    elif dt.tzinfo is None:
        return dt.strftime(f"%Y-%m-%d %H:%M {timezone_str}")
    else:
        dt = dt.astimezone(target_tz)

    tz_formatted = dt.strftime("%z")
    if not tz_formatted:
        tz_formatted = timezone_str
    return dt.strftime(f"%Y-%m-%d %H:%M {tz_formatted}")

def generate_new_post_template(
    dt: datetime = None,
    timezone_str: str = "-0300",
    client_date: str = None,
) -> str:
    date_str = get_current_formatted_date(dt, timezone_str, client_date=client_date)
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

def sanitize_custom_filename(custom_name: str, date_str: str = None, title: str = None) -> str:
    """Sanitizes a user-specified custom filename.

    Ensures safe characters, date prefix YYYY-MM-DD-, and .md extension.
    If the user provided only a slug (e.g. 'sistema-com-ia'), the date prefix
    and .md extension are automatically added.
    """
    raw = os.path.basename(str(custom_name or '').strip())
    ext = ".md"
    match_ext = re.search(r"\.(md|markdown|html)$", raw, re.IGNORECASE)
    if match_ext:
        ext = match_ext.group(0).lower()
        raw = raw[:match_ext.start()]

    date_prefix = ""
    match_date = re.match(r"^(\d{4}-\d{2}-\d{2})-(.*)$", raw)
    if match_date:
        date_prefix = match_date.group(1)
        slug_part = match_date.group(2)
    else:
        if date_str:
            m = re.match(r"(\d{4}-\d{2}-\d{2})", str(date_str).strip())
            if m:
                date_prefix = m.group(1)
        if not date_prefix:
            date_prefix = datetime.now(timezone.utc).astimezone(parse_timezone_str("-0300")).strftime("%Y-%m-%d")
        slug_part = raw

    slug = slugify(slug_part) if slug_part else (slugify(title) if title else "sem-titulo")
    if not slug:
        slug = "sem-titulo"

    return f"{date_prefix}-{slug}{ext}"


def generate_post_filename(title: str, date_str: str = None, slug: str = None) -> str:
    date_prefix = ""
    if date_str:
        m = re.match(r"(\d{4}-\d{2}-\d{2})", str(date_str).strip())
        if m:
            date_prefix = m.group(1)
    if not date_prefix:
        date_prefix = datetime.now(timezone.utc).astimezone(parse_timezone_str("-0300")).strftime("%Y-%m-%d")

    target_slug = slugify(slug) if slug else (slugify(title) if title else "sem-titulo")
    if not target_slug:
        target_slug = "sem-titulo"
    return f"{date_prefix}-{target_slug}.md"


def save_post(
    content: str,
    posts_dir: str,
    current_filepath: str = None,
    custom_filename: str = None,
) -> str:
    os.makedirs(posts_dir, exist_ok=True)
    fm = parse_front_matter(content)
    title = fm.get("title", "")
    date_str = fm.get("date", "")
    frontmatter_slug = fm.get("slug", "")

    if custom_filename and str(custom_filename).strip():
        filename = sanitize_custom_filename(custom_filename, date_str=date_str, title=title)
        target_path = os.path.join(posts_dir, filename)
    elif current_filepath and os.path.exists(current_filepath):
        same_dir = os.path.dirname(os.path.abspath(current_filepath)) == os.path.abspath(posts_dir)
        if same_dir:
            target_path = current_filepath
        else:
            filename = generate_post_filename(title, str(date_str), slug=frontmatter_slug)
            target_path = os.path.join(posts_dir, filename)
    else:
        filename = generate_post_filename(title, str(date_str), slug=frontmatter_slug)
        target_path = os.path.join(posts_dir, filename)

    # If renaming an existing post, remove old file if paths differ
    if current_filepath and os.path.isfile(current_filepath):
        abs_current = os.path.abspath(current_filepath)
        abs_target = os.path.abspath(target_path)
        if abs_current != abs_target and os.path.dirname(abs_current) == os.path.abspath(posts_dir):
            try:
                os.remove(current_filepath)
            except OSError:
                pass

    with open(target_path, "w", encoding="utf-8") as f:
        f.write(content)

    return target_path
