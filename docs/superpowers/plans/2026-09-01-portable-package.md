# Plano de Implementação: Pacote Portátil Completo (JekyllWriter-Portable)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir uma distribuição portátil completa (`JekyllWriter-Portable.zip`) que rode com duplo clique em qualquer máquina Windows sem necessidade de instalar Ruby, Jekyll, gemas ou o utilitário Cloudflare no sistema operacional.

**Architecture:** O `JekyllWriter.exe` detectará se pastas irmãs `ruby/` e `bin/` existem ao seu lado. Se existirem, ele injeta automaticamente o caminho do Ruby portátil e as variáveis de ambiente (`GEM_HOME`, `GEM_PATH`, `PATH`) no momento do build e usa o `cloudflared.exe` embutido para o túnel SSH, operando 100% desconectado do registro e das pastas de sistema do Windows. Um script automatizado `build_portable.py` empacotará tudo em `dist/JekyllWriter-Portable.zip`.

**Tech Stack:** Python 3.14, PyInstaller, CustomTkinter, Paramiko, Pillow, PyYAML, Ruby 4.0 (UCrt x64 standalone runtime), Cloudflare Tunnel CLI.

---

## Global Constraints

- O aplicativo deve continuar funcionando normalmente em máquinas que usam o Ruby do sistema se a pasta `ruby/` não estiver presente (retrocompatibilidade).
- O pacote portátil deve ser auto-contido em uma única pasta raiz (`JekyllWriter-Portable/`) compactada em `.zip`.
- Nenhum terminal ou prompt de comando preto deve piscar durante o build ou conexão (`CREATE_NO_WINDOW`).
- Todos os testes unitários existentes (26 testes) devem continuar passando e novos testes devem cobrir a detecção portátil.

---

## Proposed Changes & Tasks

### Task 1: Detecção de Componentes Portáteis no `PublisherEngine`
**Files:**
- Modify: `jekyll_writer/publisher.py`
- Test: `tests/test_portable.py`

**Interfaces:**
- Produces: `PublisherEngine.get_portable_paths(base_dir: Optional[str] = None) -> Dict[str, Optional[str]]`
- Produces: `PublisherEngine.get_build_env(base_dir: Optional[str] = None) -> Dict[str, str]`

- [ ] **Step 1: Escrever testes unitários em `tests/test_portable.py`**
  - Testar detecção de `bin/cloudflared.exe` local.
  - Testar configuração de `PATH`, `GEM_HOME` e `GEM_PATH` quando `ruby/bin` existe.
  - Testar fallback gracioso quando pastas portáteis não existem.

- [ ] **Step 2: Rodar testes para garantir que falham**
  - `python -m pytest tests/test_portable.py`

- [ ] **Step 3: Implementar métodos de detecção e injeção de ambiente em `jekyll_writer/publisher.py`**
  - Obter `base_dir` via `sys.executable` (em binário frozen) ou `__file__`.
  - Preferir `bin/cloudflared.exe` relativo ao executável.
  - Injetar `ruby/bin`, `GEM_HOME`, `GEM_PATH` no `run_command`.

- [ ] **Step 4: Rodar testes para verificar sucesso**
  - `python -m pytest tests/test_portable.py`

- [ ] **Step 5: Commit das mudanças**
  - `git commit -m "feat: add portable ruby and cloudflared detection"`

---

### Task 2: Script de Empacotamento Automatizado (`build_portable.py`)
**Files:**
- Create: `build_portable.py`
- Modify: `.gitignore`

- [ ] **Step 1: Criar o script `build_portable.py`**
  - Compilar `dist/JekyllWriter.exe` via PyInstaller (se não compilado).
  - Criar estrutura `dist/JekyllWriter-Portable/`:
    - `JekyllWriter.exe`
    - `bin/cloudflared.exe` (copiado de `C:\Program Files (x86)\cloudflared\cloudflared.exe`)
    - `ruby/bin/` (ruby.exe, bundle.bat, jekyll.bat + DLLs de runtime)
    - `ruby/lib/` (standard library + gemas pré-instaladas)
    - `ruby/ssl/` (certificados SSL)
    - `LEIAME.txt` com instruções simples de uso.
  - Compactar para `dist/JekyllWriter-Portable.zip`.

- [ ] **Step 2: Executar `build_portable.py` e validar tamanho e arquivos**
  - Rodar `python build_portable.py`.
  - Confirmar geração do `.zip` e integridade da pasta.

- [ ] **Step 3: Executar a suíte de testes completa**
  - `python -m pytest -v`

- [ ] **Step 4: Commit e Walkthrough**
  - `git commit -m "feat: implement build_portable.py distribution bundler"`

---

## Verification Plan

### Automated Tests
- Executar `python -m pytest -v` (26 testes existentes + novos testes de portabilidade).

### Manual Verification
- Testar compilação do Jekyll diretamente contra o `ruby/` da pasta portátil gerada para confirmar que `bundle exec jekyll build` conclui com exit code 0 sem depender do `PATH` global do Windows.
- Conferir arquivo `dist/JekyllWriter-Portable.zip` gerado.
