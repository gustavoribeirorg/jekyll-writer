# ✍️ Jekyll Writer Web

> **Sistema web autohospedado, moderno e leve para redação, gerenciamento e publicação automatizada de blogs [Jekyll](https://jekyllrb.com/).**

O **Jekyll Writer Web** foi criado para simplificar todo o ciclo de vida de um blog estático: desde a criação e edição de artigos em Markdown com barra lateral interativa, até o upload e otimização automática de imagens em formato WebP e a compilação/deploy remoto via SSH/SFTP com acompanhamento de logs em tempo real.

---

## 🤖 Projeto Desenvolvido com Inteligência Artificial

Este projeto foi totalmente concebido, arquitetado, codificado e testado em colaboração com **Inteligência Artificial** (Google DeepMind / Antigravity). 

### Como a IA foi utilizada no desenvolvimento:
- **Engenharia Dirigida por Subagentes (SDD)**: O sistema foi dividido em módulos independentes com subagentes especializados atuando como desenvolvedores e revisores de código para cada funcionalidade.
- **Desenvolvimento Guiado por Testes (TDD)**: Antes da escrita de qualquer endpoint ou motor de sincronização, foram criados testes unitários de integração automatizados. O projeto conta com **100% de cobertura nos fluxos críticos (48 testes passando)**.
- **Sanitização e Segurança**: Auditoria contínua de código para garantir política de *Zero-Persistence* de credenciais e remoção de dados sensíveis antes da publicação do repositório.

---

## ⚙️ Como Funciona o Sistema

O Jekyll Writer elimina a necessidade de comandos manuais no terminal, ferramentas de FTP externas (como FileZilla) ou compressores manuais de imagens.

```text
┌─────────────────────────┐
│     Seu Navegador       │  (Desktop, Tablet ou Celular)
│  (Interface Web Vanilla)│
└────────────┬────────────┘
             │ HTTP / Server-Sent Events (SSE)
             ▼
┌─────────────────────────┐
│   FastAPI / Uvicorn     │  (Backend local / Servidor)
└────────────┬────────────┘
             ├─► Gerenciamento de Markdown (_posts/ + Front Matter YAML)
             ├─► Upload & Otimização WebP (Pillow / assets/imagens/)
             ├─► Compilação do Site (bundle exec jekyll build)
             └─► Deploy SFTP Inteligente (Paramiko + Cache MD5 diferencial)
                     │
                     ▼
             ┌─────────────────────────┐
             │ Servidor Web / Hospedagem│
             │   (Nginx, Apache, etc.)  │
             └─────────────────────────┘
```

### Principais Pilares:
1. **Editor & Gerenciador de Artigos**:
   - Barra lateral retrátil que lista todos os posts da pasta `_posts/` ordenados por data.
   - Campo de busca instantânea para encontrar artigos antigos e editá-los.
   - Criação de novos artigos com Front Matter gerado automaticamente no fuso horário correto (`date: YYYY-MM-DD HH:MM -0300`).
   - Editor em área de texto monoespaçada com atalhos de formatação rápida (Negrito, Itálico, Títulos H2/H3, Listas, Links) e atalho `Ctrl+S`.
2. **Motor de Imagens WebP Integrado**:
   - Ao fazer upload de uma imagem pela barra de ferramentas (`🖼️ Imagem`), ela é salva em `assets/imagens/`, convertida e comprimida em `.webp` e inserida no texto formatada como `<figure><img src="..." alt="..." /><figcaption>...</figcaption></figure>`.
3. **Pipeline de Publicação com Streaming em Tempo Real (SSE)**:
   - Compila o Jekyll em segundo plano e sincroniza a pasta `_site/` via SFTP.
   - **Cache MD5 diferencial**: Compara o hash de cada arquivo gerado e transfere apenas o que realmente foi alterado ou criado, tornando o deploy quase instantâneo.
   - **Console Terminal Retrátil**: Exibe os logs da compilação e do upload linha a linha em tempo real via Server-Sent Events (SSE).
4. **Segurança Zero-Persistence**:
   - **A senha do seu servidor SSH NUNCA é salva no disco nem em arquivos de configuração**.
   - As credenciais (host, porta, usuário e senha) são informadas em uma janela modal no momento da publicação, trafegam de forma efêmera e permanecem apenas na memória volátil (RAM) enquanto o upload acontece.

---

## 🚀 Como Instalar

### 1. Pré-requisitos
- **Python 3.10 ou superior** instalado.
- **Ruby e Jekyll** instalados (caso deseje compilar o blog na mesma máquina em que o editor roda).
- Acesso SSH/SFTP ao servidor onde o site Jekyll é hospedado.

### 2. Clonar o Repositório
```bash
git clone https://github.com/seu-usuario/jekyll-writer.git
cd jekyll-writer
```

### 3. Instalar as Dependências Python
```bash
pip install -r requirements.txt
```

---

## 🛠️ Como Iniciar

### No Windows (1 Clique)
Basta dar um duplo clique no arquivo:
👉 **[`run.bat`](run.bat)**

*(O script iniciará o servidor FastAPI e abrirá automaticamente seu navegador em `http://localhost:8000`)*.

### Via Terminal (Qualquer Sistema Operacional)
```bash
python main.py
```
O servidor iniciará escutando em todas as interfaces de rede (`0.0.0.0:8000`).

---

## 🌐 Como Acessar

### 🏠 1. No próprio computador
Abra o navegador e acesse:
```text
http://localhost:8000
```

### 📱 2. Na Rede Local Wi-Fi (Celular ou Tablet)
Você pode usar seu tablet ou smartphone como uma estação de escrita confortável no sofá ou na cama:
1. Descubra o IP local do computador onde o Jekyll Writer está rodando (via `ipconfig` no Windows ou `ifconfig`/`ip a` no Linux/Mac, ex: `192.168.1.50`).
2. No seu celular ou tablet conectado à mesma rede Wi-Fi, abra o navegador e acesse:
   ```text
   http://192.168.1.50:8000
   ```
3. A interface é totalmente responsiva: a barra lateral de posts se recolhe automaticamente em telas menores.

### ☁️ 3. Remotamente via Cloudflare Tunnel
Se você possui um domínio gerenciado na Cloudflare, pode acessar o Jekyll Writer de qualquer lugar do mundo com HTTPS gratuito e sem abrir portas no roteador:
1. No painel do **Cloudflare Zero Trust** > **Networks** > **Tunnels**, crie um túnel ou configure o `cloudflared` localmente:
   ```yaml
   ingress:
     - hostname: editor.seudominio.com
       service: http://localhost:8000
     - service: http_status:404
   ```
2. **Otimização Especial para Cloudflare Tunnel**: O Jekyll Writer Web envia automaticamente os cabeçalhos anti-buffering `X-Accel-Buffering: no` e `Cache-Control: no-cache` nas rotas de Server-Sent Events (SSE). Com isso, o proxy da Cloudflare entrega cada linha do log de compilação e deploy sem retenção ou atraso de buffer.
3. *(Recomendado)*: Ative uma regra de **Cloudflare Access** para exigir login seguro (por exemplo, código PIN enviado para o seu e-mail) antes de acessar o subdomínio.

---

## ⚙️ Como Configurar

Ao abrir o editor pela primeira vez, clique no botão **"⚙️ Configurações"** no topo da página:

| Campo | Exemplo | Descrição |
|---|---|---|
| **Pasta Raiz do Jekyll** | `C:\Users\voce\meu-blog` | Caminho absoluto onde está o código do seu blog (contendo `_config.yml` e `_posts/`). |
| **Comando de Compilação** | `bundle exec jekyll build` | Comando executado para compilar o site. |
| **Destino Remoto no Servidor** | `~/blog/_site` ou `/var/www/site` | Pasta no servidor SSH onde os arquivos compilados do `_site/` devem ser entregues. |
| **Usuário SSH** | `deploy` ou `root` | Usuário padrão de acesso ao servidor. |

Clique em **"Salvar"**. As preferências serão salvas localmente no arquivo `config.json`.

---

## 🚀 Como Publicar um Post

1. Escreva ou edite seu texto no editor.
2. Insira imagens usando o botão **"🖼️ Imagem"** na barra de ferramentas.
3. Quando terminar, clique no botão destacado **"🚀 Enviar Publicação"**:
   - Um modal se abrirá solicitando o **Host do Servidor**, **Porta**, **Usuário** e a **Senha do SSH**.
   - Você pode clicar em **"Testar Conexão SSH"** para verificar se as credenciais estão corretas.
   - Clique em **"Confirmar e Publicar"**.
4. O terminal de logs se abrirá automaticamente na parte inferior, mostrando em tempo real:
   - Salvamento do artigo em `_posts/`;
   - Otimização das imagens para `.webp`;
   - Execução do `bundle exec jekyll build`;
   - Sincronização inteligente dos arquivos via SFTP.

---

## 🔌 Documentação da API REST

A documentação interativa Swagger UI gerada pelo FastAPI está disponível em:
👉 **`http://localhost:8000/docs`**

---

## 🧪 Testes Automatizados

O projeto conta com uma suíte de testes unitários abrangente utilizando `pytest` e o `TestClient` do FastAPI:

```powershell
python -m pytest -v
```

Todos os testes validam isoladamente:
- Persistência e higienização de configurações (`config.json`);
- Extração de front matter, datas e formatação de slug;
- Otimização de imagens WebP;
- Upload e validação de segurança de caminhos;
- Streaming de Server-Sent Events (SSE) e conexões SSH efêmeras.

---

## 📄 Licença

Este projeto está sob a licença MIT. Sinta-se livre para usar, modificar e distribuir.
