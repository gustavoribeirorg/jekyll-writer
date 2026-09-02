# ✍️ Jekyll Writer (Desktop & Web)

Sistema para redação, gerenciamento e publicação automatizada em blogs Jekyll no Windows, disponível como aplicativo Desktop nativo ou Servidor Web autohospedado para acesso local e remoto.

---

## 🚀 Opções de Execução

### 1. Standalone Desktop (Interface Nativa Tkinter)
Ideal para uso direto e exclusivo na máquina local com zero dependências externas:
- **Executável compilado**: Abra a pasta `dist/` e dê um duplo clique em [`JekyllWriter.exe`](dist/JekyllWriter.exe).
- **Script rápido**: Dê um duplo clique em [`run.bat`](run.bat) na raiz do projeto.
- **Via terminal**: `python main.py`

### 2. Versão Web Autohospedada (FastAPI + Modern UI)
Ideal para redigir a partir de qualquer dispositivo (desktop, notebook, tablet ou smartphone) com interface responsiva dark/light mode e sincronização instantânea:
- **Script rápido**: Dê um duplo clique em [`run_web.bat`](run_web.bat) (inicia o servidor e abre o navegador automaticamente).
- **Via terminal**: `python web.py` (ou `uvicorn web:app --host 0.0.0.0 --port 8000`)

---

## 🌐 Acesso à Versão Web

O servidor web é executado por padrão em `0.0.0.0:8000`, permitindo conexões locais, na rede interna e através de túneis seguros:

### 🏠 1. Acesso Local (Mesmo Computador)
- Abra o navegador e acesse: **`http://localhost:8000`** (ou `http://127.0.0.1:8000`).

### 📱 2. Acesso em Rede Local (Wi-Fi / LAN)
- Descubra o endereço IP local do seu computador Windows (via `ipconfig`, ex: `192.168.1.100`).
- No seu tablet, smartphone ou outro computador conectado ao mesmo Wi-Fi, acesse:
  **`http://<IP-DO-COMPUTADOR>:8000`** (ex: `http://192.168.1.100:8000`).
- Permite escrever e publicar seus posts diretamente do celular ou tablet.

### ☁️ 3. Acesso Externo Seguro via Cloudflare Tunnel
Você pode expor sua instância do Jekyll Writer Web para a internet de forma segura, sem abrir portas no roteador (sem port forwarding):
1. **Configuração do Túnel**:
   No Cloudflare Zero Trust / Cloudflare Tunnel (`cloudflared`), crie um túnel ou adicione um Public Hostname:
   - **Subdomínio**: ex: `editor.seudominio.net`
   - **Tipo de Serviço**: `HTTP`
   - **URL de Destino**: `localhost:8000` (ou `127.0.0.1:8000`)
2. **Streaming em Tempo Real (SSE)**:
   - Os logs do processo de build e publicação utilizam Server-Sent Events (SSE) com cabeçalhos anti-buffering (`X-Accel-Buffering: no` e `Cache-Control: no-cache`), garantindo que o progresso linha por linha seja exibido fluidamente mesmo através do Cloudflare Proxy / Tunnel.
3. **Segurança Zero-Persistence**:
   - **Zero gravação de senhas em disco**: As senhas SSH são fornecidas em tempo de execução na requisição e trafegadas somente em memória durante a sessão de upload, nunca sendo salvas no arquivo `config.json` ou em logs.
   - Recomenda-se habilitar autenticação via Cloudflare Access (One-Time PIN por e-mail ou OAuth) no painel do Cloudflare Zero Trust para proteger o subdomínio.

---

## ✨ Funcionalidades

- 📄 **Front Matter Automático**: Cria cabeçalhos padronizados com fuso horário local (`date: YYYY-MM-DD HH:MM -0300`), título, categorias, tags, autor e meta descrição.
- 💾 **Gerenciamento e Salvamento Inteligente (`YYYY-MM-DD-TITULO.md`)**:
  - Salva e lê diretamente da pasta `_posts/` ou `posts/` configurada.
  - Na versão Web: lista lateral com barra de busca para carregar, editar ou criar novos posts instantaneamente.
- 🖼️ **Inserção e Otimização de Imagens WebP**:
  - Upload/cópia automática para `assets/imagens/` com geração de HTML `<figure>` padronizado apontando para `.webp`.
  - Motor embutido de compressão e conversão WebP executado antes de cada publicação.
- ⚙️ **Painel de Configurações**:
  - Pasta raiz do blog Jekyll local.
  - Servidor SSH (host, usuário, porta e destino remoto, ex: `~/blog/_site`).
  - Suporte a conexões diretas ou via `cloudflared access ssh` configurado no Windows OpenSSH.
  - Botão para testar conexão SSH com feedback imediato.
  - Limpeza do cache de sincronização de arquivos.
- 🚀 **Pipeline de Publicação Automatizado ("Enviar Publicação")**:
  1. Salva automaticamente o post atual.
  2. Otimiza novas imagens do blog para formato WebP.
  3. Executa a compilação do Jekyll (`bundle exec jekyll build`) utilizando o ambiente de build Ruby/Jekyll configurado ou binários portáteis embutidos.
  4. Sincroniza via SFTP apenas arquivos novos ou alterados em `_site/` com cache inteligente SHA-256.
- 📋 **Gaveta de Logs em Tempo Real**: Terminal retrátil no rodapé exibindo a saída detalhada do pipeline em tempo real (SSE na versão Web).

---

## 🔌 Endpoints da API REST (Versão Web)

A versão web expõe uma API REST moderna e documentada automaticamente via Swagger UI (`http://localhost:8000/docs`):

| Método | Endpoint | Descrição |
|---|---|---|
| `GET` | `/api/config` | Retorna as configurações atuais (sem expor senhas). |
| `POST` | `/api/config` | Salva as configurações locais em `config.json`. |
| `POST` | `/api/config/clear-cache` | Limpa o arquivo de cache de sincronização SFTP. |
| `GET` | `/api/posts` | Lista todos os posts markdown encontrados na pasta `_posts/`. |
| `GET` | `/api/posts/{filename}` | Carrega o conteúdo bruto e front matter de um post específico. |
| `POST` | `/api/posts` | Salva um post (novo ou existente), gerando o filename canônico. |
| `GET` | `/api/template` | Retorna o template inicial de Front Matter com data e fuso atualizados. |
| `POST` | `/api/images/upload` | Faz upload de uma imagem para `assets/imagens/` e retorna o snippet `<figure>`. |
| `POST` | `/api/publish/test-ssh` | Valida credenciais e conectividade com o servidor SSH remoto. |
| `POST` | `/api/publish` | Executa o pipeline de build e deploy com streaming SSE dos logs em tempo real. |

---

## 🛠️ Recompilação do Executável Desktop

Se você fizer modificações no código-fonte desktop e quiser gerar um novo `.exe`, basta executar:
[`build_exe.bat`](build_exe.bat) (ou `python -m PyInstaller jekyll_writer.spec`).
O executável standalone será gerado em `dist/JekyllWriter.exe`.

---

## 🧪 Testes Automatizados

Para rodar a suíte completa de testes unitários:
```powershell
python -m pytest -v
```
