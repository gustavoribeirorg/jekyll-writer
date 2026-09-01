# Especificação Técnica: Jekyll Writer Desktop (Windows)

## 1. Visão Geral e Objetivos

O **Jekyll Writer** é um aplicativo desktop nativo e autônomo (*standalone*) para Windows, projetado para simplificar a escrita, organização de imagens, compilação e publicação automatizada de posts para blogs baseados em **Jekyll**.

O aplicativo resolve as seguintes dores do fluxo de trabalho:
1. Elimina a necessidade de criar manualmente o arquivo Markdown e o Front Matter com data e fuso horário.
2. Formata automaticamente a inserção de imagens no formato padrão `<figure>` com extensão `.webp`.
3. Copia automaticamente as fotos selecionadas para as pastas corretas (`assets/imagens/` ou `assets/fotolog/` no caso da categoria Fotolog).
4. Executa em sequência e em segundo plano (sem travar a tela):
   - Scripts de otimização de imagem (`scripts/otimizar_imagens.py`) e atualização de álbum (`scripts/atualizar_fotolog.py`);
   - Compilação local com `bundle exec jekyll build`;
   - Envio dos arquivos gerados na pasta `_site/` para o servidor remoto via SSH/SFTP com autenticação direta por senha/usuário.
5. Apresenta um console/gaveta de logs em tempo real para monitoramento do processo.

---

## 2. Arquitetura do Sistema

- **Linguagem & Runtime**: Python 3.10+
- **Interface Gráfica (GUI)**: `customtkinter` (interface moderna, cantos arredondados, suporte nativo a temas Dark/Light do Windows).
- **Concorrência & Responsividade**: Módulo `threading` para execução assíncrona do pipeline de publicação (garantindo que a UI permaneça responsiva durante build e uploads).
- **Transferência Remota**: `paramiko` para conexão SSH e sincronização SFTP recursiva de alta velocidade, suportando autenticação direta por senha/chave sem depender de binários externos do Windows.
- **Execução de Processos**: `subprocess.Popen` com streaming em tempo real de `stdout` e `stderr` para o console de logs.
- **Persistência de Dados**: Arquivo `config.json` no diretório do aplicativo para armazenar caminhos locais e credenciais do servidor.
- **Distribuição Standalone**: Empacotamento em executável único `.exe` via `PyInstaller`.

---

## 3. Design da Interface do Usuário (UI)

### 3.1 Janela Principal
- **Dimensões Padrão**: 1000x700px (redimensionável, com lembrança de estado).
- **Barra de Ferramentas Superior (Toolbar)**:
  - Botões de Markdown:
    - **B** (`**negrito**`)
    - *I* (`*itálico*`)
    - **H2** (`## Título`)
    - **H3** (`### Subtítulo`)
    - **Link** (`[texto](url)`)
    - **Quote** (`> citação`)
    - **Code** (`` `código` `` / bloco de código)
    - **Lista** (`- item`)
    - **Mais** (`<!--more-->`)
  - Ações Rápidas:
    - **🖼️ Inserir Imagem** (Abre seletor de arquivo `.png`, `.jpg`, `.webp` etc.)
    - **📄 Novo Post** (Gera novo template com data/hora atual)
    - **💾 Salvar Post** (`Ctrl+S`)
    - **🚀 Enviar Publicação** (Inicia o pipeline)
    - **⚙️ Configurações** (Abre modal de configurações)
- **Área Central (Editor Focado)**:
  - `CTkTextbox` monoespaçado ou com tipografia limpa para escrita fluida.
  - Suporte completo a atalhos: `Ctrl+S` (Salvar), `Ctrl+B` (Negrito), `Ctrl+I` (Itálico), `Ctrl+Z` (Desfazer), `Ctrl+Y` (Refazer).
- **Barra de Rodapé & Gaveta de Logs**:
  - Barra de status com arquivo aberto atual, contador de palavras e indicador de status.
  - Painel expansível/recolhível com terminal escuro e fonte de console para exibição de logs linha por linha com timestamps.

### 3.2 Modal de Configurações
- **Pasta Raiz do Jekyll**: Campo de texto com botão "Procurar..." (valida a existência de `_posts/` ou `posts/`).
- **Servidor SSH (Host)**: Ex: `ssh.exemplo.com`
- **Porta SSH**: Ex: `22`
- **Usuário SSH**: Ex: `usuario`
- **Senha SSH**: Campo de senha com alternância de visibilidade.
- **Pasta Remota de Destino**: Ex: `~/meu-site/_site`
- **Comando Jekyll**: Ex: `bundle exec jekyll build`
- **Ações**: Botão "Testar Conexão SSH" e "Salvar".

