# Jekyll Writer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir um aplicativo desktop Windows nativo e autônomo (standalone) para redação e publicação automatizada em blogs Jekyll, com gerador de front matter, inserção inteligente de imagens em tags `<figure>` com extensão `.webp`, cópia automática para pastas de assets/fotolog, execução de scripts pré-build, compilação local com `bundle exec jekyll build`, sincronização SSH/SFTP com gaveta de logs em tempo real, e script para compilar em `.exe`.

**Architecture:** O sistema adota uma arquitetura modular em Python com interface `customtkinter` (Dark/Light mode moderno), motor assíncrono via `threading` para execução de subprocessos (`scripts/*.py` e `bundle exec jekyll build`) com captura contínua de logs, e `paramiko` para sincronização recursiva SFTP segura com autenticação direta por senha/usuário.

**Tech Stack:** Python 3.10+, CustomTkinter, Paramiko, PyYAML, Pillow, PyInstaller, Pytest.

**Spec:** [`docs/superpowers/specs/2026-09-01-jekyll-writer-design.md`](file:///c:/Users/Gustavo%20Ribeiro.DESKTOP-MQL7L2R/Desktop/jekyll-writer/docs/superpowers/specs/2026-09-01-jekyll-writer-design.md)

## Global Constraints

- Sistema operacional alvo: Windows.
- Formato de data no front matter: `YYYY-MM-DD HH:MM -0300` (respeitando fuso local).
- Nomenclatura de post: `YYYY-MM-DD-<slug-do-titulo>.md` salvo em `_posts/` ou `posts/` dentro da raiz do Jekyll.
- Tag de imagem: sempre `<figure><img src="..." alt="..."><figcaption>...</figcaption></figure>` com extensão `.webp`.
- Destino de imagem: `assets/fotolog/` se categoria for `Fotolog`, senão `assets/imagens/`.
- Build: `bundle exec jekyll build` executado na pasta raiz do blog.
- Sincronização: arquivos de `_site/` enviados para o destino SSH informado nas configurações com exibição de progresso.

---

### Task 1: Project Setup and Dependencies

**Files:**
- Create: `requirements.txt`
- Create: `jekyll_writer/__init__.py`
- Test: Environment dependency validation

**Interfaces:**
- Produces: Base project structure and installed Python libraries (`customtkinter`, `paramiko`, `pyyaml`, `pillow`, `pytest`, `pyinstaller`).

- [ ] **Step 1: Write requirements.txt**

```txt
customtkinter>=5.2.0
paramiko>=3.4.0
pyyaml>=6.0.1
pillow>=10.2.0
pytest>=8.0.0
pyinstaller>=6.4.0
```

- [ ] **Step 2: Create package directory and __init__.py**

Create `jekyll_writer/__init__.py` with module version.

- [ ] **Step 3: Install dependencies**

Run: `pip install -r requirements.txt`
Expected: Successfully installed all packages.

- [ ] **Step 4: Commit**

```bash
git add requirements.txt jekyll_writer/__init__.py
git commit -m "chore: setup project structure and dependencies"
```

---

### Task 2: Configuration Manager (`jekyll_writer/config.py`)

**Files:**
- Create: `jekyll_writer/config.py`
- Create: `tests/test_config.py`

**Interfaces:**
- Produces: `ConfigManager` class with methods:
  - `load() -> dict`
  - `save(data: dict) -> None`
  - `get(key: str, default=None) -> Any`
  - `set(key: str, value: Any) -> None`
  - `get_posts_dir() -> str` (detects `_posts` or `posts` inside `jekyll_root`)

- [ ] **Step 1: Write the failing tests**

```python
import os
import json
import pytest
from jekyll_writer.config import ConfigManager

def test_default_config(tmp_path):
    config_file = tmp_path / "config.json"
    cfg = ConfigManager(str(config_file))
    assert cfg.get("ssh_port") == 22
    assert cfg.get("jekyll_command") == "bundle exec jekyll build"

def test_save_and_load(tmp_path):
    config_file = tmp_path / "config.json"
    cfg = ConfigManager(str(config_file))
    cfg.set("ssh_host", "ssh.exemplo.com")
    cfg.set("ssh_user", "usuario_teste")
    cfg.save()

    cfg2 = ConfigManager(str(config_file))
    assert cfg2.get("ssh_host") == "ssh.exemplo.com"
    assert cfg2.get("ssh_user") == "usuario_teste"

def test_detect_posts_dir(tmp_path):
    cfg_file = tmp_path / "config.json"
    cfg = ConfigManager(str(cfg_file))
    # when _posts exists
    posts_dir = tmp_path / "_posts"
    posts_dir.mkdir()
    cfg.set("jekyll_root", str(tmp_path))
    assert cfg.get_posts_dir() == str(posts_dir)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_config.py -v`
Expected: FAIL (ModuleNotFoundError or AttributeError)

- [ ] **Step 3: Implement ConfigManager**

```python
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
}

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
        os.makedirs(os.path.dirname(os.path.abspath(self.config_path)), exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.data[key] = value

    def get_posts_dir(self) -> str:
        root = self.get("jekyll_root", "")
        if not root or not os.path.isdir(root):
            return ""
        underscore_posts = os.path.join(root, "_posts")
        if os.path.isdir(underscore_posts):
            return underscore_posts
        plain_posts = os.path.join(root, "posts")
        if os.path.isdir(plain_posts):
            return plain_posts
        # Default to creating _posts if neither exists
        return underscore_posts
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_config.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add jekyll_writer/config.py tests/test_config.py
git commit -m "feat: implement configuration manager with persistence"
```

---

### Task 3: Front Matter and Post File Manager (`jekyll_writer/frontmatter.py`)

**Files:**
- Create: `jekyll_writer/frontmatter.py`
- Create: `tests/test_frontmatter.py`

**Interfaces:**
- Produces:
  - `generate_new_post_template(now: datetime = None) -> str`
  - `slugify(text: str) -> str`
  - `parse_front_matter(content: str) -> dict`
  - `generate_post_filename(title: str, date_str: str) -> str`
  - `save_post(content: str, posts_dir: str, current_filepath: str = None) -> str`

- [ ] **Step 1: Write failing tests**

```python
import os
from datetime import datetime
import pytest
from jekyll_writer.frontmatter import (
    generate_new_post_template,
    slugify,
    parse_front_matter,
    generate_post_filename,
    save_post
)

def test_generate_new_post_template():
    dt = datetime(2026, 9, 1, 12, 30)
    template = generate_new_post_template(dt, timezone_str="-0300")
    assert "layout: post" in template
    assert "date: 2026-09-01 12:30 -0300" in template
    assert "excerpt_separator: <!--more-->" in template
    assert "title: " in template

def test_slugify():
    assert slugify("Servidor Rodando no Termux!") == "servidor-rodando-no-termux"
    assert slugify("Olá Mundo, Teste 123") == "ola-mundo-teste-123"

def test_parse_front_matter():
    text = """---
title: Teste de Post
date: 2026-09-01 12:30 -0300
layout: post
categories: Fotolog
---
Conteudo aqui
"""
    fm = parse_front_matter(text)
    assert fm.get("title") == "Teste de Post"
    assert fm.get("categories") == "Fotolog"

def test_generate_post_filename():
    filename = generate_post_filename("Meu Primeiro Post", "2026-09-01 12:30 -0300")
    assert filename == "2026-09-01-meu-primeiro-post.md"

def test_save_post(tmp_path):
    posts_dir = tmp_path / "_posts"
    posts_dir.mkdir()
    content = """---
title: Post Incrivel
date: 2026-09-01 12:30 -0300
layout: post
---
Texto legal
"""
    saved_path = save_post(content, str(posts_dir))
    assert os.path.exists(saved_path)
    assert os.path.basename(saved_path) == "2026-09-01-post-incrivel.md"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_frontmatter.py -v`
Expected: FAIL

- [ ] **Step 3: Implement Front Matter & Post functions**

```python
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
    try:
        data = yaml.safe_load(match.group(1))
        return data if isinstance(data, dict) else {}
    except Exception:
        # Fallback simple parser if YAML syntax is incomplete while editing
        data = {}
        for line in match.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                data[k.strip()] = v.strip()
        return data

def generate_post_filename(title: str, date_str: str = None) -> str:
    # Extract YYYY-MM-DD from date_str
    date_prefix = ""
    if date_str:
        m = re.match(r"(\d{4}-\d{2}-\d{2})", str(date_str).strip())
        if m:
            date_prefix = m.group(1)
    if not date_prefix:
        date_prefix = datetime.now().strftime("%Y-%m-%d")

    slug = slugify(title) if title else "sem-titulo"
    return f"{date_prefix}-{slug}.md"

def save_post(content: str, posts_dir: str, current_filepath: str = None) -> str:
    os.makedirs(posts_dir, exist_ok=True)
    fm = parse_front_matter(content)
    title = fm.get("title", "")
    date_str = fm.get("date", "")

    if current_filepath and os.path.dirname(os.path.abspath(current_filepath)) == os.path.abspath(posts_dir):
        # Update existing file
        target_path = current_filepath
    else:
        filename = generate_post_filename(title, str(date_str))
        target_path = os.path.join(posts_dir, filename)

    with open(target_path, "w", encoding="utf-8") as f:
        f.write(content)

    return target_path
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_frontmatter.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add jekyll_writer/frontmatter.py tests/test_frontmatter.py
git commit -m "feat: implement front matter generator, parser and post file saver"
```

---

### Task 4: Image Handler & HTML Figure Generator (`jekyll_writer/images.py`)

**Files:**
- Create: `jekyll_writer/images.py`
- Create: `tests/test_images.py`

**Interfaces:**
- Produces:
  - `is_fotolog_category(categories: Any) -> bool`
  - `generate_figure_html(image_relative_path: str, caption: str) -> str`
  - `process_and_copy_image(source_image_path: str, jekyll_root: str, is_fotolog: bool) -> tuple[str, str]` (returns html snippet and copied destination path)

- [ ] **Step 1: Write failing tests**

```python
import os
import pytest
from jekyll_writer.images import (
    is_fotolog_category,
    generate_figure_html,
    process_and_copy_image
)

def test_is_fotolog_category():
    assert is_fotolog_category("Fotolog") is True
    assert is_fotolog_category(["Fotolog", "Tecnologia"]) is True
    assert is_fotolog_category("fotolog") is True
    assert is_fotolog_category("Geral") is False

def test_generate_figure_html():
    html = generate_figure_html("/assets/imagens/servidor-rodando.webp", "Servidor rodando")
    expected = (
        '<figure>\n'
        '    <img src="/assets/imagens/servidor-rodando.webp" alt="Servidor rodando">\n'
        '        <figcaption>Servidor rodando</figcaption>\n'
        '</figure>'
    )
    assert html == expected

def test_process_and_copy_image_standard(tmp_path):
    jekyll_root = tmp_path / "blog"
    jekyll_root.mkdir()
    source_img = tmp_path / "minha-foto.png"
    source_img.write_text("fake image content")

    html_snippet, dest_path = process_and_copy_image(
        source_image_path=str(source_img),
        jekyll_root=str(jekyll_root),
        is_fotolog=False
    )

    assert os.path.exists(dest_path)
    assert "/assets/imagens/minha-foto.webp" in html_snippet
    assert dest_path == str(jekyll_root / "assets" / "imagens" / "minha-foto.png")

def test_process_and_copy_image_fotolog(tmp_path):
    jekyll_root = tmp_path / "blog"
    jekyll_root.mkdir()
    source_img = tmp_path / "foto-camera.jpg"
    source_img.write_text("fake image content")

    html_snippet, dest_path = process_and_copy_image(
        source_image_path=str(source_img),
        jekyll_root=str(jekyll_root),
        is_fotolog=True
    )

    assert os.path.exists(dest_path)
    assert "/assets/fotolog/foto-camera.webp" in html_snippet
    assert dest_path == str(jekyll_root / "assets" / "fotolog" / "foto-camera.jpg")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_images.py -v`
Expected: FAIL

- [ ] **Step 3: Implement Image Handler**

```python
import os
import shutil
from pathlib import Path
from jekyll_writer.frontmatter import slugify

def is_fotolog_category(categories) -> bool:
    if not categories:
        return False
    if isinstance(categories, list):
        return any(str(c).strip().lower() == "fotolog" for c in categories)
    return "fotolog" in str(categories).strip().lower()

def format_caption_from_filename(filename: str) -> str:
    stem = Path(filename).stem
    # Replace dashes/underscores with spaces and capitalize
    words = stem.replace("-", " ").replace("_", " ").split()
    if not words:
        return "Imagem"
    return " ".join(words).capitalize()

def generate_figure_html(web_path: str, caption: str) -> str:
    return (
        '<figure>\n'
        f'    <img src="{web_path}" alt="{caption}">\n'
        f'        <figcaption>{caption}</figcaption>\n'
        '</figure>'
    )

def process_and_copy_image(source_image_path: str, jekyll_root: str, is_fotolog: bool) -> tuple[str, str]:
    source = Path(source_image_path)
    stem_slug = slugify(source.stem)
    ext = source.suffix.lower()

    dest_folder_rel = "assets/fotolog" if is_fotolog else "assets/imagens"
    dest_dir = os.path.join(jekyll_root, dest_folder_rel.replace("/", os.sep))
    os.makedirs(dest_dir, exist_ok=True)

    dest_filename = f"{stem_slug}{ext}"
    dest_path = os.path.join(dest_dir, dest_filename)
    shutil.copy2(source_image_path, dest_path)

    # Web URL always uses forward slashes and always ends in .webp
    web_url = f"/{dest_folder_rel}/{stem_slug}.webp"
    caption = format_caption_from_filename(dest_filename)
    html_snippet = generate_figure_html(web_url, caption)

    return html_snippet, dest_path
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_images.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add jekyll_writer/images.py tests/test_images.py
git commit -m "feat: implement image copier and webp figure html generator"
```

---

### Task 5: Pipeline & SSH/SFTP Transfer Engine (`jekyll_writer/publisher.py`)

**Files:**
- Create: `jekyll_writer/publisher.py`
- Create: `tests/test_publisher.py`

**Interfaces:**
- Produces: `PublisherEngine` class with callbacks for log streaming:
  - `run_command(cmd: str, cwd: str) -> bool`
  - `run_pipeline(jekyll_root: str, is_fotolog: bool, has_images: bool, jekyll_cmd: str, ssh_config: dict) -> bool`
  - `sync_sftp(local_dir: str, remote_dir: str, ssh_config: dict) -> bool`

- [ ] **Step 1: Write failing tests for command runner & pipeline logic**

```python
import pytest
from unittest.mock import MagicMock, patch
from jekyll_writer.publisher import PublisherEngine

def test_publisher_command_success(tmp_path):
    logs = []
    engine = PublisherEngine(log_callback=lambda msg, lvl: logs.append((msg, lvl)))
    success = engine.run_command('python -c "print(\'Hello World\')"', cwd=str(tmp_path))
    assert success is True
    assert any("Hello World" in log[0] for log in logs)

def test_publisher_command_failure(tmp_path):
    logs = []
    engine = PublisherEngine(log_callback=lambda msg, lvl: logs.append((msg, lvl)))
    success = engine.run_command('python -c "import sys; sys.exit(1)"', cwd=str(tmp_path))
    assert success is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_publisher.py -v`
Expected: FAIL

- [ ] **Step 3: Implement PublisherEngine**

```python
import os
import subprocess
import paramiko
from typing import Callable, Optional, Dict, Any

class PublisherEngine:
    def __init__(self, log_callback: Optional[Callable[[str, str], None]] = None):
        """
        log_callback(message: str, level: str)
        level: 'info', 'success', 'warning', 'error'
        """
        self.log_callback = log_callback or (lambda msg, lvl: print(f"[{lvl.upper()}] {msg}"))
        self._is_cancelled = False

    def log(self, message: str, level: str = "info"):
        self.log_callback(message, level)

    def cancel(self):
        self._is_cancelled = True

    def run_command(self, cmd: str, cwd: str) -> bool:
        self.log(f"Executando: {cmd} em {cwd}", "info")
        try:
            process = subprocess.Popen(
                cmd,
                cwd=cwd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace"
            )

            while True:
                if self._is_cancelled:
                    process.terminate()
                    self.log("Processo cancelado pelo usuário.", "warning")
                    return False
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    self.log(line.rstrip(), "info")

            rc = process.poll()
            if rc == 0:
                self.log(f"Comando concluído com sucesso (código 0).", "success")
                return True
            else:
                self.log(f"Comando falhou com código {rc}.", "error")
                return False
        except Exception as e:
            self.log(f"Erro ao executar comando: {e}", "error")
            return False

    def sync_sftp(self, local_dir: str, remote_dir: str, ssh_config: Dict[str, Any]) -> bool:
        host = ssh_config.get("ssh_host")
        port = int(ssh_config.get("ssh_port", 22))
        user = ssh_config.get("ssh_user")
        password = ssh_config.get("ssh_password")

        if not host or not user:
            self.log("Configurações de SSH incompletas (Host ou Usuário ausentes).", "error")
            return False

        self.log(f"Conectando via SSH a {user}@{host}:{port}...", "info")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            ssh.connect(hostname=host, port=port, username=user, password=password, timeout=15)
            self.log("Conexão SSH estabelecida com sucesso.", "success")
            sftp = ssh.open_sftp()

            # Expand ~ in remote path if present
            if remote_dir.startswith("~"):
                # Get remote home dir
                stdin, stdout, stderr = ssh.exec_command("pwd")
                home = stdout.read().decode().strip()
                remote_dir = remote_dir.replace("~", home, 1)

            self.log(f"Iniciando transferência recursiva para {remote_dir}...", "info")
            self._upload_dir_sftp(sftp, local_dir, remote_dir)
            sftp.close()
            ssh.close()
            self.log("Transferência SFTP concluída com sucesso.", "success")
            return True
        except Exception as e:
            self.log(f"Falha na transferência SSH/SFTP: {e}", "error")
            return False

    def _upload_dir_sftp(self, sftp, local_dir: str, remote_dir: str):
        try:
            sftp.stat(remote_dir)
        except IOError:
            sftp.mkdir(remote_dir)

        for item in os.listdir(local_dir):
            if self._is_cancelled:
                return
            local_path = os.path.join(local_dir, item)
            remote_path = f"{remote_dir}/{item}".replace("\\", "/")

            if os.path.isdir(local_path):
                self._upload_dir_sftp(sftp, local_path, remote_path)
            else:
                self.log(f"Enviando: {item}", "info")
                sftp.put(local_path, remote_path)

    def run_pipeline(
        self,
        jekyll_root: str,
        is_fotolog: bool,
        has_images: bool,
        jekyll_cmd: str,
        ssh_config: Dict[str, Any]
    ) -> bool:
        self._is_cancelled = False
        self.log("=== INICIANDO PIPELINE DE PUBLICAÇÃO ===", "info")

        # 1. Scripts pré-build
        scripts_dir = os.path.join(jekyll_root, "scripts")
        if is_fotolog:
            fotolog_script = os.path.join(scripts_dir, "atualizar_fotolog.py")
            if os.path.exists(fotolog_script):
                self.log(">> Rodando script de Fotolog...", "info")
                if not self.run_command(f"python scripts/atualizar_fotolog.py", cwd=jekyll_root):
                    return False
            else:
                self.log(f">> Aviso: {fotolog_script} não encontrado. Pulando.", "warning")

        if has_images:
            optimize_script = os.path.join(scripts_dir, "otimizar_imagens.py")
            if os.path.exists(optimize_script):
                self.log(">> Rodando otimização de imagens...", "info")
                if not self.run_command(f"python scripts/otimizar_imagens.py", cwd=jekyll_root):
                    return False
            else:
                self.log(f">> Aviso: {optimize_script} não encontrado. Pulando.", "warning")

        # 2. Build do Jekyll
        self.log(f">> Construindo site Jekyll ({jekyll_cmd})...", "info")
        if not self.run_command(jekyll_cmd, cwd=jekyll_root):
            self.log("Build do Jekyll falhou. Interrompendo envio.", "error")
            return False

        # 3. Transferência SFTP
        site_dir = os.path.join(jekyll_root, "_site")
        if not os.path.isdir(site_dir):
            self.log(f"Pasta de saída '{site_dir}' não encontrada após a build.", "error")
            return False

        remote_path = ssh_config.get("ssh_remote_path", "~/blog/_site")
        self.log(f">> Enviando arquivos da pasta _site para {remote_path}...", "info")
        if not self.sync_sftp(site_dir, remote_path, ssh_config):
            return False

        self.log("=== PUBLICAÇÃO ENVIADA COM SUCESSO! ===", "success")
        return True
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_publisher.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add jekyll_writer/publisher.py tests/test_publisher.py
git commit -m "feat: implement publisher engine with command streaming and sftp upload"
```

---

### Task 6: Graphical User Interface (`jekyll_writer/ui.py` & `main.py`)

**Files:**
- Create: `jekyll_writer/ui.py`
- Create: `main.py`
- Test: GUI launch and integration test

**Interfaces:**
- Produces: Complete CustomTkinter application with:
  - Toolbar with markdown insertion buttons (B, I, H2, H3, Link, Quote, Code, List, More), Inserir Imagem, Novo Post, Salvar Post, Enviar Publicação, Configurações.
  - Distraction-free text editor with keyboard shortcuts (`Ctrl+S`, `Ctrl+B`, `Ctrl+I`, etc.).
  - Expandable real-time Log Console with colored text tags.
  - Settings Modal dialog with SSH Test Connection and directory pickers.

- [ ] **Step 1: Implement UI MainWindow and SettingsDialog in `jekyll_writer/ui.py`**
- [ ] **Step 2: Implement application entry point `main.py`**
- [ ] **Step 3: Test launching headless/smoke check and verify all buttons connect to backend logic**
- [ ] **Step 4: Commit**

```bash
git add jekyll_writer/ui.py main.py
git commit -m "feat: build modern CustomTkinter desktop interface with real-time logs"
```

---

### Task 7: Windows Standalone Packaging (`build_exe.bat`)

**Files:**
- Create: `build_exe.bat`
- Test: PyInstaller executable generation and launch test

**Interfaces:**
- Produces: `dist/JekyllWriter.exe` - self-contained single-file executable for Windows.

- [ ] **Step 1: Create `build_exe.bat` with PyInstaller command**
- [ ] **Step 2: Execute PyInstaller build**
- [ ] **Step 3: Verify that `dist/JekyllWriter.exe` is generated**
- [ ] **Step 4: Commit**

```bash
git add build_exe.bat
git commit -m "chore: add pyinstaller build script for standalone windows exe"
```
