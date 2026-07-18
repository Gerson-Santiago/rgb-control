import subprocess
import os
from typing import Any

class Backend:
    COLOR_FILE = "/tmp/.controle_led.color"

    def __init__(self) -> None:
        self.color_file = self.COLOR_FILE
        # rgb.sh pode estar na raiz, em assets/ ou no path
        self.root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))




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

    def get_extension_config_path(self) -> str:
        """Retorna o caminho do arquivo de configuração da extensão do GNOME."""
        return os.path.expanduser("~/.config/rgb-control/config.json")

    def get_default_extension_config(self) -> dict[str, Any]:
        """Lê a configuração padrão da extensão. SSOT: assets/default_config.json"""
        import json
        candidates = [
            os.path.join(self.root_dir, "assets", "default_config.json"),
            "/usr/share/rgb-control/assets/default_config.json",
        ]
        for path in candidates:
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        return json.load(f)  # type: ignore[no-any-return]
                except Exception:
                    pass
        # Fallback de emergência — não deve ser atingido em ambiente normal
        return {
            "quick_colors": [
                {"name": "Laranja", "hex": "#FF5500"},
                {"name": "Vermelho", "hex": "#FF0000"},
                {"name": "Azul",    "hex": "#0000FF"},
            ]
        }

    def get_extension_config(self) -> dict[str, Any]:
        """Lê e retorna a configuração da extensão do GNOME."""
        path = self.get_extension_config_path()
        if os.path.exists(path):
            try:
                import json
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "quick_colors" in data and len(data["quick_colors"]) == 3:
                        return data # type: ignore[no-any-return]
            except Exception:
                pass
        return self.get_default_extension_config()

    def save_extension_config(self, config: dict[str, Any]) -> None:
        """Salva a configuração da extensão do GNOME no arquivo JSON."""
        path = self.get_extension_config_path()
        try:
            import json
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Erro ao salvar config da extensão: {e}")


