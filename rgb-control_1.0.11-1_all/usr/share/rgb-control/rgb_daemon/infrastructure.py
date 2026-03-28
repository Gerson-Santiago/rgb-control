from abc import ABC, abstractmethod
import subprocess
import os
import logging
from pathlib import Path
from typing import Optional, List, Tuple

log = logging.getLogger("rgb_daemon.infrastructure")

class OSDProvider(ABC):
    @abstractmethod
    def notify(self, title: str, body: str, urgency: str = "normal", icon: str = "") -> None:
        pass

class ColorApplicator(ABC):
    @abstractmethod
    def apply(self, hex_code: str, name: str) -> bool:
        """Aplica a cor ao hardware."""
        raise NotImplementedError

class StatusStorage(ABC):
    @abstractmethod
    def save_status(self, status: str) -> None:
        pass
    @abstractmethod
    def save_pid(self, pid: int) -> None:
        pass

class NotifyOSD(OSDProvider):
    def __init__(self, user: str = "sant", dbus_addr: str = "unix:path=/run/user/1000/bus"):
        self.user = user
        self.dbus_addr = dbus_addr

    def notify(self, title: str, body: str, urgency: str = "normal", icon: str = "") -> None:
        try:
            cmd = [
                "sudo", "-u", self.user,
                "env", f"DBUS_SESSION_BUS_ADDRESS={self.dbus_addr}",
                "notify-send", title, body,
                f"--urgency={urgency}", "-t", "3000",
                "-h", "string:x-dunst-stack-tag:modo_led"
            ]
            if icon:
                cmd.extend(["-i", icon])
            subprocess.run(cmd, capture_output=True)
        except Exception as e:
            log.warning("Falha na notificação: %s", e)

class OpenRGBColorApplicator(ColorApplicator):
    """
    Aplica cores via comando openrgb direto.
    Substitui a dependência do script rbg.sh legado.
    """
    def __init__(self, device_id: int = 0, user: str = "sant"):
        self.device_id = device_id
        self.user = user

    def apply(self, hex_code: str, name: str) -> bool:
        """
        Executa o comando openrgb para aplicar a cor estática.
        """
        # Remove # se vier da GUI
        color = hex_code.lstrip("#")
        try:
            # Tenta executar como o usuário atual primeiro, depois com sudo se falhar
            # (Geralmente openrgb precisa de permissão de hardware ou daemon rodando)
            cmd = ["openrgb", "--device", str(self.device_id), "--mode", "static", "--color", color]
            log.debug("Executando: %s", " ".join(cmd))
            
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if res.returncode == 0:
                return True
            
            # Tenta com sudo se falhar (opcional, dependendo do setup udev)
            log.warning("Falha ao aplicar cor (sem sudo), tentando fallback...")
            cmd_sudo = ["sudo", "-u", self.user] + cmd
            res_sudo = subprocess.run(cmd_sudo, capture_output=True, text=True, timeout=5)
            return res_sudo.returncode == 0
        except Exception as e:
            log.error("Erro fatal ao aplicar cor: %s", e)
            return False

class FileStatusStorage(StatusStorage):
    def __init__(self, status_file: Path, pid_file: Path):
        self.status_file = status_file
        self.pid_file = pid_file

    def save_status(self, status: str) -> None:
        self.status_file.write_text(status)

    def save_pid(self, pid: int) -> None:
        self.pid_file.write_text(str(pid))
