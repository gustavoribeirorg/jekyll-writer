import os
import json
import pytest
from jekyll_writer.config import ConfigManager

def test_default_config(tmp_path):
    config_file = tmp_path / "config.json"
    cfg = ConfigManager(str(config_file))
    assert cfg.get("ssh_port") == 22
    assert cfg.get("jekyll_command") == "bundle exec jekyll build"
    assert cfg.get("ssh_host") == ""
    assert cfg.get("ssh_user") == ""

def test_save_and_load(tmp_path):
    config_file = tmp_path / "config.json"
    cfg = ConfigManager(str(config_file))
    cfg.set("ssh_host", "meuhost.com")
    cfg.set("ssh_user", "usuario_teste")
    cfg.save()

    cfg2 = ConfigManager(str(config_file))
    assert cfg2.get("ssh_host") == "meuhost.com"
    assert cfg2.get("ssh_user") == "usuario_teste"

def test_detect_posts_dir_underscore(tmp_path):
    cfg_file = tmp_path / "config.json"
    cfg = ConfigManager(str(cfg_file))
    posts_dir = tmp_path / "_posts"
    posts_dir.mkdir()
    cfg.set("jekyll_root", str(tmp_path))
    assert cfg.get_posts_dir() == str(posts_dir)

def test_detect_posts_dir_plain(tmp_path):
    cfg_file = tmp_path / "config.json"
    cfg = ConfigManager(str(cfg_file))
    posts_dir = tmp_path / "posts"
    posts_dir.mkdir()
    cfg.set("jekyll_root", str(tmp_path))
    assert cfg.get_posts_dir() == str(posts_dir)


def test_resolve_path_empty():
    from jekyll_writer.config import resolve_path
    assert resolve_path("") == ""
    assert resolve_path(None) == ""


def test_resolve_path_home(monkeypatch):
    from jekyll_writer.config import resolve_path
    monkeypatch.setenv("HOME", "/data/data/com.termux/files/home")
    resolved = resolve_path("$HOME/gustavoribeiro-net")
    assert resolved == os.path.normpath("/data/data/com.termux/files/home/gustavoribeiro-net")

    resolved_braces = resolve_path("${HOME}/gustavoribeiro-net")
    assert resolved_braces == os.path.normpath("/data/data/com.termux/files/home/gustavoribeiro-net")


def test_config_get_jekyll_root_resolves_home(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    cfg_file = tmp_path / "config.json"
    cfg = ConfigManager(str(cfg_file))
    cfg.set("jekyll_root", "$HOME/myblog")
    assert cfg.get_jekyll_root() == os.path.normpath(str(tmp_path / "myblog"))


def test_detect_posts_dir_with_home_variable(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    cfg_file = tmp_path / "config.json"
    cfg = ConfigManager(str(cfg_file))
    posts_dir = tmp_path / "myblog" / "_posts"
    posts_dir.mkdir(parents=True)
    cfg.set("jekyll_root", "$HOME/myblog")
    assert cfg.get_posts_dir() == os.path.normpath(str(posts_dir))


def test_resolve_path_without_dollar(monkeypatch):
    from jekyll_writer.config import resolve_path
    monkeypatch.setenv("HOME", "/data/data/com.termux/files/home")
    resolved = resolve_path("HOME/gustavoribeiro-net")
    assert resolved == os.path.normpath("/data/data/com.termux/files/home/gustavoribeiro-net")


def test_resolve_path_tilde(monkeypatch):
    from jekyll_writer.config import resolve_path
    monkeypatch.setenv("HOME", "/data/data/com.termux/files/home")
    resolved = resolve_path("~/gustavoribeiro-net")
    assert resolved == os.path.normpath("/data/data/com.termux/files/home/gustavoribeiro-net")


def test_validate_jekyll_root(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    cfg_file = tmp_path / "config.json"
    cfg = ConfigManager(str(cfg_file))
    cfg.set("jekyll_root", "HOME/myblog")

    # Before dir exists
    val = cfg.validate_jekyll_root()
    assert val["root_exists"] is False
    assert val["posts_dir_exists"] is False

    # Create root
    myblog = tmp_path / "myblog"
    myblog.mkdir()
    val = cfg.validate_jekyll_root()
    assert val["root_exists"] is True
    assert val["posts_dir_exists"] is False

    # Create _posts with 2 markdown files
    posts = myblog / "_posts"
    posts.mkdir()
    (posts / "2026-01-01-post1.md").write_text("content", encoding="utf-8")
    (posts / "2026-01-02-post2.md").write_text("content", encoding="utf-8")
    (posts / "not_a_post.txt").write_text("txt", encoding="utf-8")

    val = cfg.validate_jekyll_root()
    assert val["root_exists"] is True
    assert val["posts_dir_exists"] is True
    assert val["posts_count"] == 2
