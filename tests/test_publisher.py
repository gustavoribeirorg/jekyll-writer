import os
import sys
import pytest
from unittest.mock import MagicMock, patch
from jekyll_writer.publisher import PublisherEngine

def test_publisher_command_success(tmp_path):
    logs = []
    engine = PublisherEngine(log_callback=lambda msg, lvl: logs.append((msg, lvl)))
    success = engine.run_command(f'"{sys.executable}" -c "print(\'Hello World\')"', cwd=str(tmp_path))
    assert success is True
    assert any("Hello World" in log[0] for log in logs)

def test_publisher_command_failure(tmp_path):
    logs = []
    engine = PublisherEngine(log_callback=lambda msg, lvl: logs.append((msg, lvl)))
    success = engine.run_command(f'"{sys.executable}" -c "import sys; sys.exit(1)"', cwd=str(tmp_path))
    assert success is False

def test_publisher_pipeline_missing_root(tmp_path):
    logs = []
    engine = PublisherEngine(log_callback=lambda msg, lvl: logs.append((msg, lvl)))
    success = engine.run_pipeline(
        jekyll_root=str(tmp_path / "non_existent"),
        has_images=False,
        jekyll_cmd="echo test",
        ssh_config={}
    )
    assert success is False
    assert any("não encontrada" in log[0] for log in logs)

def test_publisher_pipeline_with_mocked_steps(tmp_path):
    jekyll_root = tmp_path / "blog"
    jekyll_root.mkdir()
    site_dir = jekyll_root / "_site"
    site_dir.mkdir()
    (site_dir / "index.html").write_text("<html></html>")

    logs = []
    engine = PublisherEngine(log_callback=lambda msg, lvl: logs.append((msg, lvl)))

    with patch.object(engine, "sync_sftp", return_value=True) as mock_sync:
        success = engine.run_pipeline(
            jekyll_root=str(jekyll_root),
            has_images=True,
            jekyll_cmd=f'"{sys.executable}" -c "print(\'build ok\')"',
            ssh_config={"ssh_host": "example.com", "ssh_user": "user"}
        )
        assert success is True
        assert mock_sync.called
        assert any("build ok" in log[0] for log in logs)
        assert any("otimização de imagens" in log[0] for log in logs)

def test_publisher_pipeline_local_mode(tmp_path):
    jekyll_root = tmp_path / "blog"
    jekyll_root.mkdir()
    site_dir = jekyll_root / "_site"
    site_dir.mkdir()
    (site_dir / "index.html").write_text("<html></html>")

    logs = []
    engine = PublisherEngine(log_callback=lambda msg, lvl: logs.append((msg, lvl)))

    with patch.object(engine, "sync_sftp") as mock_sync:
        success = engine.run_pipeline(
            jekyll_root=str(jekyll_root),
            has_images=False,
            jekyll_cmd=f'"{sys.executable}" -c "print(\'build local ok\')"',
            ssh_config=None
        )
        assert success is True
        assert not mock_sync.called
        assert any("Modo Local" in log[0] for log in logs)
        assert any("build local ok" in log[0] for log in logs)

def test_test_ssh_connection_empty():
    engine = PublisherEngine()
    ok, msg = engine.test_ssh_connection({})
    assert ok is False
    assert "obrigatórios" in msg

def test_sync_cache_only_uploads_changed_files(tmp_path):
    local_site = tmp_path / "_site"
    local_site.mkdir()
    file1 = local_site / "index.html"
    file1.write_text("Hello 1", encoding="utf-8")
    file2 = local_site / "about.html"
    file2.write_text("Hello 2", encoding="utf-8")

    cache_file = tmp_path / ".jekyll_writer_cache.json"

    engine = PublisherEngine()
    mock_sftp = MagicMock()

    # First sync: both files uploaded
    uploaded = engine._upload_dir_sftp(mock_sftp, str(local_site), "/remote", cache_file=str(cache_file))
    assert uploaded == 2
    assert mock_sftp.put.call_count == 2

    # Second sync: neither file modified, 0 uploaded
    mock_sftp.reset_mock()
    uploaded2 = engine._upload_dir_sftp(mock_sftp, str(local_site), "/remote", cache_file=str(cache_file))
    assert uploaded2 == 0
    assert mock_sftp.put.call_count == 0

    # Third sync: modify file1 only
    file1.write_text("Hello 1 Modified", encoding="utf-8")
    mock_sftp.reset_mock()
    uploaded3 = engine._upload_dir_sftp(mock_sftp, str(local_site), "/remote", cache_file=str(cache_file))
    assert uploaded3 == 1
    assert mock_sftp.put.call_count == 1

def test_clear_sync_cache(tmp_path):
    cache_file = tmp_path / ".jekyll_writer_cache.json"
    cache_file.write_text('{"file.html": "hash123"}', encoding="utf-8")
    assert cache_file.exists()

    engine = PublisherEngine()
    cleared = engine.clear_sync_cache(str(tmp_path))
    assert cleared is True
    assert not cache_file.exists()

def test_upload_skips_original_when_webp_exists(tmp_path):
    local_site = tmp_path / "_site"
    img_dir = local_site / "assets" / "imagens"
    img_dir.mkdir(parents=True)

    # Create original png and companion webp
    (img_dir / "servidor.png").write_text("original png content")
    (img_dir / "servidor.webp").write_text("converted webp content")
    # And another image that does NOT have webp
    (img_dir / "logo.svg").write_text("<svg></svg>")

    cache_file = tmp_path / ".jekyll_writer_cache.json"

    engine = PublisherEngine()
    mock_sftp = MagicMock()

    uploaded = engine._upload_dir_sftp(mock_sftp, str(local_site), "/remote", cache_file=str(cache_file))
    # Should upload servidor.webp and logo.svg, but SKIP servidor.png
    assert uploaded == 2
    uploaded_files = [call[0][0] for call in mock_sftp.put.call_args_list]
    assert any("servidor.webp" in f for f in uploaded_files)
    assert any("logo.svg" in f for f in uploaded_files)
    assert not any("servidor.png" in f for f in uploaded_files)
