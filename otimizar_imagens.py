#!/usr/bin/env python3
import os
import subprocess
import re
import unicodedata

from PIL import Image, ImageOps

# Caminhos do projeto
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
assets_dir = os.path.join(project_dir, "assets")
gitignore_path = os.path.join(project_dir, ".gitignore")

def normalize_name(name):
    # Remove acentos
    name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('utf-8')
    # Substitui espacos e caracteres estranhos por underline
    name = re.sub(r'[^a-zA-Z0-9_.-]', '_', name)
    # Remove underlines consecutivos
    name = re.sub(r'_+', '_', name)
    return name

extensions = {".heic", ".jpg", ".jpeg", ".png"}

images_to_process = []
for root, dirs, files in os.walk(assets_dir):
    for f in files:
        ext = os.path.splitext(f)[1].lower()
        if ext in extensions:
            images_to_process.append(os.path.join(root, f))

# Arquivos a serem atualizados
files_to_update = []
for root, dirs, files in os.walk(project_dir):
    parts = root.split(os.sep)
    if ".git" in parts or "_site" in parts or ".ruby-lsp" in parts or "vendor" in parts or "scripts" in parts:
        continue
    for f in files:
        ext = os.path.splitext(f)[1].lower()
        if ext in {".md", ".html", ".css", ".yml", ".txt"}:
            files_to_update.append(os.path.join(root, f))

# Lendo o gitignore atual
try:
    with open(gitignore_path, "r", encoding="utf-8") as f:
        gitignore_content = f.read()
except FileNotFoundError:
    gitignore_content = ""

new_gitignore_entries = []
count_converted = 0

print("Buscando imagens novas...")

for img_path in images_to_process:
    base_name = os.path.basename(img_path)
    
    # 1. Normalizar o nome base para evitar acentos e espacos
    good_base_name = normalize_name(base_name)
    name_no_ext, ext = os.path.splitext(good_base_name)
    webp_name = name_no_ext + ".webp"
    webp_path = os.path.join(os.path.dirname(img_path), webp_name)
    
    # Adicionar o original ao gitignore se nao estiver
    rel_path = os.path.relpath(img_path, project_dir).replace("\\", "/")
    if rel_path not in gitignore_content and rel_path not in new_gitignore_entries:
        new_gitignore_entries.append(rel_path)
    
    # Verificar se ja existe uma versao webp processada
    if os.path.exists(webp_path):
        continue
        
    print(f"Convertendo imagem nova: {base_name} -> {webp_name}...")
    
    try:
        with Image.open(img_path) as img:
            img = ImageOps.exif_transpose(img)
            if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                img = img.convert("RGBA")
            else:
                img = img.convert("RGB")
            
            img.save(webp_path, "WEBP", quality=80)
            
            # Validar tamanho e forcar qualidade menor se passar de 1MB (1048576 bytes)
            if os.path.exists(webp_path) and os.path.getsize(webp_path) > 1048576:
                img.save(webp_path, "WEBP", quality=50)
    except Exception as e:
        print(f"Erro ao converter {img_path}: {e}")
        continue
    
    # Atualizar referencias nos arquivos
    for filepath in files_to_update:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            new_content = content
            
            # Substituir nome original apenas se nao for seguido de .webp
            pattern = re.escape(base_name) + r'(?!\.webp)'
            new_content = re.sub(pattern, webp_name, new_content)
            
            # Substituir espacos codificados caso o usuario tenha arrastado a imagem (URL)
            url_encoded_base = base_name.replace(" ", "%20")
            if url_encoded_base != base_name:
                pattern_encoded = re.escape(url_encoded_base) + r'(?!\.webp)'
                new_content = re.sub(pattern_encoded, webp_name, new_content)
            
            # Garantir que src="assets/imagens/" tenha barra inicial /assets/imagens/
            new_content = new_content.replace('src="assets/imagens/', 'src="/assets/imagens/')
            # Corrigir qualquer eventual .webp.webp
            new_content = new_content.replace('.webp.webp', '.webp')
                
            if new_content != content:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f"  -> Links atualizados em {os.path.relpath(filepath, project_dir)}")
        except Exception as e:
            pass

    count_converted += 1

if new_gitignore_entries:
    with open(gitignore_path, "a", encoding="utf-8") as f:
        f.write("\n# Imagens originais auto-geradas pelo script\n")
        for entry in new_gitignore_entries:
            f.write(f"{entry}\n")
    print(f"\n{len(new_gitignore_entries)} novos arquivos originais adicionados ao .gitignore")

if count_converted == 0:
    print("\nNenhuma imagem nova precisou de conversao. Todas ja possuem versao em .webp!")
else:
    print(f"\nProcesso concluido! {count_converted} imagens novas convertidas para .webp.")
