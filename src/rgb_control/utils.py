import logging
from typing import Optional

logger = logging.getLogger(__name__)

def hex_to_rgba_tuple(hex_val: Optional[str]) -> tuple[int, int, int, float]:
    """
    Converte string HEX (#RRGGBB) para tupla (r, g, b, a) 0-255 e float.
    Garante resiliência total contra inputs malformados ou nulos.
    """
    fallback = (0, 0, 0, 1.0)
    if not hex_val:
        return fallback
        
    try:
        color_str = hex_val.strip().upper()
        if not color_str.startswith("#"):
            color_str = f"#{color_str}"
            
        # Suporte a #RGB curto (ex: #F00 -> #FF0000)
        if len(color_str) == 4:
            r = int(color_str[1] * 2, 16)
            g = int(color_str[2] * 2, 16)
            b = int(color_str[3] * 2, 16)
        elif len(color_str) == 7:
            r = int(color_str[1:3], 16)
            g = int(color_str[3:5], 16)
            b = int(color_str[5:7], 16)
        else:
            raise ValueError("Tamanho de HEX inválido")
            
        return (r, g, b, 1.0)
    except (ValueError, IndexError, AttributeError):
        logger.warning(f"Cor inválida detectada: {hex_val}. Usando fallback Preto.")
        return fallback
