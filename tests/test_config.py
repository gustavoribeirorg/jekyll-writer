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
