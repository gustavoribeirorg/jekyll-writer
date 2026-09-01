#!/usr/bin/env python
"""
build_portable.py - Script de empacotamento automatizado da distribuição portátil do Jekyll Writer.

Cria a pasta dist/JekyllWriter-Portable/ contendo:
- JekyllWriter.exe (compilado via PyInstaller se necessário)
- bin/cloudflared.exe
- ruby/bin/ (ruby.exe, bundle.bat, jekyll.bat, DLLs de runtime)
- ruby/lib/ (bibliotecas e gemas)
- ruby/ssl/ (certificados SSL)
- LEIAME.txt (instruções de uso)
E gera o arquivo compactado dist/JekyllWriter-Portable.zip.
"""

import os
import sys
import glob
import time
import shutil
import zipfile
import argparse
import subprocess

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

LEIAME_TEXT = """=====================================================
Jekyll Writer - Distribuição Portátil para Windows
=====================================================

Esta pasta contém tudo o que você precisa para escrever,
otimizar imagens, compilar o blog Jekyll e publicar via SSH.

COMO USAR:
1. Basta dar dois cliques em "JekyllWriter.exe".
2. Não é necessário instalar Ruby, gemas ou Cloudflare CLI.
3. Ao abrir pela primeira vez em um novo computador, clique
   em Configurações (⚙️) para selecionar a pasta do seu blog.
=====================================================
"""

DEFAULT_RUBY_DIR = r"C:\Ruby40-x64"
DEFAULT_CLOUDFLARED = r"C:\Program Files (x86)\cloudflared\cloudflared.exe"

def find_ruby_dir(preferred: str = DEFAULT_RUBY_DIR) -> str:
    if os.path.isdir(preferred):
        return preferred
    candidates = [
        r"C:\Ruby40-x64",
        r"C:\Ruby33-x64",
        r"C:\Ruby32-x64",
        r"C:\Ruby31-x64",
        r"C:\Ruby30-x64",
    ]
    for c in candidates:
        if os.path.isdir(c):
            return c
    raise FileNotFoundError(f"Diretório do Ruby não encontrado em {preferred} nem em caminhos padrão.")

def find_cloudflared(preferred: str = DEFAULT_CLOUDFLARED) -> str:
    if os.path.isfile(preferred):
        return preferred
    candidates = [
        r"C:\Program Files (x86)\cloudflared\cloudflared.exe",
        r"C:\Program Files\cloudflared\cloudflared.exe",
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    which = shutil.which("cloudflared") or shutil.which("cloudflared.exe")
    if which and os.path.isfile(which):
        return which
    raise FileNotFoundError(f"cloudflared.exe não encontrado em {preferred} nem no PATH.")

def ensure_executable(project_root: str, dist_dir: str, force_rebuild: bool = False) -> str:
    exe_path = os.path.join(dist_dir, "JekyllWriter.exe")
    if os.path.isfile(exe_path) and not force_rebuild:
        print(f"[OK] JekyllWriter.exe encontrado: {exe_path}")
        return exe_path

    print("[*] JekyllWriter.exe não encontrado ou reconstrução solicitada.")
    print("[*] Compilando executável com PyInstaller...")
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconsole",
        "--onefile",
        "--name",
        "JekyllWriter",
        "--collect-all",
        "customtkinter",
        "main.py"
    ]
    print(f"    Executando: {' '.join(cmd)}")
    subprocess.run(cmd, cwd=project_root, check=True)

    if not os.path.isfile(exe_path):
        raise FileNotFoundError(f"Falha ao gerar executável: {exe_path} não existe após build.")

    print(f"[OK] Executável compilado com sucesso: {exe_path}")
    return exe_path

