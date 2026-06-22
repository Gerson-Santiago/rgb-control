import subprocess
import os

class Backend:
    STATUS_FILE = "/tmp/.controle_led.status"
    COLOR_FILE = "/tmp/.controle_led.color"
    PID_FILE = "/tmp/.controle_led.pid"

    def __init__(self) -> None:
        # Caminho fixo para o arquivo de status (IPC simples entre GUI e Daemon)
        self.status_file = self.STATUS_FILE
        self.color_file = self.COLOR_FILE
        # rgb.sh pode estar na raiz, em assets/ ou no path
        self.root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


    def is_service_active(self) -> bool:
        """Verifica se o systemctl list-units ou is-active retorna active"""
        try:
            res = subprocess.run(["systemctl", "is-active", "rgb-control-daemon.service"], capture_output=True, text=True)
            return res.stdout.strip() == "active"
        except Exception:
            return False

    def set_service_state(self, active: bool) -> bool:
        """Usa pkexec para subir privilegios e iniciar/parar o serviço"""
        try:
            action = "start" if active else "stop"
            res = subprocess.run(["pkexec", "systemctl", action, "rgb-control-daemon.service"], capture_output=True)
            return res.returncode == 0
        except Exception:
            return False

    def is_led_mode_active(self) -> bool:
        """Lê o arquivo de estado compartilhado com o daemon"""
        if not os.path.exists(self.status_file):
            return False
        try:
            with open(self.status_file, "r") as f:
                return "on" in f.read().strip()
        except:
            return False

    def set_led_mode(self, active: bool) -> None:
        """Escreve no status file e manda sinal para o daemon recarregar o estado"""
        try:
            with open(self.status_file, "w") as f:
                f.write("on" if active else "off")
                
            if os.path.exists(self.PID_FILE):
                with open(self.PID_FILE, "r") as p:
                    pid = int(p.read().strip())

                os.kill(pid, 10) # SIGUSR1
        except Exception as e:
            print("Erro mode_toggle:", e)

    def apply_color(self, hex_val: str, name: str) -> None:
        """
        Aplica a cor via openrgb nativamente.
        Tenta via SDK server local primeiro, e faz fallback para acesso direto (com e sem pkexec).
        """
        color = hex_val.lstrip("#")
        mode = "off" if color == "000000" else "static"
        color_args = [] if color == "000000" else ["--color", color]
        try:
            # 1. Tenta rodar normal via servidor local (sem --noautoconnect)
            cmd = ["openrgb", "--device", "0", "--mode", mode] + color_args
            res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # 2. Se falhar, tenta com --noautoconnect (acesso direto local como usuário)
            if res.returncode != 0:
                cmd = ["openrgb", "--noautoconnect", "--device", "0", "--mode", mode] + color_args
                res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
            # 3. Se ainda falhar, tenta via pkexec (acesso root direto local)
            if res.returncode != 0:
                pk_cmd = ["pkexec", "openrgb", "--noautoconnect", "--device", "0", "--mode", mode] + color_args
                subprocess.Popen(pk_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"Erro ao aplicar cor na GUI: {e}")
            
        try:
            with open(self.color_file, "w") as f:
                f.write(f"#{color}")
        except Exception:
            pass

    def get_current_color(self) -> str:
        """Lê o código hexadecimal da cor sincronizada em memória."""
        if os.path.exists(self.color_file):
            try:
                with open(self.color_file, "r") as f:
                    v = f.read().strip()
                    if v.startswith("#") and len(v) == 7:
                        return v
            except:
                pass
        return "#FF0000" # Vermelho default de fabrica


    def get_daemon_logs(self, limit: int = 20) -> list[str]:
        """Lê as últimas N linhas do log do daemon"""
        log_file = os.path.expanduser("~/.cache/rgb-control/daemon.log")
        if not os.path.exists(log_file):
            return ["Arquivo de log não encontrado."]
        
        try:
            with open(log_file, "r") as f:
                lines = f.readlines()
                # Garantindo que o slice seja compatível com tipagem estrita
                count = len(lines)
                start_idx = max(0, count - limit)
                # Slicing explícito
                tail_lines = []
                for i in range(start_idx, count):
                    tail_lines.append(lines[i].strip())
                return tail_lines
        except Exception as e:
            return [f"Erro ao ler log: {e}"]

    def is_controller_connected(self) -> bool:
        """Verifica no barramento evdev se o controle físico (1915:1025) está conectado."""
        try:
            from evdev import list_devices, InputDevice
            for path in list_devices():
                try:
                    dev = InputDevice(path)
                    if dev.info.vendor == 0x1915 and dev.info.product == 0x1025:
                        return True
                except Exception:
                    pass
        except Exception:
            pass
        return False

    def get_daemon_log_path(self) -> str:
        if os.path.exists("/var/log/rgb-control-daemon.log"):
            return "/var/log/rgb-control-daemon.log"
        if os.path.exists("/tmp/rgb-control-daemon.log"):
            return "/tmp/rgb-control-daemon.log"
        return os.path.expanduser("~/.cache/rgb-control/daemon.log")

    def get_gui_log_path(self) -> str:
        return os.path.expanduser("~/.cache/rgb-control/app.log")

    def read_log_file(self, path: str) -> str:
        """Retorna todo o conteúdo do arquivo de log"""
        if not os.path.exists(path):
            return f"Arquivo de log não encontrado em: {path}"
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"Erro ao ler log: {e}"

    def clear_log_file(self, path: str) -> bool:
        """Limpa o conteúdo do arquivo de log"""
        if not os.path.exists(path):
            return False
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("")
            return True
        except Exception:
            return False

