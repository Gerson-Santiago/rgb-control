import logging

logger = logging.getLogger(__name__)

def hex_to_rgba_tuple(hex_val: str) -> tuple[int, int, int]:
    """
    Converte string HEX (#RRGGBB) para tupla (r, g, b) 0-255.
    Garante resiliência contra inputs malformados.
    """
    color_str = hex_val.strip().upper()
    if not color_str.startswith("#"):
        color_str = f"#{color_str}"
        
    try:
        # Suporte a #RGB curto (ex: #F00 -> #FF0000)
        if len(color_str) == 4:
            r = int(color_str[1] * 2, 16)
            g = int(color_str[2] * 2, 16)
            b = int(color_str[3] * 2, 16)
        else:
            r = int(color_str[1:3], 16)
            g = int(color_str[3:5], 16)
            b = int(color_str[5:7], 16)
        return (r, g, b)
    except (ValueError, IndexError):
        logger.warning(f"Cor inválida detectada: {hex_val}. Usando fallback Vermelho.")
        return (255, 0, 0)
