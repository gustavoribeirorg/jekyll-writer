from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Tuple

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

    if os.path.isdir(p):
        return os.path.abspath(p)

    # 7. Smart fallback for proot / Termux / relative paths:
    # If the path does not exist (e.g., user is inside proot Debian where ~ is /root,
    # but the blog is in Termux home /data/data/com.termux/files/home/...),
    # search common candidate locations for a folder with the same name containing _posts or _config.yml
    subname = os.path.basename(p.rstrip("/\\"))
    if subname:
        candidates = [
            os.path.join(termux_home, subname),
            os.path.join("/root", subname),
            os.path.join("/home", subname),
            os.path.abspath(os.path.join(os.getcwd(), "..", subname)),
            os.path.abspath(os.path.join(os.getcwd(), subname)),
        ]
        for cand in candidates:
            cand_clean = cand.replace("\\", "/") if os.name == "posix" else os.path.normpath(cand)
            if os.path.isdir(cand_clean):
                if (
                    os.path.exists(os.path.join(cand_clean, "_posts"))
                    or os.path.exists(os.path.join(cand_clean, "posts"))
                    or os.path.exists(os.path.join(cand_clean, "_config.yml"))
                ):
                    return os.path.abspath(cand_clean)

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

    @staticmethod
    def auto_detect_jekyll_roots() -> list:
        search_roots = [
            "/data/data/com.termux/files/home",
            os.environ.get("HOME", ""),
            os.path.expanduser("~"),
            "/root",
            "/home",
            os.path.abspath(os.path.join(os.getcwd(), "..")),
            os.getcwd(),
        ]
        detected = []
        seen = set()
        for s_root in search_roots:
            if not s_root or not os.path.isdir(s_root):
                continue
            try:
                # Check s_root itself
                if (
                    os.path.exists(os.path.join(s_root, "_config.yml"))
                    or os.path.exists(os.path.join(s_root, "_posts"))
                ):
                    norm = os.path.normpath(s_root).replace("\\", "/") if os.name == "posix" else os.path.normpath(s_root)
                    if norm not in seen:
                        detected.append(norm)
                        seen.add(norm)
                # Check 1 level of subdirectories
                for entry in os.listdir(s_root):
                    sub = os.path.join(s_root, entry)
                    if os.path.isdir(sub):
                        if (
                            os.path.exists(os.path.join(sub, "_config.yml"))
                            or os.path.exists(os.path.join(sub, "_posts"))
                        ):
                            norm = os.path.normpath(sub).replace("\\", "/") if os.name == "posix" else os.path.normpath(sub)
                            if norm not in seen:
                                detected.append(norm)
                                seen.add(norm)
            except Exception:
                pass
        return detected

    def validate_jekyll_root(self, test_path: Optional[str] = None) -> Dict[str, Any]:
        raw = test_path if test_path is not None else self.get("jekyll_root", "")
        root = resolve_path(raw) if raw else ""
        exists = bool(root and os.path.isdir(root))
        posts_dir = ""
        posts_dir_exists = False
        posts_count = 0
        if exists:
            underscore_posts = os.path.join(root, "_posts")
            plain_posts = os.path.join(root, "posts")
            if os.path.isdir(underscore_posts):
                posts_dir = underscore_posts
                posts_dir_exists = True
            elif os.path.isdir(plain_posts):
                posts_dir = plain_posts
                posts_dir_exists = True
            if posts_dir_exists:
                try:
                    posts_count = len([
                        f for f in os.listdir(posts_dir)
                        if (f.endswith(".md") or f.endswith(".markdown")) and os.path.isfile(os.path.join(posts_dir, f))
                    ])
                except Exception:
                    pass
        candidates = self.auto_detect_jekyll_roots()
        return {
            "configured_root": raw,
            "resolved_root": root,
            "root_exists": exists,
            "posts_dir": posts_dir,
            "posts_dir_exists": posts_dir_exists,
            "posts_count": posts_count,
            "detected_candidates": candidates,
            "server_home": os.environ.get("HOME") or os.path.expanduser("~"),
            "server_user": os.environ.get("USER", "unknown"),
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
