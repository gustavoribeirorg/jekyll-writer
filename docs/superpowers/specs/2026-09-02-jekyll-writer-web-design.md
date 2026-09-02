# Especificação de Design: Jekyll Writer Web (Self-Hosted)

**Data:** 2026-09-02  
**Status:** Aprovado  
**Objetivo:** Transformar o Jekyll Writer em uma aplicação web moderna e autohospedada, permitindo escrever, gerenciar imagens e publicar posts no blog Jekyll a partir de qualquer dispositivo conectado à rede local através de um navegador.

---

## 1. Visão Geral e Requisitos

### 1.1 Objetivos
- Executar como serviço web leve em Python (`python -m jekyll_writer.web` ou `python web.py`) utilizando **FastAPI** e **Uvicorn**.
- Interface acessível via navegador em computadores, tablets ou smartphones (`http://localhost:8000` ou IP local).
- Sem autenticação inicial (acesso direto em rede local / localhost).
- Gerenciamento de posts com barra lateral para listar, abrir e criar novos posts a partir da pasta `_posts/` do blog.
- Editor em área de texto com barra de formatação rápida (Negrito, Itálico, Título, Lista, Inserção de Imagem com upload e conversão para WebP).
- Transmissão de logs de compilação e publicação em tempo real usando **Server-Sent Events (SSE)**.
- Painel de configurações no navegador para ajustar caminhos locais, credenciais SSH e limpar cache de sincronização.

### 1.2 Restrições e Compatibilidade
- Manter e reutilizar 100% dos motores de lógica de negócio já existentes:
  - `jekyll_writer/config.py`
  - `jekyll_writer/frontmatter.py`
  - `jekyll_writer/images.py`
  - `jekyll_writer/image_optimizer.py`
  - `jekyll_writer/publisher.py`
- Dependências web mínimas: `fastapi`, `uvicorn`, `python-multipart` (para upload de imagens).
- Frontend limpo em HTML5/CSS3/JavaScript Vanilla, sem dependências pesadas de Node.js/npm.

---

## 2. Arquitetura do Sistema

```text
[ Navegador Web (Cliente) ]
       │
       ▼  HTTP REST & Server-Sent Events (SSE)
┌─────────────────────────────────────────────────────────────┐
│ Backend FastAPI (jekyll_writer/web.py + Uvicorn)            │
│                                                             │
│  ├── Rotas Estáticas:                                       │
│  │   └── /                -> jekyll_writer/static/index.html│
│  │   └── /static/*        -> CSS, JS, Ícones               │
│  │                                                          │
│  ├── API de Posts:                                          │
│  │   ├── GET  /api/posts             (Listar posts)         │
│  │   ├── GET  /api/posts/{filename}  (Carregar post)        │
│  │   └── POST /api/posts             (Salvar post)          │
│  │                                                          │
│  ├── API de Mídia:                                          │
│  │   └── POST /api/images/upload     (Upload + WebP figure) │
│  │                                                          │
│  ├── API de Publicação & SSH:                               │
│  │   ├── GET  /api/publish/stream    (SSE Streaming de Logs)│
│  │   └── POST /api/ssh/test          (Testar conexão SSH)   │
│  │                                                          │
│  └── API de Configurações:                                  │
│      ├── GET  /api/config            (Obter configurações)  │
│      ├── POST /api/config            (Salvar configurações) │
│      └── POST /api/config/clear-cache(Limpar cache de sync) │
└─────────────────────────────────────────────────────────────┘
       │
       ├── Lê / Grava no Blog Jekyll (_posts/, assets/imagens/)
       └── Executa build local (Jekyll) e sincroniza via SSH/SFTP
```

---

## 3. Especificação dos Endpoints REST & SSE

### 3.1 Posts
- **`GET /api/posts`**:
  - Lê a pasta `_posts/` ou `posts/` configurada.
  - Retorna JSON ordenado cronologicamente decrescente:
    ```json
    [
      {
        "filename": "2026-09-01-meu-post.md",
        "title": "Meu Post",
        "date": "2026-09-01 12:30 -0300",
        "categories": "Tecnologia"
      }
    ]
    ```
- **`GET /api/posts/{filename}`**:
  - Retorna o conteúdo bruto do post:
    ```json
    {
      "filename": "2026-09-01-meu-post.md",
      "content": "---\ntitle: Meu Post\n---\nTexto aqui..."
    }
    ```
- **`POST /api/posts`**:
  - Recebe `{ "content": "...", "current_filename": "..." (opcional) }`.
  - Executa `save_post` do módulo `frontmatter`.
  - Retorna `{ "filename": "...", "path": "..." }`.

- **`GET /api/posts/template/new`**:
  - Retorna o modelo padrão com front matter inicial preenchido com a data/hora local atual:
    ```json
    { "template": "---\ntitle: \ndate: 2026-09-02 08:30 -0300\nlayout: post\nexcerpt_separator: <!--more-->\ncategories: \ntags: \n---\n\n" }
    ```

