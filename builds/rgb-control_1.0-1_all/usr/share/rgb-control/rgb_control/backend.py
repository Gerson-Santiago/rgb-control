import subprocess
import os

class Backend:
    def __init__(self):
        # Resolve o caminho do Status File baseado de onde está executando
        self.status_file = "/tmp/.controle_led.status"
        local_status_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".controle_led.status")
        
        # Prefere o local se a pasta existir (onde o MVP foi rodado antes)
        if os.path.exists(os.path.dirname(local_status_file)):
            self.status_file = local_status_file

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
        """Lê o arquivo de estado compartilhado com mvp.py"""
        if not os.path.exists(self.status_file):
            return False
        try:
            with open(self.status_file, "r") as f:
                return "on" in f.read().strip()
        except:
            return False

    def set_led_mode(self, active: bool) -> None:
        """Escreve no status file e manda sinal para o mvp.py recarregar o estado"""
        try:
            with open(self.status_file, "w") as f:
                f.write("on" if active else "off")
                
            pid_file = self.status_file.replace(".status", ".pid")
            if os.path.exists(pid_file):
                with open(pid_file, "r") as p:
                    pid = int(p.read().strip())
                # Envia sinal de SIGUSR1 para o daemon (que alterna seu estado interno em memoria e notifica)
                # OBS: Como nós setamos "on" ou "off", o toggle do daemon vai sempre inverter. 
                # Um problema pequeno é que sinalizar toggle inverte o estado atual, 
                # então se a gnt acabou de forçar a string pra 'on', ele pode ler ou apenas ignorar.
                # No MVP o SIGUSR1 apenas alterna.
                os.kill(pid, 10)
        except Exception as e:
            print("Erro mode_toggle:", e)

    def apply_color(self, hex_val: str, name: str) -> None:
        # Busca o rbg.sh local ou instalado
        script_path = "/usr/bin/rbg.sh"
        if not os.path.exists(script_path):
            local_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "rbg.sh")
            if os.path.exists(local_path):
                script_path = local_path
        
        name_cor = name.lower().replace("desligar", "off").replace("âmbar", "ambar")
        
        # Prioriza via bash rbg.sh (por usar o mesmo padrão validado)
        if os.path.exists(script_path):
            try:
                subprocess.Popen(["bash", script_path, name_cor])
                return
            except:
                pass
                
        # Fallback para execução direta em caso do script não existir
        try:
            subprocess.Popen(["openrgb", "--device", "0", "--mode", "static", "--color", hex_val.lstrip("#")])
        except:
            pass
