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
    and handles platform-specific HOME/USERPROFILE fallback.
    """
    if not path or not isinstance(path, str):
        return ""
    expanded = os.path.expanduser(path.strip())
    expanded = os.path.expandvars(expanded)
    for var_name in ("$HOME", "${HOME}"):
        if var_name in expanded:
            home = os.environ.get("HOME") or os.environ.get("USERPROFILE", "")
            expanded = expanded.replace(var_name, home)
    return os.path.normpath(expanded)


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
