import os
import sys
import pytest
from unittest.mock import MagicMock, patch
from jekyll_writer.publisher import PublisherEngine


def test_get_portable_paths_none_when_empty(tmp_path):
    paths = PublisherEngine.get_portable_paths(base_dir=str(tmp_path))
    assert paths["cloudflared"] is None
    assert paths["ruby_bin"] is None
    assert paths["ruby_root"] is None


def test_get_portable_paths_detection_in_bin(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    cf_exe = bin_dir / "cloudflared.exe"
    cf_exe.touch()

    ruby_dir = tmp_path / "ruby"
    ruby_bin = ruby_dir / "bin"
    ruby_bin.mkdir(parents=True)

    paths = PublisherEngine.get_portable_paths(base_dir=str(tmp_path))
    assert paths["cloudflared"] == str(cf_exe)
    assert paths["ruby_bin"] == str(ruby_bin)
    assert paths["ruby_root"] == str(ruby_dir)


def test_get_portable_paths_detection_in_root(tmp_path):
    cf_exe = tmp_path / "cloudflared.exe"
    cf_exe.touch()

    paths = PublisherEngine.get_portable_paths(base_dir=str(tmp_path))
    assert paths["cloudflared"] == str(cf_exe)
    assert paths["ruby_bin"] is None
    assert paths["ruby_root"] is None


def test_get_portable_paths_frozen(monkeypatch, tmp_path):
    fake_exe = tmp_path / "app" / "jekyll-writer.exe"
    fake_exe.parent.mkdir(parents=True)
    fake_exe.touch()

    cf_exe = tmp_path / "app" / "bin" / "cloudflared.exe"
    cf_exe.parent.mkdir(parents=True)
    cf_exe.touch()

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(fake_exe))

    paths = PublisherEngine.get_portable_paths()
    assert paths["cloudflared"] == str(cf_exe)


def test_get_build_env_without_portable(tmp_path):
    engine = PublisherEngine()
    env = engine.get_build_env(base_dir=str(tmp_path))
    assert "GEM_HOME" not in env or env.get("GEM_HOME") == os.environ.get("GEM_HOME")
    assert "GEM_PATH" not in env or env.get("GEM_PATH") == os.environ.get("GEM_PATH")


def test_get_build_env_with_portable(tmp_path):
    ruby_bin = tmp_path / "ruby" / "bin"
    ruby_bin.mkdir(parents=True)

    gems_dir = tmp_path / "ruby" / "lib" / "ruby" / "gems" / "4.0.0"
    gems_dir.mkdir(parents=True)

    ssl_dir = tmp_path / "ruby" / "ssl"
    ssl_dir.mkdir(parents=True)
    cert_file = ssl_dir / "cert.pem"
    cert_file.touch()

    engine = PublisherEngine()
    env = engine.get_build_env(base_dir=str(tmp_path))

    path_sep = os.pathsep
    assert env["PATH"].startswith(f"{str(ruby_bin)}{path_sep}")
    assert env["GEM_HOME"] == str(gems_dir)
    assert env["GEM_PATH"] == str(gems_dir)
    assert env["SSL_CERT_FILE"] == str(cert_file)


def test_check_cloudflared_in_ssh_config_portable_priority(tmp_path, monkeypatch):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    cf_exe = bin_dir / "cloudflared.exe"
    cf_exe.touch()

    engine = PublisherEngine()
    monkeypatch.setattr(
        PublisherEngine,
        "get_portable_paths",
        staticmethod(lambda base_dir=None: {"cloudflared": str(cf_exe), "ruby_bin": None, "ruby_root": None})
    )

    detected = engine._check_cloudflared_in_ssh_config("some-host")
    assert detected == str(cf_exe)


def test_run_command_passes_build_env(monkeypatch):
    engine = PublisherEngine()
    mock_popen = MagicMock()
    mock_popen.return_value.poll.return_value = 0
    mock_popen.return_value.stdout.readline.return_value = ""

    fake_env = {"DUMMY_KEY": "DUMMY_VALUE"}
    monkeypatch.setattr(engine, "get_build_env", lambda: fake_env)
    monkeypatch.setattr("subprocess.Popen", mock_popen)

    res = engine.run_command("echo hello", cwd=".")
    assert res is True
    assert mock_popen.called
    assert mock_popen.call_args[1].get("env") == fake_env
