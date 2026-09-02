import os
import re
import threading
from datetime import datetime
from tkinter import filedialog, messagebox
import customtkinter as ctk

from jekyll_writer.config import ConfigManager
from jekyll_writer.frontmatter import (
    generate_new_post_template,
    parse_front_matter,
    save_post
)
from jekyll_writer.images import process_and_copy_image
from jekyll_writer.publisher import PublisherEngine

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class SettingsModal(ctk.CTkToplevel):
    def __init__(self, parent, config_manager: ConfigManager, on_save_callback=None):
        super().__init__(parent)
        self.config = config_manager
        self.on_save_callback = on_save_callback

        self.title("Configurações do Jekyll Writer")
        self.geometry("620x560")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._build_ui()
        self._load_values()

    def _build_ui(self):
        pad_x = 24

        # Title
        title_lbl = ctk.CTkLabel(
            self,
            text="Configurações do Blog & Servidor",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_lbl.pack(pady=(20, 15), padx=pad_x, anchor="w")

        # Container
        frame = ctk.CTkScrollableFrame(self, width=570, height=400)
        frame.pack(padx=pad_x, pady=(0, 15), fill="both", expand=True)

        # 1. Jekyll Root
        ctk.CTkLabel(frame, text="Pasta Raiz do Jekyll (Local):", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(5, 2))
        root_row = ctk.CTkFrame(frame, fg_color="transparent")
        root_row.pack(fill="x", pady=(0, 10))
        self.entry_root = ctk.CTkEntry(root_row, placeholder_text="C:\\caminho\\para\\meu-blog", height=32)
        self.entry_root.pack(side="left", fill="x", expand=True, padx=(0, 8))
        btn_browse = ctk.CTkButton(root_row, text="📁 Procurar...", width=110, height=32, command=self._browse_folder)
        btn_browse.pack(side="right")

        # 2. Jekyll Command
        ctk.CTkLabel(frame, text="Comando de Build do Jekyll:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(5, 2))
        self.entry_cmd = ctk.CTkEntry(frame, placeholder_text="bundle exec jekyll build", height=32)
        self.entry_cmd.pack(fill="x", pady=(0, 10))

        # Divider
        ctk.CTkLabel(frame, text="Configurações de Transferência SSH / SFTP", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(15, 5))

        # SSH Host & Port
        host_row = ctk.CTkFrame(frame, fg_color="transparent")
        host_row.pack(fill="x", pady=(0, 10))
        
        host_col = ctk.CTkFrame(host_row, fg_color="transparent")
        host_col.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkLabel(host_col, text="Servidor SSH (Host):").pack(anchor="w")
        self.entry_host = ctk.CTkEntry(host_col, placeholder_text="ssh.exemplo.com", height=32)
        self.entry_host.pack(fill="x")

        port_col = ctk.CTkFrame(host_row, fg_color="transparent")
        port_col.pack(side="right")
        ctk.CTkLabel(port_col, text="Porta:").pack(anchor="w")
        self.entry_port = ctk.CTkEntry(port_col, width=80, placeholder_text="22", height=32)
        self.entry_port.pack()

        # SSH User & Password
        user_row = ctk.CTkFrame(frame, fg_color="transparent")
        user_row.pack(fill="x", pady=(0, 10))

        user_col = ctk.CTkFrame(user_row, fg_color="transparent")
        user_col.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkLabel(user_col, text="Usuário SSH:").pack(anchor="w")
        self.entry_user = ctk.CTkEntry(user_col, placeholder_text="usuario", height=32)
        self.entry_user.pack(fill="x")

        pass_col = ctk.CTkFrame(user_row, fg_color="transparent")
        pass_col.pack(side="right", fill="x", expand=True)
        ctk.CTkLabel(pass_col, text="Senha SSH:").pack(anchor="w")
        
        pass_input_row = ctk.CTkFrame(pass_col, fg_color="transparent")
        pass_input_row.pack(fill="x")
        self.entry_pass = ctk.CTkEntry(pass_input_row, show="*", placeholder_text="••••••••", height=32)
        self.entry_pass.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self.show_pass = False
        self.btn_toggle_pass = ctk.CTkButton(pass_input_row, text="👁", width=36, height=32, command=self._toggle_password)
        self.btn_toggle_pass.pack(side="right")

        # Remote Path
        ctk.CTkLabel(frame, text="Pasta Remota de Destino (Servidor):", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(5, 2))
        self.entry_remote = ctk.CTkEntry(frame, placeholder_text="~/meu-blog/_site", height=32)
        self.entry_remote.pack(fill="x", pady=(0, 15))

        # Sync Cache
        cache_row = ctk.CTkFrame(frame, fg_color="transparent")
        cache_row.pack(fill="x", pady=(5, 10))
        ctk.CTkLabel(cache_row, text="Memória de Sincronização:").pack(side="left")
        self.btn_clear_cache = ctk.CTkButton(
            cache_row,
            text="🗑️ Limpar Cache",
            width=130,
            height=28,
            fg_color="#b91c1c",
            hover_color="#991b1b",
            command=self._clear_cache
        )
        self.btn_clear_cache.pack(side="right")

        # Bottom Buttons
        bottom_row = ctk.CTkFrame(self, fg_color="transparent")
        bottom_row.pack(fill="x", padx=pad_x, pady=(0, 15))

        self.btn_test = ctk.CTkButton(
            bottom_row,
            text="🔌 Testar SSH",
            fg_color="#334155",
            hover_color="#475569",
            command=self._test_ssh
        )
        self.btn_test.pack(side="left")

        self.btn_save = ctk.CTkButton(
            bottom_row,
            text="💾 Salvar Configurações",
            fg_color="#16a34a",
            hover_color="#15803d",
            command=self._save
        )
        self.btn_save.pack(side="right")

    def _toggle_password(self):
        self.show_pass = not self.show_pass
        self.entry_pass.configure(show="" if self.show_pass else "*")

    def _browse_folder(self):
        folder = filedialog.askdirectory(title="Selecione a pasta raiz do seu blog Jekyll")
        if folder:
            self.entry_root.delete(0, "end")
            self.entry_root.insert(0, os.path.abspath(folder))

    def _load_values(self):
        self.entry_root.insert(0, self.config.get("jekyll_root", ""))
        self.entry_cmd.insert(0, self.config.get("jekyll_command", "bundle exec jekyll build"))
        self.entry_host.insert(0, self.config.get("ssh_host", ""))
        self.entry_port.insert(0, str(self.config.get("ssh_port", 22)))
        self.entry_user.insert(0, self.config.get("ssh_user", ""))
        self.entry_pass.insert(0, self.config.get("ssh_password", ""))
        self.entry_remote.insert(0, self.config.get("ssh_remote_path", ""))

    def _test_ssh(self):
        self.btn_test.configure(text="Conectando...", state="disabled")
        self.update()

        def run_test():
            ssh_cfg = {
                "ssh_host": self.entry_host.get().strip(),
                "ssh_port": int(self.entry_port.get().strip() or 22),
                "ssh_user": self.entry_user.get().strip(),
                "ssh_password": self.entry_pass.get(),
            }
            engine = PublisherEngine()
            ok, msg = engine.test_ssh_connection(ssh_cfg)
            
            def update_ui():
                self.btn_test.configure(text="🔌 Testar SSH", state="normal")
                if ok:
                    messagebox.showinfo("Sucesso", msg, parent=self)
                else:
                    messagebox.showerror("Erro na Conexão", msg, parent=self)

            self.after(0, update_ui)

        threading.Thread(target=run_test, daemon=True).start()

    def _clear_cache(self):
        root = self.entry_root.get().strip()
        if not root or not os.path.isdir(root):
            messagebox.showwarning("Pasta Inválida", "Por favor, selecione primeiro a pasta raiz do blog Jekyll.", parent=self)
            return
        res = messagebox.askyesno(
            "Limpar Cache de Sincronização",
            "Deseja realmente limpar o cache de sincronização?\n\nNa próxima publicação, todos os arquivos do site serão reenviados para o servidor.",
            parent=self
        )
        if res:
            engine = PublisherEngine()
            engine.clear_sync_cache(root)
            messagebox.showinfo("Cache Limpo", "O cache de sincronização foi limpo com sucesso!", parent=self)

    def _save(self):
        self.config.set("jekyll_root", self.entry_root.get().strip())
        self.config.set("jekyll_command", self.entry_cmd.get().strip() or "bundle exec jekyll build")
        self.config.set("ssh_host", self.entry_host.get().strip())
        try:
            self.config.set("ssh_port", int(self.entry_port.get().strip() or 22))
        except ValueError:
            self.config.set("ssh_port", 22)
        self.config.set("ssh_user", self.entry_user.get().strip())
        self.config.set("ssh_password", self.entry_pass.get())
        self.config.set("ssh_remote_path", self.entry_remote.get().strip())
        self.config.save()

        if self.on_save_callback:
            self.on_save_callback()

        messagebox.showinfo("Configurações Salvas", "As configurações foram atualizadas com sucesso!", parent=self)
        self.destroy()


class JekyllWriterApp(ctk.CTk):
    def __init__(self, config_manager: ConfigManager = None):
        super().__init__()
        self.config = config_manager or ConfigManager()
        self.current_filepath = None
        self.has_images = False
        self.publisher = PublisherEngine(log_callback=self._append_log)

        self.title("Jekyll Writer")
        self.geometry("1100x750")
        self.minsize(850, 600)

        self._build_ui()
        self._bind_shortcuts()
        self.new_post()

    def _build_ui(self):
        # 1. Top Toolbar (Actions & Formatting)
        toolbar = ctk.CTkFrame(self, height=54, corner_radius=0)
        toolbar.pack(side="top", fill="x", padx=0, pady=0)

        # Left: Main Actions
        actions_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        actions_frame.pack(side="left", padx=12, pady=8)

        self.btn_new = ctk.CTkButton(actions_frame, text="📄 Novo", width=80, height=32, command=self.new_post)
        self.btn_new.pack(side="left", padx=3)

        self.btn_save = ctk.CTkButton(actions_frame, text="💾 Salvar", width=85, height=32, fg_color="#2563eb", hover_color="#1d4ed8", command=self.save_current_post)
        self.btn_save.pack(side="left", padx=3)

        self.btn_image = ctk.CTkButton(actions_frame, text="🖼️ Imagem", width=95, height=32, fg_color="#4f46e5", hover_color="#4338ca", command=self.insert_image)
        self.btn_image.pack(side="left", padx=3)

        # Center: Markdown Tools
        md_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        md_frame.pack(side="left", padx=10, pady=8)

        md_tools = [
            ("B", lambda: self._wrap_selection("**", "**"), "Negrito (Ctrl+B)"),
            ("I", lambda: self._wrap_selection("*", "*"), "Itálico (Ctrl+I)"),
            ("H2", lambda: self._insert_line_prefix("## "), "Título H2"),
            ("H3", lambda: self._insert_line_prefix("### "), "Subtítulo H3"),
            ("Link", self._insert_link, "Inserir Link"),
            ("Quote", lambda: self._insert_line_prefix("> "), "Citação"),
            ("Code", lambda: self._wrap_selection("`", "`"), "Código"),
            ("Lista", self._format_list, "Lista"),
            ("Mais", self._insert_more, "Separador <!--more-->"),
        ]

        for label, cmd, tooltip in md_tools:
            btn = ctk.CTkButton(
                md_frame,
                text=label,
                width=42,
                height=32,
                fg_color="#334155",
                hover_color="#475569",
                command=cmd
            )
            btn.pack(side="left", padx=2)

        # Right: Publish & Settings
        right_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        right_frame.pack(side="right", padx=12, pady=8)

        self.btn_publish = ctk.CTkButton(
            right_frame,
            text="🚀 Enviar Publicação",
            width=150,
            height=32,
            font=ctk.CTkFont(weight="bold"),
            fg_color="#16a34a",
            hover_color="#15803d",
            command=self.publish
        )
        self.btn_publish.pack(side="left", padx=6)

        self.btn_settings = ctk.CTkButton(
            right_frame,
            text="⚙️",
            width=38,
            height=32,
            fg_color="#334155",
            hover_color="#475569",
            command=self.open_settings
        )
        self.btn_settings.pack(side="left", padx=2)

        # 2. Main Editor Area
        self.editor_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.editor_frame.pack(side="top", fill="both", expand=True, padx=12, pady=(8, 4))

        self.textbox = ctk.CTkTextbox(
            self.editor_frame,
            font=ctk.CTkFont(family="Consolas", size=14),
            wrap="word",
            undo=True,
            corner_radius=8
        )
        self.textbox.pack(fill="both", expand=True)
        self.textbox.bind("<KeyRelease>", self._on_text_change)

        # 3. Log Drawer (Collapsible)
        self.log_drawer_visible = False
        self.log_frame = ctk.CTkFrame(self, height=180, corner_radius=8)
        
        log_header = ctk.CTkFrame(self.log_frame, height=32, fg_color="transparent")
        log_header.pack(side="top", fill="x", padx=8, pady=4)
        ctk.CTkLabel(log_header, text="📋 Console de Publicação & Logs", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
        ctk.CTkButton(log_header, text="✖ Ocultar", width=70, height=24, fg_color="transparent", hover_color="#334155", command=self.toggle_log_drawer).pack(side="right")

        self.log_textbox = ctk.CTkTextbox(
            self.log_frame,
            font=ctk.CTkFont(family="Consolas", size=12),
            wrap="none",
            height=140,
            corner_radius=6
        )
        self.log_textbox.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.log_textbox.configure(state="disabled")

        # 4. Status Bar
        self.statusbar = ctk.CTkFrame(self, height=28, corner_radius=0)
        self.statusbar.pack(side="bottom", fill="x")

        self.status_file_lbl = ctk.CTkLabel(self.statusbar, text="Novo post não salvo", font=ctk.CTkFont(size=12))
        self.status_file_lbl.pack(side="left", padx=12)

        self.btn_toggle_log = ctk.CTkButton(
            self.statusbar,
            text="📋 Logs",
            width=65,
            height=22,
            fg_color="#334155",
            hover_color="#475569",
            font=ctk.CTkFont(size=11),
            command=self.toggle_log_drawer
        )
        self.btn_toggle_log.pack(side="right", padx=12)

        self.status_words_lbl = ctk.CTkLabel(self.statusbar, text="Palavras: 0 | Linhas: 0", font=ctk.CTkFont(size=12))
        self.status_words_lbl.pack(side="right", padx=15)

    def _bind_shortcuts(self):
        self.bind("<Control-s>", lambda e: self.save_current_post())
        self.bind("<Control-S>", lambda e: self.save_current_post())
        self.bind("<Control-b>", lambda e: self._wrap_selection("**", "**"))
        self.bind("<Control-B>", lambda e: self._wrap_selection("**", "**"))
        self.bind("<Control-i>", lambda e: self._wrap_selection("*", "*"))
        self.bind("<Control-I>", lambda e: self._wrap_selection("*", "*"))
        self.bind("<Control-n>", lambda e: self.new_post())
        self.bind("<Control-N>", lambda e: self.new_post())

    def _on_text_change(self, event=None):
        content = self.textbox.get("1.0", "end-1c")
        words = len(re.findall(r"\b\w+\b", content))
        lines = content.count("\n") + (1 if content else 0)
        self.status_words_lbl.configure(text=f"Palavras: {words} | Linhas: {lines}")

    def toggle_log_drawer(self):
        if self.log_drawer_visible:
            self.log_frame.pack_forget()
            self.log_drawer_visible = False
            self.btn_toggle_log.configure(text="📋 Logs")
        else:
            self.log_frame.pack(side="bottom", fill="x", padx=12, pady=(0, 4), before=self.statusbar)
            self.log_drawer_visible = True
            self.btn_toggle_log.configure(text="✖ Ocultar Logs")

    def _append_log(self, message: str, level: str = "info"):
        def update():
            if not self.log_drawer_visible:
                self.toggle_log_drawer()
            self.log_textbox.configure(state="normal")
            timestamp = datetime.now().strftime("%H:%M:%S")
            prefix = {
                "info": "ℹ️",
                "success": "✅",
                "warning": "⚠️",
                "error": "❌"
            }.get(level, "•")
            self.log_textbox.insert("end", f"[{timestamp}] {prefix} {message}\n")
            self.log_textbox.see("end")
            self.log_textbox.configure(state="disabled")
        self.after(0, update)

    def new_post(self):
        template = generate_new_post_template()
        self.textbox.delete("1.0", "end")
        self.textbox.insert("1.0", template)
        self.current_filepath = None
        self.has_images = False
        self.status_file_lbl.configure(text="Novo post (não salvo)")
        # Position cursor after 'title: '
        self.textbox.focus_set()
        self.textbox.mark_set("insert", "2.7")
        self._on_text_change()

    def save_current_post(self) -> bool:
        posts_dir = self.config.get_posts_dir()
        if not posts_dir:
            res = messagebox.askyesno(
                "Configuração Necessária",
                "A pasta raiz do Jekyll ainda não foi configurada. Deseja configurar agora?",
                parent=self
            )
            if res:
                self.open_settings()
            return False

        content = self.textbox.get("1.0", "end-1c")
        fm = parse_front_matter(content)
        title = fm.get("title", "").strip()

        if not title:
            messagebox.showwarning("Título Vazio", "Por favor, preencha o campo 'title:' no cabeçalho antes de salvar.", parent=self)
            return False

        try:
            saved_path = save_post(content, posts_dir, current_filepath=self.current_filepath)
            self.current_filepath = saved_path
            filename = os.path.basename(saved_path)
            self.status_file_lbl.configure(text=f"Salvo: {filename}")
            self.title(f"Jekyll Writer - {filename}")
            return True
        except Exception as e:
            messagebox.showerror("Erro ao Salvar", f"Não foi possível salvar o arquivo:\n{e}", parent=self)
            return False

    def insert_image(self):
        jekyll_root = self.config.get("jekyll_root", "").strip()
        if not jekyll_root or not os.path.isdir(jekyll_root):
            messagebox.showwarning(
                "Configuração Necessária",
                "Por favor, selecione primeiro a pasta raiz do blog Jekyll nas Configurações.",
                parent=self
            )
            self.open_settings()
            return

        image_path = filedialog.askopenfilename(
            title="Selecione uma imagem para o post",
            filetypes=[
                ("Imagens", "*.png *.jpg *.jpeg *.webp *.gif *.bmp *.svg"),
                ("Todos os arquivos", "*.*")
            ],
            parent=self
        )
        if not image_path:
            return

        content = self.textbox.get("1.0", "end-1c")
        fm = parse_front_matter(content)

        try:
            html_snippet, dest_path = process_and_copy_image(
                source_image_path=image_path,
                jekyll_root=jekyll_root
            )
            self.has_images = True
            # Insert at current cursor position
            self.textbox.insert("insert", f"\n{html_snippet}\n")
            self._append_log("Imagem copiada para assets/imagens e bloco figure inserido.", "success")
        except Exception as e:
            messagebox.showerror("Erro ao Inserir Imagem", f"Falha ao copiar/inserir a imagem:\n{e}", parent=self)

    def _wrap_selection(self, prefix: str, suffix: str):
        try:
            sel_start = self.textbox.index("sel.first")
            sel_end = self.textbox.index("sel.last")
            selected_text = self.textbox.get(sel_start, sel_end)
            self.textbox.delete(sel_start, sel_end)
            self.textbox.insert(sel_start, f"{prefix}{selected_text}{suffix}")
        except Exception:
            # If no text selected, insert placeholder
            self.textbox.insert("insert", f"{prefix}texto{suffix}")

    def _insert_line_prefix(self, prefix: str):
        self.textbox.insert("insert", f"\n{prefix}")

    def _format_list(self):
        try:
            sel_start = self.textbox.index("sel.first")
            sel_end = self.textbox.index("sel.last")

            # Expand to full lines
            start_line = self.textbox.index(f"{sel_start} linestart")
            end_line = self.textbox.index(f"{sel_end} lineend")

            selected_text = self.textbox.get(start_line, end_line)
            lines = selected_text.split("\n")

            non_empty = [l for l in lines if l.strip()]
            all_bulleted = non_empty and all(l.lstrip().startswith("- ") for l in non_empty)

            new_lines = []
            for line in lines:
                if line.strip():
                    stripped = line.lstrip()
                    indent = line[:len(line) - len(stripped)]
                    if all_bulleted:
                        if stripped.startswith("- "):
                            new_lines.append(indent + stripped[2:])
                        else:
                            new_lines.append(line)
                    else:
                        if stripped.startswith("- "):
                            new_lines.append(line)
                        else:
                            new_lines.append(f"{indent}- {stripped}")
                else:
                    new_lines.append(line)

            replacement = "\n".join(new_lines)
            self.textbox.delete(start_line, end_line)
            self.textbox.insert(start_line, replacement)
        except Exception:
            self.textbox.insert("insert", "- ")

    def _insert_link(self):
        try:
            sel_start = self.textbox.index("sel.first")
            sel_end = self.textbox.index("sel.last")
            selected_text = self.textbox.get(sel_start, sel_end)
            self.textbox.delete(sel_start, sel_end)
            self.textbox.insert(sel_start, f"[{selected_text}](https://)")
        except Exception:
            self.textbox.insert("insert", "[link](https://)")

    def _insert_more(self):
        self.textbox.insert("insert", "\n<!--more-->\n\n")

    def open_settings(self):
        SettingsModal(self, self.config, on_save_callback=self._on_settings_saved)

    def _on_settings_saved(self):
        self._append_log("Configurações atualizadas.", "info")

    def publish(self):
        jekyll_root = self.config.get("jekyll_root", "").strip()
        if not jekyll_root or not os.path.isdir(jekyll_root):
            messagebox.showwarning(
                "Configuração Incompleta",
                "Por favor, configure a pasta raiz do Jekyll antes de publicar.",
                parent=self
            )
            self.open_settings()
            return

        # Auto save before publishing
        if not self.save_current_post():
            return

        # Check images
        content = self.textbox.get("1.0", "end-1c")
        has_images = self.has_images or ("<figure" in content) or ("<img" in content)

        jekyll_cmd = self.config.get("jekyll_command", "bundle exec jekyll build")
        ssh_config = {
            "ssh_host": self.config.get("ssh_host"),
            "ssh_port": self.config.get("ssh_port", 22),
            "ssh_user": self.config.get("ssh_user"),
            "ssh_password": self.config.get("ssh_password"),
            "ssh_remote_path": self.config.get("ssh_remote_path"),
        }

        # Disable publish button during execution
        self.btn_publish.configure(state="disabled", text="⏳ Publicando...")

        def run_publish_thread():
            success = self.publisher.run_pipeline(
                jekyll_root=jekyll_root,
                has_images=has_images,
                jekyll_cmd=jekyll_cmd,
                ssh_config=ssh_config
            )

            def finish_ui():
                self.btn_publish.configure(state="normal", text="🚀 Enviar Publicação")
                if success:
                    messagebox.showinfo("Publicação Enviada!", "O site foi construído e sincronizado com o servidor com sucesso!", parent=self)
                else:
                    messagebox.showerror("Erro na Publicação", "Ocorreu um erro durante a publicação. Verifique os logs abaixo.", parent=self)

            self.after(0, finish_ui)

        threading.Thread(target=run_publish_thread, daemon=True).start()
