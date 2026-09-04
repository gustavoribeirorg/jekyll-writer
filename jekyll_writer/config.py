import json
import os
from typing import Any, Dict

DEFAULT_CONFIG = {
    "jekyll_root": "",
    "ssh_host": "",
    "ssh_port": 22,
    "ssh_user": "",
    "ssh_password": "",
    "ssh_remote_path": "",
    "jekyll_command": "bundle exec jekyll build",
    "deploy_mode": "local",
}

def resolve_path(path: str) -> str:
    """
    Expands user home (~), environment variables ($HOME, %VAR%),
    leading HOME/ (without $), and handles Termux, Windows, and Linux fallbacks.
    """
    if not path or not isinstance(path, str):
        return ""

    p = path.strip()

    # 1. If user typed HOME/... or HOME\... without $, prefix with $
    if p == "HOME" or p.startswith("HOME/") or p.startswith("HOME\\"):
        p = "$" + p

    # 2. Determine best home directory candidate
    termux_home = "/data/data/com.termux/files/home"
    is_termux = os.path.exists(termux_home)
    home = os.environ.get("HOME") or os.environ.get("USERPROFILE")
    if not home and is_termux:
        home = termux_home

    # 3. Explicitly expand tilde ~ (handles cases on Android where os.path.expanduser fails if HOME is unset)
    if p.startswith("~/") or p.startswith("~\\"):
        if home:
            p = home + p[1:]
        else:
            p = os.path.expanduser(p)
    elif p == "~":
        p = home or os.path.expanduser(p)
    else:
        p = os.path.expanduser(p)

    # 4. Expand environment variables
    p = os.path.expandvars(p)

    # 5. Fallback for $HOME or ${HOME}
    for var_token in ("$HOME", "${HOME}"):
        if var_token in p:
            h = home or (termux_home if is_termux else "")
            if h:
                p = p.replace(var_token, h)

    # 6. Normalize separators
    if os.name == "posix":
        p = p.replace("\\", "/")
        p = os.path.normpath(p)
    else:
        p = os.path.normpath(p)

    return p


class ConfigManager:
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.data: Dict[str, Any] = DEFAULT_CONFIG.copy()
        self.load()

    def load(self) -> Dict[str, Any]:
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    self.data.update(saved)
            except Exception:
                pass
        return self.data

    def save(self, extra_data: Dict[str, Any] = None) -> None:
        if extra_data:
            self.data.update(extra_data)
        dir_name = os.path.dirname(os.path.abspath(self.config_path))
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.data[key] = value

    def get_jekyll_root(self) -> str:
        root = self.get("jekyll_root", "")
        return resolve_path(root) if root else ""

    def validate_jekyll_root(self) -> Dict[str, Any]:
        root = self.get_jekyll_root()
        exists = bool(root and os.path.isdir(root))
        posts_dir = self.get_posts_dir()
        posts_dir_exists = bool(posts_dir and os.path.isdir(posts_dir))
        posts_count = 0
        if posts_dir_exists:
            try:
                posts_count = len([
                    f for f in os.listdir(posts_dir)
                    if f.endswith((".md", ".markdown")) and os.path.isfile(os.path.join(posts_dir, f))
                ])
            except Exception:
                pass
        return {
            "configured_root": self.get("jekyll_root", ""),
            "resolved_root": root,
            "root_exists": exists,
            "posts_dir": posts_dir,
            "posts_dir_exists": posts_dir_exists,
            "posts_count": posts_count,
        }

    def get_posts_dir(self) -> str:
        root = self.get_jekyll_root()
        if not root or not os.path.isdir(root):
            return ""
        underscore_posts = os.path.join(root, "_posts")
        if os.path.isdir(underscore_posts):
            return underscore_posts
        plain_posts = os.path.join(root, "posts")
        if os.path.isdir(plain_posts):
            return plain_posts
        # Default to _posts if neither exists yet
        return underscore_posts
