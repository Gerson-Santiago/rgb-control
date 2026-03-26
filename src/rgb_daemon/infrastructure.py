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
        pass

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

class ShellColorApplicator(ColorApplicator):
    def __init__(self, script_path: Path, user: str = "sant"):
        self.script_path = script_path
        self.user = user

    def apply(self, hex_code: str, name: str) -> bool:
        nome_cor = name.lower().replace("desligar", "off").replace("âmbar", "ambar")
        if self.script_path.exists():
            try:
                cmd = ["sudo", "-u", self.user, "bash", str(self.script_path), nome_cor]
                res = subprocess.run(cmd, capture_output=True, text=True)
                if res.returncode == 0:
                    return True
            except Exception:
                pass
        
        # Fallback
        try:
            cmd_fb = ["openrgb", "--device", "0", "--mode", "static", "--color", hex_code.lstrip("#")]
            return subprocess.run(cmd_fb, capture_output=True).returncode == 0
        except Exception:
            return False

class FileStatusStorage(StatusStorage):
    def __init__(self, status_file: Path, pid_file: Path):
        self.status_file = status_file
        self.pid_file = pid_file

    def save_status(self, status: str) -> None:
        self.status_file.write_text(status)

    def save_pid(self, pid: int) -> None:
        self.pid_file.write_text(str(pid))
