import dataclasses
from typing import Optional, List, Tuple

@dataclasses.dataclass(frozen=True)
class Color:
    name: str
    hex_code: str

    def __post_init__(self):
        if len(self.hex_code) != 6:
            raise ValueError(f"Hex code inválido: {self.hex_code} (deve ter 6 caracteres)")
        try:
            int(self.hex_code, 16)
        except ValueError:
            raise ValueError(f"Hex code inválido: {self.hex_code} (não alfanumérico hex)")

PALETTE: List[Color] = [
    Color("Vermelho", "FF0000"), Color("Laranja",  "FF5500"), Color("Amarelo",  "FFFF00"),
    Color("Verde",    "00FF00"), Color("Ciano",    "00F2EA"), Color("Azul",     "0000FF"),
    Color("Roxo",     "AA00FF"), Color("Ambar",    "FFB200"), Color("Branco",   "FFFFFF"),
    Color("Desligar", "000000"),
]

@dataclasses.dataclass
class DaemonState:
    is_active: bool = False
    color_index: int = 8  # Branco
    last_toggle_time: float = 0.0
    mic_clicks: int = 0
    last_click_time: float = 0.0
    ok_press_time: Optional[float] = None
    is_grabbed: bool = False

    def next_color(self) -> Color:
        self.color_index = (self.color_index + 1) % len(PALETTE)
        return PALETTE[self.color_index]

    def prev_color(self) -> Color:
        self.color_index = (self.color_index - 1) % len(PALETTE)
        return PALETTE[self.color_index]

    def get_current_color(self) -> Color:
        return PALETTE[self.color_index]
