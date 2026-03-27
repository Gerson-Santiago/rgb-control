import logging
import time
from typing import Optional
from rgb_daemon.domain import DaemonState, Color
from rgb_daemon.infrastructure import OSDProvider, ColorApplicator, StatusStorage

log = logging.getLogger("rgb_daemon.application")

class DaemonUseCases:
    def __init__(
        self,
        state: DaemonState,
        osd: OSDProvider,
        applicator: ColorApplicator,
        storage: StatusStorage
    ):
        self.state = state
        self.osd = osd
        self.applicator = applicator
        self.storage = storage

    def toggle_mode(self, hardware_grabber=None) -> None:
        now = time.monotonic()
        if now - self.state.last_toggle_time < 0.5:
            return
        self.state.last_toggle_time = now

        self.state.is_active = not self.state.is_active
        if self.state.is_active:
            log.info("✅ MODO LED ATIVO")
            if hardware_grabber:
                try:
                    hardware_grabber.grab()
                    self.state.is_grabbed = True
                except Exception:
                    log.warning("⚠️ Grab falhou")
            self.storage.save_status("on")
            self.osd.notify(
                "🟢  MODO LED",
                "ATIVO — use ← → ou Vol± para cores",
                urgency="normal",
                icon="display-brightness-high"
            )
        else:
            log.info("🔕 MODO LED DESATIVADO")
            if hardware_grabber and self.state.is_grabbed:
                try:
                    hardware_grabber.ungrab()
                    self.state.is_grabbed = False
                except Exception:
                    pass
            self.storage.save_status("off")
            self.osd.notify(
                "⚫  MODO LED",
                "MODO LED — Desativado",
                urgency="normal",
                icon="display-brightness-off"
            )

    def next_color(self) -> None:
        if not self.state.is_active:
            return
        color = self.state.next_color()
        if self.applicator.apply(color.hex_code, color.name):
            self.osd.notify(f"🎨 {color.name}", "Setas navegam | Vol±", "normal", "color-picker")

    def prev_color(self) -> None:
        if not self.state.is_active:
            return
        color = self.state.prev_color()
        if self.applicator.apply(color.hex_code, color.name):
            self.osd.notify(f"🎨 {color.name}", "Setas navegam | Vol±", "normal", "color-picker")
