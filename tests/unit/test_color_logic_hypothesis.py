import pytest
from hypothesis import given, strategies as st
from rgb_control.utils import hex_to_rgba_tuple

@given(
    r=st.integers(min_value=0, max_value=255),
    g=st.integers(min_value=0, max_value=255),
    b=st.integers(min_value=0, max_value=255)
)
def test_hex_to_rgba_tuple_roundtrip(r, g, b):
    """Garante que qualquer HEX válido gere exatamente os componentes R, G, B originais."""
    hex_val = f"#{r:02X}{g:02X}{b:02X}"
    res_r, res_g, res_b = hex_to_rgba_tuple(hex_val)
    assert (res_r, res_g, res_b) == (r, g, b)

@given(st.text())
def test_hex_to_rgba_tuple_resilience(random_text):
    """Garante que NUNCA haja crash (Exception) independentemente do lixo passado como input."""
    # A função deve retornar o fallback (255, 0, 0) para qualquer entrada inválida
    try:
        res = hex_to_rgba_tuple(random_text)
        assert len(res) == 3
        for val in res:
            assert 0 <= val <= 255
    except Exception as e:
        pytest.fail(f"A função crashou com o input '{random_text}': {e}")

def test_hex_short_form_conversion():
    """Garante suporte a formato curto #F00 -> (255, 0, 0)."""
    assert hex_to_rgba_tuple("#F00") == (255, 0, 0)
    assert hex_to_rgba_tuple("#0F0") == (0, 255, 0)
    assert hex_to_rgba_tuple("#00F") == (0, 0, 255)

def test_hex_lowercase_resilience():
    """Garante que HEX em minúsculo seja tratado corretamente."""
    assert hex_to_rgba_tuple("#ff0000") == (255, 0, 0)
    assert hex_to_rgba_tuple("aabbcc") == (170, 187, 204)