### 3.2 Mídia e Imagens
- **`POST /api/images/upload`**:
  - Recebe arquivo via `multipart/form-data`.
  - Salva em `{jekyll_root}/assets/imagens/{slug}.{ext}`.
  - Executa conversão WebP se Pillow estiver disponível.
  - Retorna o snippet `<figure>` pronto para ser inserido na posição atual do cursor:
    ```json
    {
      "html_snippet": "<figure>\n    <img src=\"/assets/imagens/minha-foto.webp\" alt=\"Minha foto\">\n        <figcaption>Minha foto</figcaption>\n</figure>",
      "filename": "minha-foto.webp"
    }
    ```

### 3.3 Publicação e Streaming de Logs (SSE com Segurança Zero-Persistence)
- **Política de Senhas**: A senha do SSH nunca é gravada em disco (`config.json`). O usuário sempre informa o host/IP, porta, usuário e senha diretamente no momento da ação (modal de publicação ou teste).
- **`POST /api/publish`**:
  - Recebe `{ "ssh_host": "...", "ssh_port": 22, "ssh_user": "...", "ssh_password": "..." }`.
  - Inicia o pipeline de compilação Jekyll e upload SFTP em background com credenciais exclusivamente em memória RAM temporária.
  - Retorna uma chave de sessão ou transmite via **Server-Sent Events** (`text/event-stream`) com cabeçalhos `X-Accel-Buffering: no` e `Cache-Control: no-cache` (otimizado para Cloudflare Tunnel):
    ```text
    data: {"level": "info", "message": "🔨 Compilando blog Jekyll..."}

    data: {"level": "info", "message": "$ bundle exec jekyll build"}

    data: {"level": "success", "message": "=== PUBLICAÇÃO ENVIADA COM SUCESSO! ==="}

    data: {"event": "done", "success": true}
    ```

### 3.4 Conexão SSH & Configurações
- **`POST /api/ssh/test`**:
  - Recebe `{ "ssh_host": "...", "ssh_port": 22, "ssh_user": "...", "ssh_password": "..." }`.
  - Testa conexão SSH com os dados informados via `PublisherEngine.test_ssh_connection`.
  - Retorna `{ "success": true, "message": "Conexão estabelecida com sucesso!" }` ou erro.
- **`GET /api/config`**:
  - Retorna campos gerais persistentes (`jekyll_root`, `jekyll_command`, `ssh_remote_path`, `ssh_user`). Nunca retorna ou armazena senhas.
- **`POST /api/config`**:
  - Atualiza e persiste as preferências gerais em `config.json` (sem campos de senha).
- **`POST /api/config/clear-cache`**:
  - Remove `.jekyll_writer_cache.json` chamando `PublisherEngine.clear_sync_cache`.

---

## 4. Interface Web do Usuário (Frontend)

### 4.1 Estrutura Visual
1. **Cabeçalho Superior**:
   - Logotipo e título: ✍️ **Jekyll Writer**.
   - Indicador de status de salvamento (Salvo / Alterações pendentes).
   - Botão **+ Novo Post**.
   - Botão **Salvar** (com atalho `Ctrl+S`).
   - Botão **⚙️ Configurações**.
   - Botão de destaque **🚀 Enviar Publicação**.
2. **Barra Lateral Retrátil (Sidebar)**:
   - Campo de busca para filtrar posts por título/data.
   - Lista de posts existentes em `_posts/` com data e título.
   - Botão para colapsar/expandir a barra lateral (útil em telas pequenas/smartphones).
3. **Barra de Ferramentas de Formatação (Toolbar)**:
   - `B` (Negrito `**texto**`), `I` (Itálico `*texto*`), `H2` (`## Título`), `H3` (`### Subtítulo`), `Lista` (`- Item`), `Link` (`[texto](url)`).
   - `🖼️ Imagem`: abre seletor de arquivos do navegador, faz upload assíncrono para o servidor e insere o bloco `<figure>` na posição do cursor.
4. **Área do Editor (Textarea)**:
   - Campo de texto limpo, fonte monoespaçada legível, foco automático.
5. **Console de Logs Retrátil (Terminal Drawer)**:
   - Localizado no rodapé da página.
   - Exibe timestamps e cores (`info` azul, `success` verde, `warning` amarelo, `error` vermelho).
   - Rola automaticamente para a última linha durante a compilação e publicação.
6. **Modal de Configurações**:
   - Pasta raiz do Jekyll, comando de build, host SSH, porta, usuário, senha, pasta remota.
   - Botão "Testar SSH" e "Limpar Cache".

---

## 5. Estratégia de Testes

- Testes de API automatizados com `pytest` e `fastapi.testclient.TestClient`:
  - Listagem, leitura e gravação de posts.
  - Upload de imagem e geração de `<figure>`.
  - Salvamento de configurações e limpeza de cache.
  - Streaming SSE de logs durante publicação simulada.
- Verificação de compatibilidade com os testes existentes (31 testes do core continuam passando).
