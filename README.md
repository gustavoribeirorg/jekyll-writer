# ✍️ Jekyll Writer Web (Self-Hosted)

Sistema web autohospedado, moderno e responsivo para redação, gerenciamento e publicação automatizada em blogs Jekyll.

Permite redigir seus textos, gerenciar imagens e publicar seu blog a partir de qualquer dispositivo (computador, notebook, tablet ou smartphone) na sua rede local ou remotamente via Cloudflare Tunnel.

---

## 🚀 Como Executar

### 1. Pré-requisitos
Instale as dependências Python necessárias:
```powershell
pip install -r requirements.txt
```

### 2. Inicialização Rápida
- **No Windows (1 clique)**: Dê um duplo clique em [`run.bat`](run.bat) (inicia o servidor e abre o navegador automaticamente).
- **Via Terminal**:
  ```powershell
  python main.py
  ```
  *(O servidor iniciará escutando em `0.0.0.0:8000`)*.

---

## 🌐 Como Acessar

### 🏠 1. Acesso Local (No mesmo computador)
- Abra o navegador em: **`http://localhost:8000`**

### 📱 2. Acesso em Rede Local (Wi-Fi / Celular / Tablet)
1. Descubra o IP local do computador onde o servidor está rodando (via `ipconfig`, ex: `192.168.1.50`).
2. No seu smartphone ou tablet conectado ao mesmo Wi-Fi, acesse:
   **`http://192.168.1.50:8000`**
3. Você poderá redigir, formatar e publicar diretamente do celular com interface responsiva!

### ☁️ 3. Acesso Externo via Cloudflare Tunnel
Você pode expor seu Jekyll Writer com HTTPS gratuito e sem abrir portas no roteador:
1. No painel do **Cloudflare Zero Trust** (Tunnels), aponte um subdomínio para seu servidor local:
   - **Hostname**: `editor.seudominio.net`
   - **Service**: `HTTP -> localhost:8000`
2. **Streaming em Tempo Real (SSE)**: O servidor já envia cabeçalhos anti-buffering (`X-Accel-Buffering: no` e `Cache-Control: no-cache`), garantindo que os logs do Jekyll e do envio SFTP apareçam linha a linha em tempo real mesmo através do proxy da Cloudflare.
3. **Segurança Zero-Persistence**: Nenhuma senha SSH é salva no disco ou no `config.json`. A senha é solicitada no modal de envio e trafega exclusivamente na memória durante a publicação.

---

## ✨ Funcionalidades

- 📄 **Barra Lateral de Posts (Sidebar)**: Lista todos os artigos existentes da pasta `_posts/`, ordenados por data decrescente, com campo de busca em tempo real e botão de recolher/expandir.
- ✍️ **Editor em Área de Texto**: Leve, monoespaçado, com atalhos de teclado (`Ctrl+S`) e barra de formatação (Negrito, Itálico, Títulos H2/H3, Lista, Links).
- 🖼️ **Upload e Otimização Direta de Fotos (`🖼️ Imagem`)**:
  - Selecione imagens pelo navegador;
  - São salvas automaticamente em `assets/imagens/`;
  - Convertidas para `.webp`;
  - Bloco `<figure>` é inserido na posição exata do cursor.
- 🚀 **Pipeline de Publicação Automatizado ("Enviar Publicação")**:
  1. Salva automaticamente o post atual.
  2. Otimiza imagens para formato WebP.
  3. Compila o blog Jekyll (`bundle exec jekyll build`).
  4. Sincroniza via SFTP apenas arquivos novos ou alterados em `_site/` com cache inteligente MD5.
- 📋 **Terminal de Logs em Tempo Real**: Gaveta retrátil no rodapé exibindo a saída do Jekyll e da transferência via Server-Sent Events (SSE).
- ⚙️ **Configurações e Limpeza de Cache**: Ajuste o caminho da pasta do blog, comando Jekyll, usuário SSH e limpe a memória de sincronização a qualquer momento.

---

## 🔌 API REST Documentada

A documentação interativa da API (Swagger UI) fica disponível automaticamente em:
👉 **`http://localhost:8000/docs`**

| Método | Endpoint | Descrição |
|---|---|---|
| `GET` | `/` | Interface web principal |
| `GET` | `/api/posts` | Lista posts de `_posts/` ordenados por data |
| `GET` | `/api/posts/{filename}` | Carrega conteúdo de um post |
| `POST` | `/api/posts` | Salva post (novo ou existente) |
| `GET` | `/api/posts/template/new` | Gera modelo com front matter e fuso horário local |
| `POST` | `/api/images/upload` | Upload de fotos, conversão para WebP e tag `<figure>` |
| `POST` | `/api/ssh/test` | Valida credenciais e conectividade SSH sem salvar senha |
| `POST` | `/api/publish` | Executa build e deploy com streaming SSE de logs |
| `GET` | `/api/config` | Consulta configurações locais (sem senhas) |
| `POST` | `/api/config` | Salva preferências locais |
| `POST` | `/api/config/clear-cache` | Limpa o arquivo de cache de sincronização |

---

## 🧪 Testes Automatizados

Para rodar a suíte completa de testes unitários:
```powershell
python -m pytest -v
```
