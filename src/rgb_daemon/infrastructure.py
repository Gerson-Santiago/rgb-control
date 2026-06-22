from abc import ABC, abstractmethod
import subprocess
import os
import logging
import asyncio
from pathlib import Path
from typing import Optional, List, Tuple
from evdev import InputDevice, ecodes, list_devices

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
    def __init__(self, user: str = "sant", dbus_addr: str = "unix:path=/run/user/1000/bus") -> None:
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
    Substitui a dependência do script rgb.sh legado.
    """
    def __init__(self, device_id: int = 0, user: str = "sant") -> None:
        self.device_id = device_id
        self.user = user

    def apply(self, hex_code: str, name: str) -> bool:
        """
        Executa o comando openrgb para aplicar a cor estática.
        Tenta via SDK server local primeiro, e faz fallback para acesso direto se falhar.
        """
        color = hex_code.lstrip("#")
        log.info("Tentando aplicar cor %s (#%s) no dispositivo %s", name, color, self.device_id)
        
        # 1. Tenta via servidor SDK (sem --noautoconnect)
        cmd_sdk = ["openrgb", "--device", str(self.device_id), "--mode", "static", "--color", color]
        try:
            log.info("Executando (via SDK Server): %s", " ".join(cmd_sdk))
            res = subprocess.run(cmd_sdk, capture_output=True, text=True, timeout=5)
            if res.returncode == 0:
                log.info("Cor #%s aplicada com sucesso via SDK Server (stdout: %s)", color, res.stdout.strip() if res.stdout else "nenhuma saída")
                return True
            log.warning("Conexão via SDK Server falhou (código de saída %d): %s. Tentando acesso direto...", res.returncode, res.stderr.strip() if res.stderr else "sem saída")
        except Exception as e:
            log.warning("Erro ao tentar conectar via SDK Server: %s. Tentando acesso direto...", e)

        # 2. Fallback: Acesso direto ao hardware (com --noautoconnect)
        cmd_direct = ["openrgb", "--noautoconnect", "--device", str(self.device_id), "--mode", "static", "--color", color]
        try:
            log.info("Executando (Acesso Direto): %s", " ".join(cmd_direct))
            res = subprocess.run(cmd_direct, capture_output=True, text=True, timeout=5)
            if res.returncode == 0:
                log.info("Cor #%s aplicada com sucesso via Acesso Direto (stdout: %s)", color, res.stdout.strip() if res.stdout else "nenhuma saída")
                return True
            log.error("OpenRGB falhou no acesso direto (código de saída %d). Erro: %s", res.returncode, res.stderr.strip() if res.stderr else "sem mensagem de erro")
            return False
        except Exception as e:
            log.error("Erro fatal no acesso direto do openrgb: %s", e)
            return False

class FileStatusStorage(StatusStorage):
    def __init__(self, status_file: Path, pid_file: Path) -> None:
        self.status_file = status_file
        self.pid_file = pid_file

    def save_status(self, status: str) -> None:
        self.status_file.write_text(status)

    def save_pid(self, pid: int) -> None:
        self.pid_file.write_text(str(pid))
