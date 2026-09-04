/**
 * Jekyll Writer - Frontend Application
 * Single Page Interface for Jekyll Post Management & Publishing
 */

(function () {
  'use strict';

  // --- State ---
  const state = {
    currentFilename: null,
    isDirty: false,
    posts: [],
    config: {},
    isPublishing: false,
  };

  // --- DOM Elements ---
  const el = {
    // Header & Navigation
    btnToggleSidebar: document.getElementById('btnToggleSidebar'),
    sidebar: document.getElementById('sidebar'),
    saveStatus: document.getElementById('saveStatus'),
    btnNewPost: document.getElementById('btnNewPost'),
    btnSavePost: document.getElementById('btnSavePost'),
    btnOpenSettings: document.getElementById('btnOpenSettings'),
    btnOpenPublish: document.getElementById('btnOpenPublish'),

    // Sidebar
    postSearch: document.getElementById('postSearch'),
    postList: document.getElementById('postList'),

    // Editor & Toolbar
    postEditor: document.getElementById('postEditor'),
    postCustomFilename: document.getElementById('postCustomFilename'),
    btnAutoFilename: document.getElementById('btnAutoFilename'),
    btnBold: document.getElementById('btnBold'),
    btnItalic: document.getElementById('btnItalic'),
    btnUnderline: document.getElementById('btnUnderline'),
    btnStrike: document.getElementById('btnStrike'),
    btnInlineCode: document.getElementById('btnInlineCode'),
    btnH2: document.getElementById('btnH2'),
    btnH3: document.getElementById('btnH3'),
    btnBlockquote: document.getElementById('btnBlockquote'),
    btnList: document.getElementById('btnList'),
    btnOrderedList: document.getElementById('btnOrderedList'),
    btnLink: document.getElementById('btnLink'),
    btnInternalLink: document.getElementById('btnInternalLink'),
    imageFileInput: document.getElementById('imageFileInput'),

    // Status Bar
    currentFilenameDisplay: document.getElementById('currentFilenameDisplay'),
    wordCountDisplay: document.getElementById('wordCountDisplay'),
    btnToggleLogs: document.getElementById('btnToggleLogs'),
    logBadge: document.getElementById('logBadge'),

    // Terminal Log Drawer
    logDrawer: document.getElementById('logDrawer'),
    logOutput: document.getElementById('logOutput'),
    btnClearLogs: document.getElementById('btnClearLogs'),
    btnCloseLogs: document.getElementById('btnCloseLogs'),

    // Settings Modal
    settingsModal: document.getElementById('settingsModal'),
    btnCloseSettings: document.getElementById('btnCloseSettings'),
    btnCloseSettingsX: document.getElementById('btnCloseSettingsX'),
    btnSaveSettings: document.getElementById('btnSaveSettings'),
    btnClearCache: document.getElementById('btnClearCache'),
    clearCacheFeedback: document.getElementById('clearCacheFeedback'),
    cfgJekyllRoot: document.getElementById('cfgJekyllRoot'),
    cfgJekyllRootFeedback: document.getElementById('cfgJekyllRootFeedback'),
    cfgDetectedCandidates: document.getElementById('cfgDetectedCandidates'),
    cfgBuildCommand: document.getElementById('cfgBuildCommand'),
    cfgDeployMode: document.getElementById('cfgDeployMode'),
    sshSettingsFields: document.getElementById('sshSettingsFields'),
    cfgRemotePath: document.getElementById('cfgRemotePath'),
    cfgSshUser: document.getElementById('cfgSshUser'),

    // Confirm Local Publish Modal
    confirmPublishModal: document.getElementById('confirmPublishModal'),
    btnCloseConfirmPublishX: document.getElementById('btnCloseConfirmPublishX'),
    btnCancelConfirmPublish: document.getElementById('btnCancelConfirmPublish'),
    btnExecuteLocalPublish: document.getElementById('btnExecuteLocalPublish'),

    // Publish Modal (SSH)
    publishModal: document.getElementById('publishModal'),
    btnClosePublishX: document.getElementById('btnClosePublishX'),
    btnCancelPublish: document.getElementById('btnCancelPublish'),
    btnConfirmPublish: document.getElementById('btnConfirmPublish'),
    btnTestSsh: document.getElementById('btnTestSsh'),
    sshTestFeedback: document.getElementById('sshTestFeedback'),
    pubSshHost: document.getElementById('pubSshHost'),
    pubSshPort: document.getElementById('pubSshPort'),
    pubSshUser: document.getElementById('pubSshUser'),
    pubSshPassword: document.getElementById('pubSshPassword'),

    // Internal Link Modal
    internalLinkModal: document.getElementById('internalLinkModal'),
    btnCloseInternalLinkX: document.getElementById('btnCloseInternalLinkX'),
    btnCancelInternalLink: document.getElementById('btnCancelInternalLink'),
    btnConfirmInternalLink: document.getElementById('btnConfirmInternalLink'),
    internalLinkText: document.getElementById('internalLinkText'),
    internalLinkSlug: document.getElementById('internalLinkSlug'),
    internalLinkSearch: document.getElementById('internalLinkSearch'),
    internalLinkPostList: document.getElementById('internalLinkPostList'),

    // Toast
    toastContainer: document.getElementById('toastContainer'),
  };

  // --- Utility Functions ---

  function escapeHtml(text) {
    if (!text) return '';
    return String(text)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  function showToast(message, type = 'info', duration = 3500) {
    if (!el.toastContainer) return;
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `<span>${escapeHtml(message)}</span>`;
    el.toastContainer.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      setTimeout(() => toast.remove(), 300);
    }, duration);
  }

  function copyToClipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
      return navigator.clipboard.writeText(text);
    }
    return new Promise((resolve, reject) => {
      try {
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.left = '-9999px';
        textarea.style.top = '-9999px';
        textarea.setAttribute('readonly', '');
        document.body.appendChild(textarea);
        textarea.focus();
        textarea.select();
        const successful = document.execCommand('copy');
        document.body.removeChild(textarea);
        if (successful) {
          resolve();
        } else {
          reject(new Error('Falha ao copiar'));
        }
      } catch (err) {
        reject(err);
      }
    });
  }

  function setDirty(isDirty) {
    state.isDirty = isDirty;
    if (!el.saveStatus) return;

    el.saveStatus.classList.remove('saved', 'dirty', 'saving');
    const textEl = el.saveStatus.querySelector('.status-text');

    if (isDirty) {
      el.saveStatus.classList.add('dirty');
      if (textEl) textEl.textContent = 'Não salvo';
    } else {
      el.saveStatus.classList.add('saved');
      if (textEl) textEl.textContent = 'Salvo';
    }
  }

  function setSaving(isSaving) {
    if (!el.saveStatus) return;
    el.saveStatus.classList.remove('saved', 'dirty', 'saving');
    const textEl = el.saveStatus.querySelector('.status-text');

    if (isSaving) {
      el.saveStatus.classList.add('saving');
      if (textEl) textEl.textContent = 'Salvando...';
    } else {
      setDirty(state.isDirty);
    }
  }

  function updateWordCount() {
    if (!el.postEditor || !el.wordCountDisplay) return;
    const text = el.postEditor.value || '';
    // Strip YAML front matter for word count if present
    let body = text;
    if (text.startsWith('---')) {
      const parts = text.split('---');
      if (parts.length >= 3) {
        body = parts.slice(2).join('---');
      }
    }
    const words = body.trim().match(/\S+/g);
    const count = words ? words.length : 0;
    el.wordCountDisplay.textContent = `${count} ${count === 1 ? 'palavra' : 'palavras'}`;
  }

  function updateFilenameDisplay(filename) {
    if (el.currentFilenameDisplay) {
      el.currentFilenameDisplay.textContent = filename || 'sem-titulo.md';
    }
  }

  function autoGenerateFilenameFromContent() {
    if (!el.postEditor || !el.postCustomFilename) return;
    const content = el.postEditor.value;
    let title = '';
    let date = '';
    const lines = content.split('\n');
    let inFm = false;
    for (const line of lines) {
      const trimmed = line.trim();
      if (trimmed === '---') {
        if (inFm) break;
        inFm = true;
        continue;
      }
      if (inFm) {
        if (trimmed.startsWith('title:')) {
          title = trimmed.replace('title:', '').trim().replace(/^["']|["']$/g, '');
        } else if (trimmed.startsWith('date:')) {
          const match = trimmed.match(/\d{4}-\d{2}-\d{2}/);
          if (match) date = match[0];
        }
      }
    }
    if (!date) {
      const now = new Date();
      const year = now.getFullYear();
      const month = String(now.getMonth() + 1).padStart(2, '0');
      const day = String(now.getDate()).padStart(2, '0');
      date = `${year}-${month}-${day}`;
    }
    const slug = (title || 'sem-titulo')
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .toLowerCase()
      .replace(/[^\w\s-]/g, '')
      .replace(/[\s_-]+/g, '-')
      .replace(/^-+|-+$/g, '') || 'sem-titulo';

    el.postCustomFilename.value = `${date}-${slug}.md`;
    setDirty(true);
    showToast('Nome de arquivo gerado a partir do título!', 'info');
  }

  // --- API Calls & Core Operations ---

  function updateJekyllRootFeedback(data) {
    if (!el.cfgJekyllRootFeedback) return;
    const raw = (data && (data.jekyll_root || data.configured_root)) || (el.cfgJekyllRoot ? el.cfgJekyllRoot.value.trim() : '');
    if (!raw) {
      el.cfgJekyllRootFeedback.textContent = '';
      el.cfgJekyllRootFeedback.className = 'path-feedback-status';
    } else {
      const resolved = data.resolved_jekyll_root || data.resolved_root || raw;
      if (data.posts_dir_exists) {
        el.cfgJekyllRootFeedback.textContent = `Caminho no servidor: ${resolved} (${data.posts_count} posts encontrados em _posts/)`;
        el.cfgJekyllRootFeedback.className = 'path-feedback-status success';
      } else if (data.root_exists) {
        el.cfgJekyllRootFeedback.textContent = `Pasta encontrada (${resolved}), mas subpasta _posts/ ainda não existe.`;
        el.cfgJekyllRootFeedback.className = 'path-feedback-status warning';
      } else {
        el.cfgJekyllRootFeedback.textContent = `Aviso: Diretório não encontrado no servidor: ${resolved}`;
        el.cfgJekyllRootFeedback.className = 'path-feedback-status error';
      }
    }

    // Render detected candidates if available
    if (el.cfgDetectedCandidates) {
      const candidates = (data && data.detected_candidates) || [];
      if (candidates.length > 0) {
        el.cfgDetectedCandidates.style.display = 'block';
        el.cfgDetectedCandidates.innerHTML = `
          <span class="detected-candidates-title">Pastas do Jekyll detectadas no servidor:</span>
          <div class="candidates-list">
            ${candidates.map(c => `<button type="button" class="candidate-chip" data-path="${escapeHtml(c)}">[Usar] ${escapeHtml(c)}</button>`).join('')}
          </div>
        `;
        el.cfgDetectedCandidates.querySelectorAll('.candidate-chip').forEach(btn => {
          btn.addEventListener('click', () => {
            const p = btn.getAttribute('data-path');
            if (el.cfgJekyllRoot) {
              el.cfgJekyllRoot.value = p;
              checkPathRealtime(p);
            }
          });
        });
      } else {
        el.cfgDetectedCandidates.style.display = 'none';
      }
    }
  }

  let checkPathTimer = null;
  async function checkPathRealtime(path) {
    if (!path || !path.trim()) {
      if (el.cfgJekyllRootFeedback) {
        el.cfgJekyllRootFeedback.textContent = '';
        el.cfgJekyllRootFeedback.className = 'path-feedback-status';
      }
      return;
    }
    try {
      const res = await fetch('/api/config/check-path', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: path.trim() }),
      });
      if (res.ok) {
        const data = await res.json();
        updateJekyllRootFeedback(data);
      }
    } catch (e) {
      console.error('Erro ao verificar caminho:', e);
    }
  }

  async function loadConfig() {
    try {
      const res = await fetch('/api/config');
      if (!res.ok) throw new Error('Falha ao carregar configurações');
      const data = await res.json();
      state.config = data;

      if (el.cfgJekyllRoot) el.cfgJekyllRoot.value = data.jekyll_root || '';
      if (el.cfgBuildCommand) el.cfgBuildCommand.value = data.jekyll_command || 'bundle exec jekyll build';
      if (el.cfgDeployMode) el.cfgDeployMode.value = data.deploy_mode || 'local';
      if (el.cfgRemotePath) el.cfgRemotePath.value = data.ssh_remote_path || '';
      if (el.cfgSshUser) el.cfgSshUser.value = data.ssh_user || '';

      if (el.sshSettingsFields) {
        el.sshSettingsFields.style.display = (data.deploy_mode === 'ssh') ? 'block' : 'none';
      }

      if (el.pubSshHost) el.pubSshHost.value = data.ssh_host || '';
      if (el.pubSshPort) el.pubSshPort.value = data.ssh_port || 22;
      if (el.pubSshUser) el.pubSshUser.value = data.ssh_user || '';

      updateJekyllRootFeedback(data);
    } catch (err) {
      console.error('Erro ao buscar configurações:', err);
    }
  }

  async function saveConfig() {
    const payload = {
      jekyll_root: el.cfgJekyllRoot.value.trim(),
      jekyll_command: el.cfgBuildCommand.value.trim(),
      deploy_mode: el.cfgDeployMode ? el.cfgDeployMode.value : 'local',
      ssh_remote_path: el.cfgRemotePath.value.trim(),
      ssh_user: el.cfgSshUser.value.trim(),
    };

    try {
      const res = await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error('Falha ao salvar configurações');
      const data = await res.json();
      state.config = data;
      updateJekyllRootFeedback(data);

      if (data.posts_dir_exists) {
        showToast(`Configurações salvas! (${data.posts_count} posts encontrados)`, 'success');
      } else if (data.root_exists) {
        showToast('Salvo! Pasta encontrada, mas subpasta _posts não existe.', 'warning');
      } else if (data.jekyll_root) {
        showToast(`Aviso: Pasta '${data.resolved_jekyll_root || data.jekyll_root}' não existe no servidor!`, 'warning');
      } else {
        showToast('Configurações salvas com sucesso!', 'success');
      }

      closeModal(el.settingsModal);
      loadPosts();
    } catch (err) {
      showToast(`Erro ao salvar configurações: ${err.message}`, 'error');
    }
  }

  async function clearSyncCache() {
    if (el.clearCacheFeedback) {
      el.clearCacheFeedback.textContent = 'Limpando...';
      el.clearCacheFeedback.className = 'action-feedback';
    }

    try {
      const res = await fetch('/api/config/clear-cache', { method: 'POST' });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Erro ao limpar cache');

      if (el.clearCacheFeedback) {
        el.clearCacheFeedback.textContent = 'Cache limpo com sucesso!';
        el.clearCacheFeedback.className = 'action-feedback success';
      }
      showToast('Cache de sincronização limpo!', 'success');
    } catch (err) {
      if (el.clearCacheFeedback) {
        el.clearCacheFeedback.textContent = `Erro: ${err.message}`;
        el.clearCacheFeedback.className = 'action-feedback error';
      }
      showToast(`Erro: ${err.message}`, 'error');
    }
  }

  async function loadPosts() {
    try {
      const res = await fetch('/api/posts');
      if (!res.ok) throw new Error('Falha ao listar posts');
      const posts = await res.json();
      state.posts = posts;
      renderPostList();
    } catch (err) {
      console.error('Erro ao listar posts:', err);
      if (el.postList) {
        el.postList.innerHTML = '<div class="empty-list-placeholder">Configure o diretório Jekyll para visualizar posts.</div>';
      }
    }
  }

  function renderPostList() {
    if (!el.postList) return;
    const query = (el.postSearch ? el.postSearch.value.toLowerCase().trim() : '');

    const filtered = state.posts.filter((p) => {
      if (!query) return true;
      const title = (p.title || '').toLowerCase();
      const filename = (p.filename || '').toLowerCase();
      const categories = (p.categories || '').toLowerCase();
      return title.includes(query) || filename.includes(query) || categories.includes(query);
    });

    if (filtered.length === 0) {
      el.postList.innerHTML = `<div class="empty-list-placeholder">${
        query ? 'Nenhum post corresponde à busca' : 'Nenhum post encontrado'
      }</div>`;
      return;
    }

    el.postList.innerHTML = '';
    filtered.forEach((post) => {
      const item = document.createElement('div');
      item.className = `post-item ${state.currentFilename === post.filename ? 'active' : ''}`;
      item.setAttribute('role', 'listitem');
      item.setAttribute('data-filename', post.filename);

      item.innerHTML = `
        <div class="post-item-title" title="${escapeHtml(post.title)}">${escapeHtml(post.title)}</div>
        <div class="post-item-filename-row">
          <span class="post-item-filename" title="${escapeHtml(post.filename)}">${escapeHtml(post.filename)}</span>
          <button type="button" class="btn-copy-filename" title="Copiar nome do arquivo" aria-label="Copiar nome do arquivo">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
            </svg>
          </button>
        </div>
        ${post.categories ? `
        <div class="post-item-meta">
          <span class="post-item-category" title="${escapeHtml(post.categories)}">${escapeHtml(post.categories)}</span>
        </div>` : ''}
      `;

      const copyBtn = item.querySelector('.btn-copy-filename');
      if (copyBtn) {
        copyBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          copyToClipboard(post.filename)
            .then(() => showToast(`Copiado: ${post.filename}`, 'info'))
            .catch(() => showToast('Falha ao copiar nome do arquivo', 'error'));
        });
      }

      item.addEventListener('click', () => {
        if (state.currentFilename === post.filename) return;
        if (state.isDirty) {
          const confirmSwitch = confirm('Você tem alterações não salvas. Deseja descartá-las e abrir este post?');
          if (!confirmSwitch) return;
        }
        loadSinglePost(post.filename);
      });

      el.postList.appendChild(item);
    });
  }

  async function loadSinglePost(filename) {
    try {
      const res = await fetch(`/api/posts/${encodeURIComponent(filename)}`);
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Post não encontrado');
      }
      const data = await res.json();
      state.currentFilename = data.filename;
      el.postEditor.value = data.content;

      if (el.postCustomFilename) {
        el.postCustomFilename.value = data.filename;
      }
      updateFilenameDisplay(data.filename);
      setDirty(false);
      updateWordCount();
      renderPostList();
    } catch (err) {
      showToast(`Erro ao abrir post: ${err.message}`, 'error');
    }
  }

  function getClientFormattedDate() {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const offset = -now.getTimezoneOffset();
    const sign = offset >= 0 ? '+' : '-';
    const offsetHours = String(Math.floor(Math.abs(offset) / 60)).padStart(2, '0');
    const offsetMins = String(Math.abs(offset) % 60).padStart(2, '0');
    return `${year}-${month}-${day} ${hours}:${minutes} ${sign}${offsetHours}${offsetMins}`;
  }

  async function newPost() {
    if (state.isDirty) {
      const confirmNew = confirm('Você tem alterações não salvas. Deseja criar um novo post assim mesmo?');
      if (!confirmNew) return;
    }

    try {
      const clientDate = getClientFormattedDate();
      const res = await fetch(`/api/posts/template/new?client_date=${encodeURIComponent(clientDate)}`);
      if (!res.ok) throw new Error('Falha ao gerar template');
      const data = await res.json();

      state.currentFilename = null;
      el.postEditor.value = data.template;
      if (el.postCustomFilename) {
        el.postCustomFilename.value = '';
      }
      updateFilenameDisplay('sem-titulo.md');
      setDirty(false);
      updateWordCount();
      renderPostList();
      el.postEditor.focus();
    } catch (err) {
      showToast(`Erro ao criar novo post: ${err.message}`, 'error');
    }
  }

  async function savePost() {
    if (!el.postEditor) return;
    const content = el.postEditor.value;
    if (!content.trim()) {
      showToast('O conteúdo do post não pode estar vazio.', 'warning');
      return;
    }

    const customFilename = el.postCustomFilename ? el.postCustomFilename.value.trim() : '';

    setSaving(true);

    const payload = {
      content: content,
      current_filename: state.currentFilename,
      custom_filename: customFilename,
    };

    try {
      const res = await fetch('/api/posts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Falha ao salvar post');
      }

      state.currentFilename = data.filename;
      if (el.postCustomFilename) {
        el.postCustomFilename.value = data.filename;
      }
      updateFilenameDisplay(data.filename);
      setDirty(false);
      showToast('Post salvo com sucesso!', 'success');
      await loadPosts();
    } catch (err) {
      setSaving(false);
      showToast(`Erro ao salvar: ${err.message}`, 'error');
    }
  }

  // --- Editor Formatting Helpers ---

  let savedEditorSelection = { start: 0, end: 0, text: '' };

  function applyFormatting(action) {
    if (!el.postEditor) return;
    const textarea = el.postEditor;
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const text = textarea.value;
    const selected = text.substring(start, end);

    let replacement = '';
    let cursorOffset = 0;

    switch (action) {
      case 'bold':
        if (selected) {
          replacement = `**${selected}**`;
          cursorOffset = replacement.length;
        } else {
          replacement = '**texto**';
          cursorOffset = 2; // inside **|texto**
        }
        break;

      case 'italic':
        if (selected) {
          replacement = `*${selected}*`;
          cursorOffset = replacement.length;
        } else {
          replacement = '*texto*';
          cursorOffset = 1;
        }
        break;

      case 'underline':
        if (selected) {
          replacement = `<u>${selected}</u>`;
          cursorOffset = replacement.length;
        } else {
          replacement = '<u>texto</u>';
          cursorOffset = 3;
        }
        break;

      case 'strike':
        if (selected) {
          replacement = `~~${selected}~~`;
          cursorOffset = replacement.length;
        } else {
          replacement = '~~texto~~';
          cursorOffset = 2;
        }
        break;

      case 'code':
        if (selected) {
          replacement = `\`${selected}\``;
          cursorOffset = replacement.length;
        } else {
          replacement = '`código`';
          cursorOffset = 1;
        }
        break;

      case 'h2':
        if (selected) {
          replacement = `\n## ${selected}\n`;
        } else {
          replacement = '\n## Título\n';
        }
        cursorOffset = replacement.length;
        break;

      case 'h3':
        if (selected) {
          replacement = `\n### ${selected}\n`;
        } else {
          replacement = '\n### Subtítulo\n';
        }
        cursorOffset = replacement.length;
        break;

      case 'blockquote':
        if (selected) {
          const lines = selected.split('\n').map((l) => (l.startsWith('> ') ? l : `> ${l}`));
          replacement = lines.join('\n');
        } else {
          replacement = '> citação\n';
        }
        cursorOffset = replacement.length;
        break;

      case 'list':
      case 'unordered-list':
        if (selected) {
          const lines = selected.split('\n').map((l) => (l.startsWith('- ') ? l : `- ${l}`));
          replacement = lines.join('\n');
        } else {
          replacement = '- item\n';
        }
        cursorOffset = replacement.length;
        break;

      case 'ordered-list':
        if (selected) {
          const lines = selected.split('\n').map((l, idx) => {
            const stripped = l.replace(/^\d+\.\s*/, '');
            return `${idx + 1}. ${stripped || l}`;
          });
          replacement = lines.join('\n');
        } else {
          replacement = '1. item\n';
        }
        cursorOffset = replacement.length;
        break;

      case 'link':
        if (selected) {
          replacement = `[${selected}](url)`;
        } else {
          replacement = '[texto](url)';
        }
        cursorOffset = replacement.length;
        break;

      case 'internal-link':
        openInternalLinkModal(selected, start, end);
        return;

      default:
        return;
    }

    textarea.focus();
    // Using setRangeText for clean undo/redo support
    textarea.setRangeText(replacement, start, end, 'select');
    textarea.selectionStart = start + cursorOffset;
    textarea.selectionEnd = start + cursorOffset;

    setDirty(true);
    updateWordCount();
  }

  function openInternalLinkModal(selectedText, start, end) {
    savedEditorSelection = {
      start: (typeof start === 'number') ? start : (el.postEditor ? el.postEditor.selectionStart : 0),
      end: (typeof end === 'number') ? end : (el.postEditor ? el.postEditor.selectionEnd : 0),
      text: selectedText || '',
    };

    if (el.internalLinkText) {
      el.internalLinkText.value = selectedText || '';
    }
    if (el.internalLinkSlug) {
      el.internalLinkSlug.value = '';
    }
    if (el.internalLinkSearch) {
      el.internalLinkSearch.value = '';
    }

    renderInternalLinkPosts();
    openModal(el.internalLinkModal);

    setTimeout(() => {
      if (selectedText && el.internalLinkSlug) {
        el.internalLinkSlug.focus();
      } else if (el.internalLinkText) {
        el.internalLinkText.focus();
      }
    }, 100);
  }

  function renderInternalLinkPosts() {
    if (!el.internalLinkPostList) return;
    const query = (el.internalLinkSearch ? el.internalLinkSearch.value.toLowerCase().trim() : '');

    const filtered = (state.posts || []).filter((p) => {
      if (!query) return true;
      const title = (p.title || '').toLowerCase();
      const fn = (p.filename || '').toLowerCase();
      return title.includes(query) || fn.includes(query);
    });

    if (filtered.length === 0) {
      el.internalLinkPostList.innerHTML = '<div class="internal-link-item"><span style="color:var(--text-muted);font-size:0.8rem;">Nenhum post encontrado</span></div>';
      return;
    }

    el.internalLinkPostList.innerHTML = '';
    filtered.forEach((p) => {
      const item = document.createElement('div');
      item.className = 'internal-link-item';
      const slug = (p.filename || '').replace(/\.(md|markdown|html)$/i, '');
      item.innerHTML = `
        <div class="internal-link-item-title">${escapeHtml(p.title || p.filename)}</div>
        <div class="internal-link-item-slug">{% post_url ${escapeHtml(slug)} %}</div>
      `;

      item.addEventListener('click', () => {
        if (el.internalLinkSlug) el.internalLinkSlug.value = slug;
        if (el.internalLinkText && !el.internalLinkText.value.trim()) {
          el.internalLinkText.value = p.title || slug;
        }
        el.internalLinkPostList.querySelectorAll('.internal-link-item').forEach((i) => i.classList.remove('selected'));
        item.classList.add('selected');
      });

      item.addEventListener('dblclick', () => {
        if (el.internalLinkSlug) el.internalLinkSlug.value = slug;
        if (el.internalLinkText && !el.internalLinkText.value.trim()) {
          el.internalLinkText.value = p.title || slug;
        }
        confirmInsertInternalLink();
      });

      el.internalLinkPostList.appendChild(item);
    });
  }

  function confirmInsertInternalLink() {
    if (!el.postEditor) return;
    const textVal = (el.internalLinkText ? el.internalLinkText.value.trim() : '') || 'Link';
    let slugVal = (el.internalLinkSlug ? el.internalLinkSlug.value.trim() : '');
    slugVal = slugVal
      .replace(/\.(md|markdown|html)$/i, '')
      .replace(/^\{%\s*post_url\s+/, '')
      .replace(/\s*%\}$/, '')
      .trim();

    if (!slugVal) {
      showToast('Por favor, informe ou selecione o post para o link.', 'warning');
      if (el.internalLinkSlug) el.internalLinkSlug.focus();
      return;
    }

    const snippet = `[${textVal}]({% post_url ${slugVal} %})`;
    const textarea = el.postEditor;
    const start = savedEditorSelection.start;
    const end = savedEditorSelection.end;

    textarea.focus();
    textarea.setRangeText(snippet, start, end, 'select');
    textarea.selectionStart = start + snippet.length;
    textarea.selectionEnd = start + snippet.length;

    closeModal(el.internalLinkModal);
    setDirty(true);
    updateWordCount();
    showToast('Link interno inserido com sucesso!', 'info');
  }

  // --- Image Upload ---

  async function handleImageUpload(file) {
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    showToast('Processando e enviando imagem...', 'info', 2000);

    try {
      const res = await fetch('/api/images/upload', {
        method: 'POST',
        body: formData,
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Erro ao fazer upload da imagem');
      }

      const snippet = data.html_snippet ? `\n${data.html_snippet}\n` : `\n![${data.filename}](/assets/img/${data.filename})\n`;
      const textarea = el.postEditor;
      const start = textarea.selectionStart;
      const end = textarea.selectionEnd;

      textarea.setRangeText(snippet, start, end, 'end');
      setDirty(true);
      updateWordCount();
      showToast('Imagem inserida com sucesso!', 'success');
    } catch (err) {
      showToast(`Erro no upload da imagem: ${err.message}`, 'error');
    } finally {
      if (el.imageFileInput) el.imageFileInput.value = '';
    }
  }

  // --- SSH Test & Publish ---

  async function testSSHConnection() {
    const host = (el.pubSshHost.value || '').trim();
    const port = parseInt(el.pubSshPort.value, 10) || 22;
    const user = (el.pubSshUser.value || '').trim();
    const pass = el.pubSshPassword.value || '';

    if (!host || !user || !pass) {
      if (el.sshTestFeedback) {
        el.sshTestFeedback.textContent = 'Preencha Host, Usuário e Senha.';
        el.sshTestFeedback.className = 'action-feedback error';
      }
      return;
    }

    if (el.sshTestFeedback) {
      el.sshTestFeedback.textContent = 'Testando conexão...';
      el.sshTestFeedback.className = 'action-feedback';
    }

    try {
      const res = await fetch('/api/ssh/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ssh_host: host,
          ssh_port: port,
          ssh_user: user,
          ssh_password: pass,
        }),
      });

      const data = await res.json();
      if (data.success) {
        if (el.sshTestFeedback) {
          el.sshTestFeedback.textContent = 'Conexão SSH estabelecida com sucesso!';
          el.sshTestFeedback.className = 'action-feedback success';
        }
        showToast('SSH conectado com sucesso!', 'success');
      } else {
        if (el.sshTestFeedback) {
          el.sshTestFeedback.textContent = `Falha: ${data.message}`;
          el.sshTestFeedback.className = 'action-feedback error';
        }
        showToast(`Falha SSH: ${data.message}`, 'error');
      }
    } catch (err) {
      if (el.sshTestFeedback) {
        el.sshTestFeedback.textContent = `Erro: ${err.message}`;
        el.sshTestFeedback.className = 'action-feedback error';
      }
      showToast(`Erro SSH: ${err.message}`, 'error');
    }
  }

  function appendLogLine(message, level = 'info') {
    if (!el.logOutput) return;
    const line = document.createElement('div');
    line.className = `log-line log-${level}`;

    const timestamp = new Date().toLocaleTimeString('pt-BR', { hour12: false });
    line.textContent = `[${timestamp}] [${level.toUpperCase()}] ${message}`;

    el.logOutput.appendChild(line);
    el.logOutput.scrollTop = el.logOutput.scrollHeight;
  }

  function openLogDrawer() {
    if (el.logDrawer) el.logDrawer.classList.add('open');
  }

  function closeLogDrawer() {
    if (el.logDrawer) el.logDrawer.classList.remove('open');
  }

  function toggleLogDrawer() {
    if (el.logDrawer) el.logDrawer.classList.toggle('open');
  }

  async function executePublish(customPayload = null) {
    let payload = null;

    if (customPayload) {
      payload = customPayload;
    } else {
      const host = (el.pubSshHost.value || '').trim();
      const port = parseInt(el.pubSshPort.value, 10) || 22;
      const user = (el.pubSshUser.value || '').trim();
      const pass = el.pubSshPassword.value || '';

      if (!host || !user || !pass) {
        showToast('Preencha todas as credenciais SSH para publicar.', 'warning');
        return;
      }

      payload = {
        deploy_mode: 'ssh',
        ssh_host: host,
        ssh_port: port,
        ssh_user: user,
        ssh_password: pass,
      };
    }

    closeModal(el.publishModal);
    closeModal(el.confirmPublishModal);
    openLogDrawer();

    appendLogLine('Iniciando pipeline de publicação...', 'info');
    state.isPublishing = true;

    try {
      const response = await fetch('/api/publish', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Erro ao iniciar publicação');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split('\n\n');
        buffer = parts.pop(); // Retain incomplete chunk

        for (const part of parts) {
          const lines = part.split('\n');
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const jsonStr = line.slice(6).trim();
              if (!jsonStr) continue;
              try {
                const payload = JSON.parse(jsonStr);
                if (payload.event === 'done') {
                  if (payload.success) {
                    appendLogLine('Publicação concluída com sucesso!', 'success');
                    showToast('Publicação concluída com sucesso!', 'success');
                  } else {
                    appendLogLine('Publicação finalizada com erros.', 'error');
                    showToast('Publicação falhou. Verifique os logs.', 'error');
                  }
                } else if (payload.message) {
                  appendLogLine(payload.message, payload.level || 'info');
                }
              } catch (e) {
                console.error('Erro ao interpretar SSE JSON:', e, jsonStr);
              }
            }
          }
        }
      }
    } catch (err) {
      appendLogLine(`Erro fatal durante publicação: ${err.message}`, 'error');
      showToast(`Erro na publicação: ${err.message}`, 'error');
    } finally {
      state.isPublishing = false;
      // Clear sensitive password from input field
      if (el.pubSshPassword) el.pubSshPassword.value = '';
    }
  }

  // --- Modal Helpers ---

  function openModal(modal) {
    if (modal) modal.classList.remove('hidden');
  }

  function closeModal(modal) {
    if (modal) modal.classList.add('hidden');
  }

  // --- Event Listeners Setup ---

  function setupEventListeners() {
    // Sidebar toggle
    if (el.btnToggleSidebar && el.sidebar) {
      el.btnToggleSidebar.addEventListener('click', () => {
        el.sidebar.classList.toggle('collapsed');
      });
    }

    // Search filter
    if (el.postSearch) {
      el.postSearch.addEventListener('input', () => {
        renderPostList();
      });
    }

    // Editor typing & dirty state
    if (el.postEditor) {
      el.postEditor.addEventListener('input', () => {
        setDirty(true);
        updateWordCount();
      });

      // Tab key support
      el.postEditor.addEventListener('keydown', (e) => {
        if (e.key === 'Tab') {
          e.preventDefault();
          const start = el.postEditor.selectionStart;
          const end = el.postEditor.selectionEnd;
          el.postEditor.setRangeText('  ', start, end, 'end');
          setDirty(true);
        }
      });
    }

    // Global keyboard shortcuts
    window.addEventListener('keydown', (e) => {
      // Ctrl+S or Cmd+S to save
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') {
        e.preventDefault();
        savePost();
      }

      // Escape to close modals or log drawer
      if (e.key === 'Escape') {
        closeModal(el.settingsModal);
        closeModal(el.confirmPublishModal);
        closeModal(el.publishModal);
        closeModal(el.internalLinkModal);
        closeLogDrawer();
      }
    });

    // Action buttons
    if (el.btnNewPost) el.btnNewPost.addEventListener('click', newPost);
    if (el.btnSavePost) el.btnSavePost.addEventListener('click', savePost);

    // Custom filename bar
    if (el.postCustomFilename) {
      el.postCustomFilename.addEventListener('input', () => setDirty(true));
      el.postCustomFilename.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          savePost();
        }
      });
    }
    if (el.btnAutoFilename) {
      el.btnAutoFilename.addEventListener('click', autoGenerateFilenameFromContent);
    }

    // Toolbar buttons
    const toolbarButtons = [
      { el: el.btnBold, action: 'bold' },
      { el: el.btnItalic, action: 'italic' },
      { el: el.btnUnderline, action: 'underline' },
      { el: el.btnStrike, action: 'strike' },
      { el: el.btnInlineCode, action: 'code' },
      { el: el.btnH2, action: 'h2' },
      { el: el.btnH3, action: 'h3' },
      { el: el.btnBlockquote, action: 'blockquote' },
      { el: el.btnList, action: 'unordered-list' },
      { el: el.btnOrderedList, action: 'ordered-list' },
      { el: el.btnLink, action: 'link' },
      { el: el.btnInternalLink, action: 'internal-link' },
    ];

    toolbarButtons.forEach(({ el: btn, action }) => {
      if (btn) {
        btn.addEventListener('click', () => applyFormatting(action));
      }
    });

    // Internal Link Modal
    if (el.btnCloseInternalLinkX) el.btnCloseInternalLinkX.addEventListener('click', () => closeModal(el.internalLinkModal));
    if (el.btnCancelInternalLink) el.btnCancelInternalLink.addEventListener('click', () => closeModal(el.internalLinkModal));
    if (el.btnConfirmInternalLink) el.btnConfirmInternalLink.addEventListener('click', confirmInsertInternalLink);
    if (el.internalLinkSearch) el.internalLinkSearch.addEventListener('input', renderInternalLinkPosts);
    if (el.internalLinkSlug) {
      el.internalLinkSlug.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          confirmInsertInternalLink();
        }
      });
    }
    if (el.internalLinkText) {
      el.internalLinkText.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          confirmInsertInternalLink();
        }
      });
    }

    // Image upload input
    if (el.imageFileInput) {
      el.imageFileInput.addEventListener('change', (e) => {
        const file = e.target.files && e.target.files[0];
        if (file) handleImageUpload(file);
      });
    }

    // Settings Modal
    if (el.btnOpenSettings) {
      el.btnOpenSettings.addEventListener('click', () => {
        if (el.clearCacheFeedback) el.clearCacheFeedback.textContent = '';
        loadConfig();
        openModal(el.settingsModal);
      });
    }
    if (el.cfgJekyllRoot) {
      el.cfgJekyllRoot.addEventListener('input', () => {
        clearTimeout(checkPathTimer);
        checkPathTimer = setTimeout(() => {
          checkPathRealtime(el.cfgJekyllRoot.value);
        }, 300);
      });
    }
    if (el.cfgDeployMode) {
      el.cfgDeployMode.addEventListener('change', () => {
        if (el.sshSettingsFields) {
          el.sshSettingsFields.style.display = (el.cfgDeployMode.value === 'ssh') ? 'block' : 'none';
        }
      });
    }
    if (el.btnCloseSettings) el.btnCloseSettings.addEventListener('click', () => closeModal(el.settingsModal));
    if (el.btnCloseSettingsX) el.btnCloseSettingsX.addEventListener('click', () => closeModal(el.settingsModal));
    if (el.btnSaveSettings) el.btnSaveSettings.addEventListener('click', saveConfig);
    if (el.btnClearCache) el.btnClearCache.addEventListener('click', clearSyncCache);

    // Publish Trigger (decides between Local Confirm vs SSH Modal)
    if (el.btnOpenPublish) {
      el.btnOpenPublish.addEventListener('click', () => {
        const mode = (state.config && state.config.deploy_mode) || (el.cfgDeployMode ? el.cfgDeployMode.value : 'local');
        if (mode === 'local') {
          openModal(el.confirmPublishModal);
        } else {
          if (el.sshTestFeedback) el.sshTestFeedback.textContent = '';
          if (el.pubSshPassword) el.pubSshPassword.value = '';
          openModal(el.publishModal);
        }
      });
    }

    // Local Publish Modal
    if (el.btnCloseConfirmPublishX) el.btnCloseConfirmPublishX.addEventListener('click', () => closeModal(el.confirmPublishModal));
    if (el.btnCancelConfirmPublish) el.btnCancelConfirmPublish.addEventListener('click', () => closeModal(el.confirmPublishModal));
    if (el.btnExecuteLocalPublish) {
      el.btnExecuteLocalPublish.addEventListener('click', () => {
        executePublish({ deploy_mode: 'local' });
      });
    }

    // SSH Publish Modal
    if (el.btnClosePublishX) el.btnClosePublishX.addEventListener('click', () => closeModal(el.publishModal));
    if (el.btnCancelPublish) el.btnCancelPublish.addEventListener('click', () => closeModal(el.publishModal));
    if (el.btnTestSsh) el.btnTestSsh.addEventListener('click', testSSHConnection);
    if (el.btnConfirmPublish) el.btnConfirmPublish.addEventListener('click', () => executePublish());

    // Close modals on backdrop click
    [el.settingsModal, el.confirmPublishModal, el.publishModal, el.internalLinkModal].forEach((modal) => {
      if (modal) {
        modal.addEventListener('click', (e) => {
          if (e.target === modal) closeModal(modal);
        });
      }
    });

    // Log Drawer
    if (el.btnToggleLogs) el.btnToggleLogs.addEventListener('click', toggleLogDrawer);
    if (el.btnCloseLogs) el.btnCloseLogs.addEventListener('click', closeLogDrawer);
    if (el.btnClearLogs) {
      el.btnClearLogs.addEventListener('click', () => {
        if (el.logOutput) {
          el.logOutput.innerHTML = '<div class="log-line log-info">[INFO] Console limpo.</div>';
        }
      });
    }
  }

  // --- Initialize ---

  async function init() {
    setupEventListeners();
    await loadConfig();
    await loadPosts();

    // If posts exist, open the newest one; otherwise create new template
    if (state.posts && state.posts.length > 0) {
      await loadSinglePost(state.posts[0].filename);
    } else {
      await newPost();
    }
  }

  // Run on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
