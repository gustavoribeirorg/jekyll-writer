import os
import pytest
from jekyll_writer.config import ConfigManager
from jekyll_writer.ui import JekyllWriterApp

def test_app_initialization_and_template(tmp_path):
    cfg_file = tmp_path / "config.json"
    cfg = ConfigManager(str(cfg_file))
    app = JekyllWriterApp(config_manager=cfg)
    
    # Check that textbox contains initial template
    content = app.textbox.get("1.0", "end-1c")
    assert "layout: post" in content
    assert "excerpt_separator: <!--more-->" in content
    assert "title: " in content

    # Test toggling log drawer
    assert app.log_drawer_visible is False
    app.toggle_log_drawer()
    assert app.log_drawer_visible is True
    app.toggle_log_drawer()
    assert app.log_drawer_visible is False

    app.destroy()

def test_format_list_multiline(tmp_path):
    cfg_file = tmp_path / "config.json"
    cfg = ConfigManager(str(cfg_file))
    app = JekyllWriterApp(config_manager=cfg)

    # Set content with 3 lines
    app.textbox.delete("1.0", "end")
    app.textbox.insert("1.0", "Primeira linha\nSegunda linha\nTerceira linha")

    # Select all
    app.textbox.tag_add("sel", "1.0", "end-1c")

    # Call format list
    app._format_list()

    result = app.textbox.get("1.0", "end-1c")
    assert result == "- Primeira linha\n- Segunda linha\n- Terceira linha"

    # Toggle list off
    app.textbox.tag_add("sel", "1.0", "end-1c")
    app._format_list()
    result_off = app.textbox.get("1.0", "end-1c")
    assert result_off == "Primeira linha\nSegunda linha\nTerceira linha"

    app.destroy()
