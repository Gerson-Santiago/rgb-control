#!/usr/bin/env python3
# Pipeline Reference: .agents/workflows/pipeline.md
"""
Script de Bump de Versão Automatizado.
Atualiza referências de versão nos arquivos controlados.
"""
import sys
import re
from pathlib import Path

def get_root() -> Path:
    return Path(__file__).parent.parent

def main():
    root = get_root()
    pyproject_path = root / "pyproject.toml"
    
    if not pyproject_path.exists():
        print("❌ pyproject.toml não encontrado.")
        sys.exit(1)
        
    # Ler a versão atual
    content = pyproject_path.read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
    if not match:
        print("❌ Não foi possível encontrar a versão atual no pyproject.toml")
        sys.exit(1)
    current_version = match.group(1)
    
    # Obter a nova versão
    if len(sys.argv) < 2:
        print(f"Versão atual: {current_version}")
        try:
            new_version = input("Digite a nova versão (ex: 1.1.4): ").strip()
        except KeyboardInterrupt:
            print("\n❌ Cancelado pelo usuário.")
            sys.exit(1)
        if not new_version:
            print("❌ Nenhuma versão fornecida. Abortando.")
            sys.exit(1)
    else:
        new_version = sys.argv[1].strip()
        
    if not re.match(r'^\d+\.\d+\.\d+$', new_version):
        print(f"❌ Versão inválida: '{new_version}'. Deve ser no formato X.Y.Z.")
        sys.exit(1)
        
    if current_version == new_version:
        print(f"ℹ️ A versão já é {new_version}. Nenhuma alteração necessária.")
        sys.exit(0)
        
    print(f"🔄 Atualizando versão de v{current_version} para v{new_version}...")
    
    # 1. pyproject.toml
    pyproject_content = pyproject_path.read_text(encoding="utf-8")
    new_pyproject_content = re.sub(
        rf'^version\s*=\s*"{re.escape(current_version)}"',
        f'version = "{new_version}"',
        pyproject_content,
        flags=re.MULTILINE
    )
    pyproject_path.write_text(new_pyproject_content, encoding="utf-8")
    print("  ✅ pyproject.toml atualizado")
    
    # 2. docs/stack.md
    stack_path = root / "docs" / "stack.md"
    if stack_path.exists():
        content = stack_path.read_text(encoding="utf-8")
        new_content = content.replace(
            f"# Stack Tecnológica e Padrões de Projeto (v{current_version})",
            f"# Stack Tecnológica e Padrões de Projeto (v{new_version})"
        )
        stack_path.write_text(new_content, encoding="utf-8")
        print("  ✅ docs/stack.md atualizado")
        
    # 3. docs/TESTS.md
    tests_path = root / "docs" / "TESTS.md"
    if tests_path.exists():
        content = tests_path.read_text(encoding="utf-8")
        new_content = content.replace(
            f"# Arquitetura de QA Gold Standard (v{current_version})",
            f"# Arquitetura de QA Gold Standard (v{new_version})"
        )
        tests_path.write_text(new_content, encoding="utf-8")
        print("  ✅ docs/TESTS.md atualizado")
        
    # 4. src/rgb_control/main.py
    main_py_path = root / "src" / "rgb_control" / "main.py"
    if main_py_path.exists():
        content = main_py_path.read_text(encoding="utf-8")
        new_content = content.replace(
            f'print("RGB Control v{current_version}")',
            f'print("RGB Control v{new_version}")'
        )
        main_py_path.write_text(new_content, encoding="utf-8")
        print("  ✅ src/rgb_control/main.py atualizado")
        
    # 5. packaging/rgb.sh
    rgb_sh_path = root / "packaging" / "rgb.sh"
    if rgb_sh_path.exists():
        content = rgb_sh_path.read_text(encoding="utf-8")
        new_content = content.replace(
            f'echo "RGB Controller v{current_version}"',
            f'echo "RGB Controller v{new_version}"'
        )
        rgb_sh_path.write_text(new_content, encoding="utf-8")
        print("  ✅ packaging/rgb.sh atualizado")
        
    # 6. README.md
    readme_path = root / "README.md"
    if readme_path.exists():
        content = readme_path.read_text(encoding="utf-8")
        new_content = content.replace(
            f"badge/version-{current_version}-blue",
            f"badge/version-{new_version}-blue"
        ).replace(
            f"Solução profissional (v{current_version})",
            f"Solução profissional (v{new_version})"
        )
        readme_path.write_text(new_content, encoding="utf-8")
        print("  ✅ README.md atualizado")
        
    # 7. scripts/atualizar.sh
    atualizar_path = root / "scripts" / "atualizar.sh"
    if atualizar_path.exists():
        content = atualizar_path.read_text(encoding="utf-8")
        new_content = content.replace(
            f"# Version: {current_version}",
            f"# Version: {new_version}"
        )
        atualizar_path.write_text(new_content, encoding="utf-8")
        print("  ✅ scripts/atualizar.sh atualizado")
        
    print("\n🎉 Bump de versão concluído com sucesso! Execute o build ou run_tests.sh para validar a sincronia.")

if __name__ == "__main__":
    main()