---

## 4. Fluxo de Edição e Front Matter

### 4.1 Criação de Novo Post
Ao iniciar ou clicar em "Novo Post", o editor preenche:
```yaml
---
title: 
date: YYYY-MM-DD HH:MM -0300
layout: post
excerpt_separator: <!--more-->
categories: 
tags: 
---

```
O cursor é posicionado automaticamente no final da linha `title: `.

### 4.2 Regras de Salvamento do Arquivo
1. O título é extraído do front matter (`title: <texto>`).
2. O nome do arquivo gerado segue: `YYYY-MM-DD-<slug>.md`.
   - `YYYY-MM-DD` é obtido da data do post (ou da data atual se vazio).
   - `<slug>` é gerado convertendo caracteres acentuados, minúsculas e substituindo espaços por hífens (ex: `Servidor Rodando` vira `servidor-rodando`).
3. O arquivo é gravado na pasta `_posts/` (ou `posts/`, detectada na raiz do blog Jekyll configurado).

### 4.3 Inserção de Imagens
1. O usuário clica em "🖼️ Inserir Imagem".
2. O sistema verifica a categoria no front matter atual (`categories:`):
   - **Se categoria contiver `Fotolog`**:
     - O arquivo de imagem é copiado para `{jekyll_root}/assets/fotolog/{nome_slug}.{ext}`.
     - O caminho no HTML gerado aponta para `/assets/fotolog/{nome_slug}.webp`.
   - **Caso contrário**:
     - O arquivo de imagem é copiado para `{jekyll_root}/assets/imagens/{nome_slug}.{ext}`.
     - O caminho no HTML gerado aponta para `/assets/imagens/{nome_slug}.webp`.
3. É inserido no local do cursor o bloco:
   ```html
   <figure>
       <img src="/assets/imagens/nome-da-imagem.webp" alt="Nome da imagem">
           <figcaption>Nome da imagem</figcaption>
   </figure>
   ```
4. A extensão é **sempre** alterada para `.webp` na tag `<img>`.

---

## 5. Pipeline Automatizado de Publicação ("Enviar Publicação")

Ao acionar "🚀 Enviar Publicação":
```
[1. Salvar Post]
       │
       ▼
[2. Checagem de Categoria & Imagens]
       ├── Se Fotolog: Executa `python scripts/atualizar_fotolog.py`
       └── Se houver Imagens: Executa `python scripts/otimizar_imagens.py`
       │
       ▼
[3. Compilação Local Jekyll]
       └── Executa `bundle exec jekyll build` na pasta raiz do blog
       │
       ▼
[4. Transferência SSH/SFTP para o Servidor]
       └── Sincroniza recursivamente `_site/` para `~/meu-site/_site`
       │
       ▼
[5. Notificação de Sucesso]
```

### Detalhamento das Etapas:
1. **Scripts Python**:
   - Rodados a partir da pasta raiz do Jekyll via `subprocess.Popen(..., cwd=jekyll_root)`.
   - `stdout` e `stderr` são redirecionados em tempo real para a gaveta de logs.
2. **Build do Jekyll**:
   - Executa `bundle exec jekyll build` localmente na pasta raiz do blog.
   - Em caso de erro de compilação, o processo para imediatamente e notifica o usuário na interface com a mensagem de erro do Jekyll.
3. **Sincronização SFTP**:
   - Conexão via `paramiko.SSHClient` usando as credenciais salvas.
   - Sincronização inteligente: envia recursivamente arquivos novos ou com tamanho/timestamp alterados da pasta local `_site/` para a pasta remota configurada.
   - Atualiza a barra de progresso e loga cada arquivo transferido.

---

## 6. Empacotamento e Execução Standalone

- O código fonte será estruturado de forma modular em `jekyll-writer/`.
- Dependências gerenciadas via `requirements.txt` (`customtkinter`, `paramiko`, `pyyaml`, `pillow`, etc.).
- Script de compilação `build_exe.bat` utilizando `pyinstaller --onefile --windowed` para gerar um `.exe` autônomo pronto para uso no Windows sem necessidade de Python ou bibliotecas pré-instaladas.
