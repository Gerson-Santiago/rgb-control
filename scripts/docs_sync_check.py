#!/usr/bin/env python3
# Pipeline Reference: .agents/workflows/pipeline.md
"""
Validador de Sincronia Documental e Versionamento - Gold Standard QA
Verifica se todos os arquivos com versionamento declaram a mesma versão do pyproject.toml.
"""
import sys
import os
import re
import tomllib
from pathlib import Path

def get_root() -> Path:
    return Path(__file__).parent.parent

def check_file_contains(path: Path, expected: str, desc: str):
    if not path.exists():
        print(f"❌ Arquivo não encontrado: {path} ({desc})")
        sys.exit(1)
        
    content = path.read_text(encoding="utf-8")
    if expected not in content:
        print(f"❌ Descompasso em {path.name} ({desc}): esperava encontrar '{expected}'")
        sys.exit(1)
    print(f"  ✅ {path.name} ({desc}) OK!")

def main():
    root = get_root()
    pyproject_path = root / "pyproject.toml"
    
    if not pyproject_path.exists():
        print("❌ pyproject.toml não encontrado.")
        sys.exit(1)
        
    with open(pyproject_path, "rb") as f:
        toml_data = tomllib.load(f)
        
    version = toml_data.get("project", {}).get("version")
    if not version:
        print("❌ Versão não encontrada no pyproject.toml")
        sys.exit(1)
        
    print(f"🔍 Auditando sincronia de versão para v{version}...")
    
    # 1. docs/stack.md
    check_file_contains(
        root / "docs" / "stack.md",
        f"# Stack Tecnológica e Padrões de Projeto (v{version})",
        "título principal"
    )
    
    # 2. docs/TESTS.md
    check_file_contains(
        root / "docs" / "TESTS.md",
        f"# Arquitetura de QA Gold Standard (v{version})",
        "título principal"
    )
    
    # 3. src/rgb_control/main.py
    check_file_contains(
        root / "src" / "rgb_control" / "main.py",
        f'print("RGB Control v{version}")',
        "flag --version"
    )
    
    # 4. packaging/rgb.sh
    check_file_contains(
        root / "packaging" / "rgb.sh",
        f'echo "RGB Controller v{version}"',
        "flag --version"
    )
    
    # 5. README.md
    check_file_contains(
        root / "README.md",
        f"badge/version-{version}-blue",
        "badge de versão"
    )

    check_file_contains(
        root / "README.md",
        f"Solução profissional (v{version})",
        "introdução vX.Y.Z"
    )
    
    # 6. scripts/atualizar.sh
    check_file_contains(
        root / "scripts" / "atualizar.sh",
        f"# Version: {version}",
        "comentário de versão"
    )
    
    print("🚀 Sincronia de versão OK em todos os arquivos!")

if __name__ == "__main__":
    main()
