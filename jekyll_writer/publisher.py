import os
import sys
import re
import json
import socket
import time
import hashlib
import subprocess
import paramiko
from typing import Callable, Optional, Dict, Any, Tuple

from jekyll_writer.image_optimizer import optimize_images, normalize_name
from jekyll_writer.frontmatter import slugify

class PublisherEngine:
    def __init__(self, log_callback: Optional[Callable[[str, str], None]] = None):
        """
        log_callback(message: str, level: str)
        level: 'info', 'success', 'warning', 'error'
        """
        self.log_callback = log_callback or (lambda msg, lvl: print(f"[{lvl.upper()}] {msg}"))
        self._is_cancelled = False

    def log(self, message: str, level: str = "info"):
        self.log_callback(message, level)

    def cancel(self):
        self._is_cancelled = True

    def _get_creationflags(self) -> int:
        if sys.platform == "win32":
            return subprocess.CREATE_NO_WINDOW
        return 0

    @staticmethod
    def get_portable_paths(base_dir: Optional[str] = None) -> Dict[str, Optional[str]]:
        if base_dir is None:
            if getattr(sys, "frozen", False):
                base_dir = os.path.dirname(sys.executable)
            else:
                base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

        cloudflared_path = None
        bin_cf = os.path.join(base_dir, "bin", "cloudflared.exe")
        root_cf = os.path.join(base_dir, "cloudflared.exe")
        if os.path.isfile(bin_cf):
            cloudflared_path = bin_cf
        elif os.path.isfile(root_cf):
            cloudflared_path = root_cf

        ruby_bin = None
        ruby_root = None
        candidate_ruby_bin = os.path.join(base_dir, "ruby", "bin")
        if os.path.isdir(candidate_ruby_bin):
            ruby_bin = candidate_ruby_bin
            ruby_root = os.path.join(base_dir, "ruby")

        return {
            "cloudflared": cloudflared_path,
            "ruby_bin": ruby_bin,
            "ruby_root": ruby_root,
        }

    def get_build_env(self, base_dir: Optional[str] = None) -> Dict[str, str]:
        env = os.environ.copy()
        paths = self.get_portable_paths(base_dir)
        ruby_bin = paths.get("ruby_bin")
        ruby_root = paths.get("ruby_root")

        if ruby_bin and ruby_root:
            path_key = "PATH"
            for k in list(env.keys()):
                if k.upper() == "PATH":
                    path_key = k
                    break

            current_path = env.get(path_key, "")
            env[path_key] = f"{ruby_bin}{os.pathsep}{current_path}" if current_path else ruby_bin
            if path_key != "PATH":
                env["PATH"] = env[path_key]

            gems_base = os.path.join(ruby_root, "lib", "ruby", "gems")
            gems_dir = os.path.join(gems_base, "4.0.0")
            if os.path.isdir(gems_base):
                subdirs = [d for d in os.listdir(gems_base) if os.path.isdir(os.path.join(gems_base, d))]
                if subdirs:
                    gems_dir = os.path.join(gems_base, sorted(subdirs)[-1])
            env["GEM_HOME"] = gems_dir
            env["GEM_PATH"] = gems_dir

            ssl_cert = os.path.join(ruby_root, "ssl", "cert.pem")
            if os.path.isfile(ssl_cert):
                env["SSL_CERT_FILE"] = ssl_cert

        return env

    def run_command(self, cmd: str, cwd: str) -> bool:
        self.log(f"$ {cmd}", "info")
        try:
            process = subprocess.Popen(
                cmd,
                cwd=cwd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=self.get_build_env(),
                creationflags=self._get_creationflags()
            )

            while True:
                if self._is_cancelled:
                    process.terminate()
                    self.log("Processo cancelado pelo usuário.", "warning")
                    return False
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    self.log(line.rstrip(), "info")

            rc = process.poll()
            if rc == 0:
                self.log("Etapa concluída com sucesso.", "success")
                return True
            else:
                self.log(f"Comando encerrou com código de erro {rc}.", "error")
                return False
        except Exception as e:
            self.log(f"Erro ao executar comando: {e}", "error")
            return False

    def _find_free_port(self) -> int:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            return s.getsockname()[1]

    def _check_cloudflared_in_ssh_config(self, host: str) -> Optional[str]:
        portable = self.get_portable_paths().get("cloudflared")
        if portable:
            return portable

        ssh_config_file = os.path.expanduser("~/.ssh/config")
        if not os.path.exists(ssh_config_file):
            return None
        try:
            ssh_conf = paramiko.SSHConfig()
            with open(ssh_config_file, "r", encoding="utf-8", errors="ignore") as f:
                ssh_conf.parse(f)
            host_conf = ssh_conf.lookup(host)
            proxy_cmd = host_conf.get("proxycommand", "")
            if "cloudflared" in proxy_cmd.lower():
                match = re.search(r'["\']?([^"\']+\bcloudflared(?:\.exe)?)["\']?', proxy_cmd, re.IGNORECASE)
                if match and os.path.exists(match.group(1)):
                    return match.group(1)
                for candidate in [
                    r"C:\Program Files (x86)\cloudflared\cloudflared.exe",
                    r"C:\Program Files\cloudflared\cloudflared.exe"
                ]:
                    if os.path.exists(candidate):
                        return candidate
                return "cloudflared"
        except Exception as e:
            self.log(f"Aviso ao ler ~/.ssh/config: {e}", "warning")
        return None

    def _start_cloudflared_tcp_bridge(self, cloudflared_bin: str, host: str) -> Tuple[int, subprocess.Popen]:
        free_port = self._find_free_port()
        self.log(f"Iniciando ponte Cloudflare Access TCP em segundo plano (porta local {free_port})...", "info")
        cmd = [
            cloudflared_bin,
            "access",
            "tcp",
            "--hostname",
            host,
            "--url",
            f"127.0.0.1:{free_port}"
        ]
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=self._get_creationflags()
        )

        # Wait for port to be listening
        connected = False
        start_time = time.time()
        while time.time() - start_time < 6.0:
            if proc.poll() is not None:
                err = proc.stderr.read().decode("utf-8", errors="ignore")
                raise RuntimeError(f"cloudflared encerrou inesperadamente: {err}")
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as test_sock:
                    test_sock.settimeout(0.5)
                    test_sock.connect(("127.0.0.1", free_port))
                    connected = True
                    break
            except Exception:
                time.sleep(0.2)

        if not connected:
            proc.terminate()
            raise TimeoutError("Tempo limite esgotado aguardando o túnel Cloudflare Access iniciar.")

        return free_port, proc

    def _create_ssh_client(self, ssh_config: Dict[str, Any]) -> Tuple[paramiko.SSHClient, Optional[subprocess.Popen]]:
        host = ssh_config.get("ssh_host", "").strip()
        port = int(ssh_config.get("ssh_port", 22))
        user = ssh_config.get("ssh_user", "").strip()
        password = ssh_config.get("ssh_password") or None

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        cloudflared_bin = self._check_cloudflared_in_ssh_config(host)
        tunnel_proc = None
        target_host = host
        target_port = port

        if cloudflared_bin:
            bridge_port, tunnel_proc = self._start_cloudflared_tcp_bridge(cloudflared_bin, host)
            target_host = "127.0.0.1"
            target_port = bridge_port

        connect_kwargs = {
            "hostname": target_host,
            "port": target_port,
            "username": user,
            "timeout": 20,
            "allow_agent": True,
            "look_for_keys": True
        }
        if password:
            connect_kwargs["password"] = password

        try:
            ssh.connect(**connect_kwargs)
            return ssh, tunnel_proc
        except Exception:
            if tunnel_proc:
                try:
                    tunnel_proc.terminate()
                    tunnel_proc.wait(timeout=2)
                except Exception:
                    pass
            raise

    def test_ssh_connection(self, ssh_config: Any, port: int = 22, user: str = "", password: str = "") -> Tuple[bool, str]:
        if isinstance(ssh_config, str):
            ssh_config = {
                "ssh_host": ssh_config,
                "ssh_port": port,
                "ssh_user": user,
                "ssh_password": password,
            }
        elif not isinstance(ssh_config, dict):
            ssh_config = {}
        host = ssh_config.get("ssh_host", "").strip()
        user = ssh_config.get("ssh_user", "").strip()
        if not host or not user:
            return False, "Host e Usuário são obrigatórios."

        tunnel_proc = None
        try:
            ssh, tunnel_proc = self._create_ssh_client(ssh_config)
            stdin, stdout, stderr = ssh.exec_command("echo connection_ok")
            res = stdout.read().decode().strip()
            ssh.close()
            if "connection_ok" in res:
                return True, "Conexão SSH estabelecida com sucesso!"
            return False, f"Resposta inesperada do servidor: {res}"
        except Exception as e:
            return False, f"Falha na conexão SSH: {e}"
        finally:
            if tunnel_proc:
                try:
                    tunnel_proc.terminate()
                    tunnel_proc.wait(timeout=2)
                except Exception:
                    pass

    @staticmethod
    def _calculate_file_hash(filepath: str) -> str:
        hasher = hashlib.md5()
        with open(filepath, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

    def clear_sync_cache(self, jekyll_root: str) -> bool:
        cache_file = os.path.join(jekyll_root, ".jekyll_writer_cache.json")
        if os.path.exists(cache_file):
            try:
                os.remove(cache_file)
                self.log("Cache de sincronização limpo com sucesso.", "info")
                return True
            except Exception as e:
                self.log(f"Erro ao limpar cache de sincronização: {e}", "warning")
                return False
        self.log("Nenhum cache de sincronização para limpar.", "info")
        return True

    def sync_sftp(self, local_dir: str, remote_dir: str, ssh_config: Dict[str, Any], cache_file: Optional[str] = None) -> bool:
        host = ssh_config.get("ssh_host", "").strip()
        user = ssh_config.get("ssh_user", "").strip()

        if not host or not user:
            self.log("Configurações de SSH incompletas (Host ou Usuário ausentes).", "error")
            return False

        self.log(f"Conectando ao servidor SSH ({user}@{host})...", "info")
        tunnel_proc = None
        try:
            ssh, tunnel_proc = self._create_ssh_client(ssh_config)
            self.log("Autenticação SSH realizada com sucesso.", "success")
            sftp = ssh.open_sftp()

            # Expand ~ in remote path if needed
            if remote_dir.startswith("~"):
                stdin, stdout, stderr = ssh.exec_command("pwd")
                remote_home = stdout.read().decode().strip()
                if remote_home:
                    remote_dir = remote_dir.replace("~", remote_home, 1)

            self.log(f"Iniciando sincronização inteligente para {remote_dir}...", "info")
            total_transferred = self._upload_dir_sftp(sftp, local_dir, remote_dir, cache_file=cache_file)
            sftp.close()
            ssh.close()

            self.log(f"Sincronização concluída com sucesso ({total_transferred} arquivos novos/alterados enviados).", "success")
            return True
        except Exception as e:
            self.log(f"Falha durante transferência SSH/SFTP: {e}", "error")
            return False
        finally:
            if tunnel_proc:
                try:
                    tunnel_proc.terminate()
                    tunnel_proc.wait(timeout=2)
                except Exception:
                    pass

    def _upload_dir_sftp(self, sftp, local_dir: str, remote_dir: str, cache_file: Optional[str] = None) -> int:
        cache: Dict[str, str] = {}
        if cache_file and os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cache = json.load(f)
            except Exception:
                cache = {}

        remote_dirs_created = set()

        def ensure_remote_dir(r_dir: str):
            if r_dir in remote_dirs_created:
                return
            parts = r_dir.split("/")
            accum = ""
            for p in parts:
                if not p:
                    accum += "/"
                    continue
                accum = f"{accum}/{p}" if accum and accum != "/" else f"/{p}"
                if accum not in remote_dirs_created:
                    try:
                        sftp.stat(accum)
                    except IOError:
                        try:
                            sftp.mkdir(accum)
                        except IOError:
                            pass
                    remote_dirs_created.add(accum)

        ensure_remote_dir(remote_dir)

        uploaded_count = 0
        skipped_count = 0

        # Collect all files recursively
        all_files = []
        for root, dirs, files in os.walk(local_dir):
            for file in files:
                all_files.append(os.path.join(root, file))

        for local_path in all_files:
            if self._is_cancelled:
                break

            # Se for imagem original e existir a versão .webp correspondente, envia apenas o .webp
            ext = os.path.splitext(local_path)[1].lower()
            if ext in {".png", ".jpg", ".jpeg", ".heic"}:
                folder = os.path.dirname(local_path)
                stem = os.path.splitext(os.path.basename(local_path))[0]
                candidates = [
                    f"{stem}.webp",
                    f"{normalize_name(stem)}.webp",
                    f"{slugify(stem)}.webp"
                ]
                if any(os.path.exists(os.path.join(folder, c)) for c in candidates):
                    skipped_count += 1
                    continue

            rel_path = os.path.relpath(local_path, local_dir).replace("\\", "/")
            cur_hash = self._calculate_file_hash(local_path)

            if cache.get(rel_path) == cur_hash:
                skipped_count += 1
                continue

            remote_path = f"{remote_dir}/{rel_path}"
            remote_parent = "/".join(remote_path.split("/")[:-1])
            ensure_remote_dir(remote_parent)

            self.log(f"Enviando: {rel_path}", "info")
            sftp.put(local_path, remote_path)
            cache[rel_path] = cur_hash
            uploaded_count += 1

        if cache_file:
            try:
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(cache, f, indent=2)
            except Exception as e:
                self.log(f"Aviso ao salvar cache de sincronização: {e}", "warning")

        if skipped_count > 0:
            self.log(f"Otimização de rede: {skipped_count} arquivos idênticos foram mantidos no servidor (não precisaram ser reenviados).", "info")

        return uploaded_count

    def run_pipeline(
        self,
        jekyll_root: str,
        has_images: bool,
        jekyll_cmd: str,
        ssh_config: Optional[Dict[str, Any]] = None
    ) -> bool:
        self._is_cancelled = False
        self.log("=========================================", "info")
        self.log("🚀 INICIANDO PIPELINE DE PUBLICAÇÃO", "info")
        self.log("=========================================", "info")

        if not jekyll_root or not os.path.isdir(jekyll_root):
            self.log(f"Erro: Pasta raiz do Jekyll não encontrada: '{jekyll_root}'", "error")
            return False

        # 1. Otimização de imagens embutida
        if has_images:
            self.log("🖼️ Executando otimização de imagens (embutido)...", "info")
            try:
                optimize_images(jekyll_root, log_callback=self.log)
            except Exception as e:
                self.log(f"Erro ao otimizar imagens: {e}", "error")
                return False

        # 2. Build do Jekyll
        self.log(f"🔨 Compilando blog Jekyll com: {jekyll_cmd}", "info")
        if not self.run_command(jekyll_cmd, cwd=jekyll_root):
            self.log("Erro na compilação do Jekyll. Envio cancelado.", "error")
            return False

        site_dir = os.path.join(jekyll_root, "_site")
        if not os.path.isdir(site_dir):
            self.log(f"Erro: Pasta '{site_dir}' não encontrada após a compilação.", "error")
            return False

        # 3. Transferência SFTP ou Deploy Local
        if ssh_config and ssh_config.get("ssh_host"):
            cache_file = os.path.join(jekyll_root, ".jekyll_writer_cache.json")
            remote_path = ssh_config.get("ssh_remote_path", "").strip() or "~/blog/_site"
            self.log(f"📡 Transferindo arquivos de _site/ para o servidor remoto via SFTP...", "info")
            if not self.sync_sftp(site_dir, remote_path, ssh_config, cache_file=cache_file):
                self.log("Falha no envio dos arquivos para o servidor.", "error")
                return False
        else:
            self.log("⚡ Modo Local: arquivos compilados em _site/ prontos para o servidor web.", "success")

        self.log("=========================================", "success")
        self.log("✅ PUBLICAÇÃO CONCLUÍDA COM SUCESSO!", "success")
        self.log("=========================================", "success")
        return True
