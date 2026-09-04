# ✍️ Jekyll Writer Web

Editor web autohospedado, moderno e leve para redação, gerenciamento e publicação automatizada de blogs [Jekyll](https://jekyllrb.com/).

> 🤖 **Desenvolvido com Inteligência Artificial**: Concebido, arquitetado e testado em colaboração com IA (Google DeepMind / Antigravity), utilizando Desenvolvimento Guiado por Testes (TDD), Subagent-Driven Development (SDD) e rigorosa política de segurança e sanitização.

---

## ✨ Funcionalidades

- **Gerenciador de Artigos**: Barra lateral com busca em tempo real de artigos em `_posts/` e geração automática de Front Matter YAML.
- **Editor Markdown**: Área de texto leve, atalhos de formatação rápida, suporte a `Ctrl+S` e dirty state.
- **Otimização de Imagens**: Upload direto com conversão automática para `.webp` e inserção de `<figure>`.
- **Publicação em 1 Clique**: Executa `bundle exec jekyll build` diretamente na pasta `_site/` com streaming de logs em tempo real via Server-Sent Events (SSE).
- **Flexível**: Suporta deploy direto no próprio servidor (Termux / VPS) ou envio remoto via SFTP/SSH.
- **Segurança Zero-Persistence**: Nenhuma credencial ou senha é gravada em disco.

---

## 🚀 Instalação e Execução

### 1. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 2. Iniciar o Servidor
- **Terminal (Linux / macOS / Termux)**:
  ```bash
  python main.py
  ```
- **Windows (1 Clique)**:
  Execute o arquivo [`run.bat`](run.bat).

O servidor iniciará escutando em `http://localhost:8000`.

---

## ⚙️ Configuração Básica

Abra o painel em **⚙️ Configurações**:

1. **Diretório do Jekyll (Root)**: Caminho da pasta do seu blog contendo `_posts/` e `_config.yml` (ex: `/home/usuario/blog` ou `C:\Users\usuario\blog`).
2. **Modo de Publicação**:
   - `⚡ Direto no Servidor (Local)` *(Recomendado)*: Compila o blog diretamente na máquina onde o app roda. Se o seu servidor web já lê a pasta `_site`, a publicação é instantânea e não requer senhas de SSH.
   - `🌐 Servidor Remoto via SSH/SFTP`: Permite enviar os arquivos para outro servidor remoto.

---

## ☁️ Acesso Remoto Seguro (Cloudflare Tunnel + Access)

Para acessar o editor de qualquer aparelho (computador, tablet ou smartphone) sem expor portas no roteador:

1. **Cloudflare Tunnel**: Aponte um Public Hostname HTTP para `localhost:8000` (ex: `editor.seudominio.com`). Os cabeçalhos SSE já possuem otimização anti-buffering (`X-Accel-Buffering: no`).
2. **Cloudflare Access (Zero Trust)**: Ative uma política de acesso no painel da Cloudflare exigindo autenticação por e-mail (PIN de 6 dígitos) ou conta Google para bloquear qualquer acesso não autorizado antes mesmo de atingir seu servidor.

---

## 🧪 Testes Automatizados

O projeto conta com suíte de testes unitários automatizados com 100% de aprovação:

```bash
pytest -v
```

---

## 📄 Licença

Distribuído sob a licença MIT.