def build_portable_package(
    project_root: str,
    ruby_dir: str,
    cloudflared_path: str,
    force_rebuild_exe: bool = False
) -> tuple[str, str, float]:
    start_time = time.time()
    dist_dir = os.path.join(project_root, "dist")
    portable_dir = os.path.join(dist_dir, "JekyllWriter-Portable")
    zip_path = os.path.join(dist_dir, "JekyllWriter-Portable.zip")

    os.makedirs(dist_dir, exist_ok=True)

    # 1. Garantir que o JekyllWriter.exe existe
    exe_src = ensure_executable(project_root, dist_dir, force_rebuild=force_rebuild_exe)

    # 2. Limpar diretório portátil anterior se existir
    if os.path.isdir(portable_dir):
        print(f"[*] Limpando diretório portátil existente: {portable_dir}")
        shutil.rmtree(portable_dir)
    os.makedirs(portable_dir, exist_ok=True)

    # 3. Copiar JekyllWriter.exe para a raiz do pacote portátil
    print(f"[*] Copiando JekyllWriter.exe para {portable_dir}...")
    shutil.copy2(exe_src, os.path.join(portable_dir, "JekyllWriter.exe"))

    # 4. Copiar cloudflared.exe para bin/
    portable_bin = os.path.join(portable_dir, "bin")
    os.makedirs(portable_bin, exist_ok=True)
    print(f"[*] Copiando cloudflared.exe ({cloudflared_path}) para {portable_bin}...")
    shutil.copy2(cloudflared_path, os.path.join(portable_bin, "cloudflared.exe"))

    # 5. Montar ruby/bin/
    ruby_bin_dest = os.path.join(portable_dir, "ruby", "bin")
    os.makedirs(ruby_bin_dest, exist_ok=True)
    ruby_bin_src = os.path.join(ruby_dir, "bin")

    # Arquivos essenciais de ruby/bin
    ruby_bin_files = ["ruby.exe", "bundle.bat", "bundle", "jekyll.bat", "jekyll"]
    for item in os.listdir(ruby_bin_src):
        if item.endswith(".dll") and "ruby" in item.lower() and item not in ruby_bin_files:
            ruby_bin_files.append(item)
    print(f"[*] Copiando executáveis e scripts do Ruby ({ruby_bin_src})...")
    for f in ruby_bin_files:
        src_file = os.path.join(ruby_bin_src, f)
        if os.path.isfile(src_file):
            shutil.copy2(src_file, os.path.join(ruby_bin_dest, f))
        else:
            print(f"    [AVISO] Arquivo {f} não encontrado em {ruby_bin_src}")

    # Copiar todas as DLLs de runtime (ucrt64\\bin\\*.dll)
    ucrt_bin_src = os.path.join(ruby_dir, "msys64", "ucrt64", "bin")
    if os.path.isdir(ucrt_bin_src):
        dlls = glob.glob(os.path.join(ucrt_bin_src, "*.dll"))
        print(f"[*] Copiando {len(dlls)} DLLs de runtime de {ucrt_bin_src}...")
        for dll in dlls:
            shutil.copy2(dll, os.path.join(ruby_bin_dest, os.path.basename(dll)))
    else:
        # Fallback: copiar DLLs encontradas diretamente em ruby/bin
        fallback_dlls = glob.glob(os.path.join(ruby_bin_src, "*.dll"))
        print(f"[*] Diretório ucrt64/bin não encontrado. Copiando {len(fallback_dlls)} DLLs de {ruby_bin_src}...")
        for dll in fallback_dlls:
            dest = os.path.join(ruby_bin_dest, os.path.basename(dll))
            if not os.path.exists(dest):
                shutil.copy2(dll, dest)

    # 6. Copiar ruby/lib/ recursivamente
    ruby_lib_src = os.path.join(ruby_dir, "lib")
    ruby_lib_dest = os.path.join(portable_dir, "ruby", "lib")
    print(f"[*] Copiando bibliotecas e gemas ({ruby_lib_src} -> {ruby_lib_dest})...")
    shutil.copytree(ruby_lib_src, ruby_lib_dest, dirs_exist_ok=True)

    # 7. Copiar ruby/ssl/ recursivamente
    ruby_ssl_src = os.path.join(ruby_dir, "ssl")
    ruby_ssl_dest = os.path.join(portable_dir, "ruby", "ssl")
    if os.path.isdir(ruby_ssl_src):
        print(f"[*] Copiando certificados SSL ({ruby_ssl_src} -> {ruby_ssl_dest})...")
        shutil.copytree(ruby_ssl_src, ruby_ssl_dest, dirs_exist_ok=True)

    # 8. Criar LEIAME.txt
    leiame_path = os.path.join(portable_dir, "LEIAME.txt")
    print(f"[*] Criando {leiame_path}...")
    with open(leiame_path, "w", encoding="utf-8") as f:
        f.write(LEIAME_TEXT)

    # 9. Compactar para dist/JekyllWriter-Portable.zip
    if os.path.isfile(zip_path):
        os.remove(zip_path)

    print(f"[*] Compactando {portable_dir} em {zip_path}...")
    file_count = 0
    total_uncompressed_bytes = 0

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
        for root, _, files in os.walk(portable_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, dist_dir)
                zipf.write(file_path, arcname)
                file_count += 1
                total_uncompressed_bytes += os.path.getsize(file_path)

    elapsed = time.time() - start_time
    zip_size_mb = os.path.getsize(zip_path) / (1024 * 1024)
    uncompressed_mb = total_uncompressed_bytes / (1024 * 1024)

    print("\n" + "=" * 60)
    print("[OK] PACOTE PORTATIL GERADO COM SUCESSO!")
    print("=" * 60)
    print(f" Pasta de origem:       {portable_dir}")
    print(f" Arquivo compactado:    {zip_path}")
    print(f" Total de arquivos:     {file_count}")
    print(f" Tamanho descompactado: {uncompressed_mb:.2f} MB")
    print(f" Tamanho compactado:    {zip_size_mb:.2f} MB")
    print(f" Tempo de execucao:     {elapsed:.2f}s")
    print("=" * 60)

    return portable_dir, zip_path, zip_size_mb

def main():
    parser = argparse.ArgumentParser(description="Empacota a distribuição portátil do Jekyll Writer.")
    parser.add_argument("--ruby-dir", default=None, help="Caminho para instalação do Ruby (padrão: C:\\Ruby40-x64)")
    parser.add_argument("--cloudflared", default=None, help="Caminho para o executável cloudflared.exe")
    parser.add_argument("--rebuild-exe", action="store_true", help="Força a recompilação do executável PyInstaller")
    args = parser.parse_args()

    project_root = os.path.abspath(os.path.dirname(__file__))

    ruby_dir = find_ruby_dir(args.ruby_dir) if args.ruby_dir else find_ruby_dir()
    cloudflared_path = find_cloudflared(args.cloudflared) if args.cloudflared else find_cloudflared()

    print(f"Ruby source:        {ruby_dir}")
    print(f"Cloudflared source: {cloudflared_path}")

    build_portable_package(
        project_root=project_root,
        ruby_dir=ruby_dir,
        cloudflared_path=cloudflared_path,
        force_rebuild_exe=args.rebuild_exe
    )

if __name__ == "__main__":
    main()
