import subprocess
import os

class Backend:
    def __init__(self):
        # Caminho fixo para o arquivo de status (IPC simples entre GUI e Daemon)
        self.status_file = "/tmp/.controle_led.status"
        # rbg.sh pode estar na raiz, em assets/ ou no path
        self.root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    def is_service_active(self) -> bool:
        """Verifica se o systemctl list-units ou is-active retorna active"""
        try:
            res = subprocess.run(["systemctl", "is-active", "openrbg.service"], capture_output=True, text=True)
            return res.stdout.strip() == "active"
        except Exception:
            return False

    def set_service_state(self, active: bool) -> bool:
        """Usa pkexec para subir privilegios e iniciar/parar o serviço"""
        try:
            action = "start" if active else "stop"
            res = subprocess.run(["pkexec", "systemctl", action, "openrbg.service"], capture_output=True)
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
                
            pid_file = "/tmp/.controle_led.pid"
            if os.path.exists(pid_file):
                with open(pid_file, "r") as p:
                    pid = int(p.read().strip())
                os.kill(pid, 10) # SIGUSR1
        except Exception as e:
            print("Erro mode_toggle:", e)

    def apply_color(self, hex_val: str, name: str) -> None:
        """
        Aplica a cor via openrgb nativamente.
        Contém fallback de sudo para dispositivos que exigem permissão root (igual ao rbg.sh).
        """
        color = hex_val.lstrip("#")
        try:
            # Tenta rodar sem sudo primeiro
            res = subprocess.run(["openrgb", "--device", "0", "--mode", "static", "--color", color],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Se falhar (código de saída não for 0), tenta via sudo (pedirá senha silenciosamente no tty ou falhará caso sem polkit)
            if res.returncode != 0:
                subprocess.Popen(["sudo", "openrgb", "--device", "0", "--mode", "static", "--color", color],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"Erro ao aplicar cor na GUI: {e}")

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
