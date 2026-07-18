"""
rgb_config.config
=================
Módulo de responsabilidade única: gerenciar leitura e escrita do arquivo de
configuração da extensão GNOME (~/.config/rgb-control/config.json).

Sem dependências externas — Python puro + stdlib.
"""
import json
import os
from typing import Optional

# ---------------------------------------------------------------------------
# Tipos
# ---------------------------------------------------------------------------
ColorEntry = dict[str, str]  # {"name": "Laranja", "hex": "#FF5500"}
Config = dict[str, list[ColorEntry]]  # {"quick_colors": [...]}

# ---------------------------------------------------------------------------
# SSOT — cores padrão
# ---------------------------------------------------------------------------
_SSOT_CANDIDATES = [
    # Instalação local de desenvolvimento (raiz do projeto)
    os.path.join(os.path.dirname(__file__), "..", "..", "assets", "default_config.json"),
    # Instalação global via .deb
    "/usr/share/rgb-control/assets/default_config.json",
]

_FALLBACK_COLORS: list[ColorEntry] = [
    {"name": "Laranja",  "hex": "#FF5500"},
    {"name": "Vermelho", "hex": "#FF0000"},
    {"name": "Azul",     "hex": "#0000FF"},
    {"name": "Verde",    "hex": "#00FF00"},
    {"name": "Ciano",    "hex": "#00FFFF"},
    {"name": "Roxo",     "hex": "#FF00FF"},
    {"name": "Amarelo",  "hex": "#FFFF00"},
    {"name": "Branco",   "hex": "#FFFFFF"},
]


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def get_config_path() -> str:
    """Retorna o caminho canônico do config.json do usuário."""
    return os.path.expanduser("~/.config/rgb-control/config.json")


def get_default_config() -> Config:
    """
    Lê e retorna as cores padrão a partir do arquivo SSOT (assets/default_config.json).
    Em caso de falha, usa o fallback embutido — nunca levanta exceção.
    """
    for candidate in _SSOT_CANDIDATES:
        path = os.path.normpath(candidate)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data: Config = json.load(f)
                if "quick_colors" in data and len(data["quick_colors"]) == 8:
                    return data
            except Exception:
                pass
    return {"quick_colors": list(_FALLBACK_COLORS)}


def read_config() -> Config:
    """
    Lê o config.json do usuário. Se ausente, corrompido ou com quantidade
    incorreta de cores, retorna o config padrão.
    """
    path = get_config_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data: Config = json.load(f)
            if "quick_colors" in data and len(data["quick_colors"]) == 8:
                return data
        except Exception:
            pass
    return get_default_config()


def save_config(config: Config) -> None:
    """
    Persiste o config.json do usuário criando o diretório pai se necessário.
    Não levanta exceção — falhas são silenciosas para não interromper o fluxo
    do usuário.
    """
    path = get_config_path()
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"rgb_config: erro ao salvar config: {e}")


# ---------------------------------------------------------------------------
# Utilitário de conversão de cor (mantido aqui para evitar dependência de GTK)
# ---------------------------------------------------------------------------

def hex_to_rgb(hex_val: Optional[str]) -> tuple[int, int, int]:
    """
    Converte string HEX (#RRGGBB ou #RGB) para tupla (r, g, b) 0-255.
    Retorna (0, 0, 0) para qualquer entrada inválida — nunca levanta exceção.
    """
    fallback = (0, 0, 0)
    if not hex_val:
        return fallback
    try:
        color = hex_val.strip().upper().lstrip("#")
        if len(color) == 3:
            color = color[0] * 2 + color[1] * 2 + color[2] * 2
        if len(color) != 6:
            return fallback
        r = int(color[0:2], 16)
        g = int(color[2:4], 16)
        b = int(color[4:6], 16)
        return (r, g, b)
    except (ValueError, IndexError, AttributeError):
        return fallback
