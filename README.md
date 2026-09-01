# ✍️ Jekyll Writer Desktop (Windows)

Sistema desktop nativo e autônomo (*standalone*) para redação e publicação automatizada em blogs Jekyll no Windows.

---

## 🚀 Como Executar

### Opção 1: Executável Standalone (Recomendado)
Você pode rodar diretamente o executável independente (não requer Python nem dependências instaladas):
- Abra a pasta `dist\` e dê um duplo clique em [`JekyllWriter.exe`](file:///c:/Users/Gustavo%20Ribeiro.DESKTOP-MQL7L2R/Desktop/jekyll-writer/dist/JekyllWriter.exe).

### Opção 2: Via Script Rápido
- Dê um duplo clique em [`run.bat`](file:///c:/Users/Gustavo%20Ribeiro.DESKTOP-MQL7L2R/Desktop/jekyll-writer/run.bat) na raiz do projeto.

### Opção 3: Via Linha de Comando
```powershell
python main.py
```

---

## ✨ Funcionalidades

- 📄 **Front Matter Automático**: Ao iniciar ou clicar em *Novo*, cria o cabeçalho completo com `date` no formato exato com fuso horário local (`2026-09-01 12:30 -0300`) e posiciona o cursor em `title: `.
- 💾 **Salvamento Inteligente (`YYYY-MM-DD-TITULO.md`)**: Gera o nome do arquivo limpo e padronizado e salva diretamente na pasta `_posts/` ou `posts/` do seu blog Jekyll.
- 🖼️ **Inserção de Imagens e Extensão `.webp`**:
  - Copia automaticamente a imagem selecionada para `assets/imagens/` (ou para `assets/fotolog/` se a categoria for `Fotolog`).
  - Insere o bloco `<figure>` padronizado sempre apontando para a extensão `.webp`.
- ⚙️ **Painel de Configurações**:
  - Seleção da pasta raiz do seu blog Jekyll no Windows.
  - Servidor SSH (host), usuário, porta e senha (suporte transparente a conexões diretas e Cloudflare Tunnel).
  - Pasta remota de destino no servidor (ex: `~/blog/_site`).
  - Comando de build do Jekyll (`bundle exec jekyll build`).
  - Botão para testar a conexão SSH antes de enviar.
- 🚀 **Pipeline de Publicação Automatizado ("Enviar Publicação")**:
  1. Salva automaticamente o post atual.
  2. Se a categoria for `Fotolog`, executa o motor embutido de Fotolog.
  3. Se houver imagens no post, executa o motor embutido de otimização de imagens WebP.
  4. Executa `bundle exec jekyll build` na pasta do blog.
  5. Sincroniza apenas os arquivos novos/alterados em `_site/` para o servidor remoto via SSH/SFTP com cache inteligente.
- 📋 **Gaveta de Logs em Tempo Real**: Console retrátil com exibição linha por linha do progresso dos scripts, build do Jekyll e upload de arquivos.

---

## 🛠️ Como Recompilar o Executável

Se você fizer modificações no código-fonte e quiser gerar um novo `.exe`, basta dar um duplo clique em:
[`build_exe.bat`](file:///c:/Users/Gustavo%20Ribeiro.DESKTOP-MQL7L2R/Desktop/jekyll-writer/build_exe.bat).
O novo executável será gerado em `dist/JekyllWriter.exe`.

---

## 🧪 Testes Automatizados

Para rodar a suíte completa de testes unitários:
```powershell
python -m pytest -v
```
