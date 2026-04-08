#!/usr/bin/env python3
"""
Validador de Sincronia Documental - Gold Standard QA
Verifica se docs/stack.md reflete fielmente o pyproject.toml.
"""
import sys
import os
import re
import tomllib
from pathlib import Path

def get_root() -> Path:
    return Path(__file__).parent.parent

def check_version(toml_data: dict, stack_content: str):
    version = toml_data.get("project", {}).get("version")
    if not version:
        print("❌ Versão não encontrada no pyproject.toml")
        sys.exit(1)
    
    # Procura por (vX.X.X) ou vX.X.X no stack.md (primeira linha ou cabeçalho)
    match = re.search(r"v(?P<version>\d+\.\d+\.\d+)", stack_content)
    if not match:
        print("❌ Versão não encontrada no docs/stack.md")
        sys.exit(1)
    
    stack_version = match.group("version")
    if stack_version != version:
        print(f"❌ Descompasso de Versão: pyproject({version}) != stack.md({stack_version})")
        sys.exit(1)
    
    print(f"✅ Versões Sincronizadas: v{version}")

def check_dependencies(toml_data: dict, stack_content: str):
    # Opcional: Validar se deps de runtime estão no stack.md
    # Como as deps no .deb são listadas manualmente no build_deb.sh,
    # aqui buscamos validações de integridade básica.
    pass

def main():
    root = get_root()
    pyproject_path = root / "pyproject.toml"
    stack_path = root / "docs" / "stack.md"

    if not pyproject_path.exists() or not stack_path.exists():
        print("❌ Arquivos de configuração não encontrados.")
        sys.exit(1)

    with open(pyproject_path, "rb") as f:
        toml_data = tomllib.load(f)

    with open(stack_path, "r", encoding="utf-8") as f:
        stack_content = f.read()

    print("🔍 Auditando sincronia documental...")
    check_version(toml_data, stack_content)
    # check_dependencies(toml_data, stack_content)
    
    print("🚀 Sincronia de documentação OK!")

if __name__ == "__main__":
    main()
