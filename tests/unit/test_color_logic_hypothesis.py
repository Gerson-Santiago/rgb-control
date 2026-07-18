# Pipeline Reference: run_tests.sh — novos arquivos de teste precisam de `git add` (Gate 0 bloqueia arquivos não rastreados).
import pytest
from hypothesis import given, strategies as st
from rgb_config.config import hex_to_rgb


@given(
    r=st.integers(min_value=0, max_value=255),
    g=st.integers(min_value=0, max_value=255),
    b=st.integers(min_value=0, max_value=255),
)
def test_hex_to_rgb_roundtrip(r: int, g: int, b: int) -> None:
    """Garante que qualquer HEX válido gere exatamente os componentes R, G, B originais."""
    hex_val = f"#{r:02X}{g:02X}{b:02X}"
    res_r, res_g, res_b = hex_to_rgb(hex_val)
    assert (res_r, res_g, res_b) == (r, g, b)


@given(st.text())
def test_hex_to_rgb_resilience(random_text: str) -> None:
    """Garante que NUNCA haja crash independentemente do lixo passado como input."""
    try:
        res = hex_to_rgb(random_text)
        assert len(res) == 3
        for channel in res:
            assert 0 <= channel <= 255
    except Exception as e:
        pytest.fail(f"A função crashou com o input '{random_text}': {e}")
