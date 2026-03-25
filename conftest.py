# conftest.py — configuração global do pytest
# Adiciona o diretório raiz do projeto ao sys.path
# para que 'import mvp' funcione nos testes (e o type checker resolva o módulo)
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
