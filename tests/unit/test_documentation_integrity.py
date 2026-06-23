import os
import subprocess
import sys
from pathlib import Path

# Pipeline Reference: .agents/workflows/pipeline.md

PROJECT_ROOT = Path(__file__).parent.parent.parent

# Lista de 12 arquivos que devem conter o cabeçalho canônico
EXPECTED_FILES = [
    "scripts/pipeline_run.sh",
    "scripts/bump_version.py",
    "scripts/atualizar.sh",
    "scripts/coverage_ratchet.py",
    "scripts/docs_sync_check.py",
    "scripts/install_extension.sh",
    "scripts/linhas_tam.sh",
    "scripts/setup_dev.sh",
    "run_tests.sh",
    "build_deb.sh",
    "packaging/git-hooks/commit-msg",
    "packaging/git-hooks/pre-push",
]

def test_pipeline_reference_headers():
    """Garante que todos os 12 arquivos de scripts/hooks possuam a referência do pipeline no cabeçalho."""
    canonical_header = "# Pipeline Reference: .agents/workflows/pipeline.md"
    
    for relative_path in EXPECTED_FILES:
        path = PROJECT_ROOT / relative_path
        assert path.exists(), f"Arquivo esperado não encontrado: {relative_path}"
        
        content = path.read_text(encoding="utf-8")
        assert canonical_header in content, (
            f"Arquivo '{relative_path}' não contém a referência canônica: '{canonical_header}'"
        )

def test_rule_files_links():
    """Garante que as regras 2, 3 e 4 em .agents/rules/ referenciem o pipeline.md."""
    rules_dir = PROJECT_ROOT / ".agents" / "rules"
    if not rules_dir.exists():
        return
        
    expected_link = "[.agents/workflows/pipeline.md](file:///home/sant/Área de trabalho/PROJETOS/openrgb/.agents/workflows/pipeline.md)"
    
    for rule_name in ["regra2.md", "regra3.md", "regra4.md"]:
        rule_file = rules_dir / rule_name
        content = rule_file.read_text(encoding="utf-8")
        assert expected_link in content, (
            f"Regra '{rule_name}' não referencia o link correto para o pipeline.md: '{expected_link}'"
        )

def test_pipeline_txt_deleted():
    """Garante que o arquivo pipeline.txt foi excluído do repositório."""
    pipeline_txt = PROJECT_ROOT / "scripts" / "pipeline.txt"
    assert not pipeline_txt.exists(), "O arquivo redundante scripts/pipeline.txt ainda existe no repositório."

def test_atualizar_sh_logic():
    """Garante que atualizar.sh usa a lógica dinâmica de detecção de versão e revisão."""
    atualizar_path = PROJECT_ROOT / "scripts" / "atualizar.sh"
    assert atualizar_path.exists()
    
    content = atualizar_path.read_text(encoding="utf-8")
    
    # Valida presença das fontes dinâmicas de dados
    assert "pyproject.toml" in content, "atualizar.sh não faz referência a pyproject.toml para obter versão"
    assert "build_deb.sh" in content, "atualizar.sh não faz referência a build_deb.sh para obter revisão"
    
    # Valida que não há hardcode estático direto do pacote deb compilado
    assert "PACKAGE=" in content
    # Garante que usa expansão de variável (${VERSION} ou similar) e não uma string estática
    assert "${VERSION}" in content or "$VERSION" in content, "atualizar.sh parece ter a versão hardcodada"
    assert "${REV}" in content or "$REV" in content, "atualizar.sh parece ter a revisão hardcodada"

def test_githooks_installation():
    """Valida se os hooks do git estão instalados localmente. Pula a asserção em ambientes de CI."""
    ci_vars = ["CI", "CONTINUOUS_INTEGRATION", "GITHUB_ACTIONS", "GITLAB_CI"]
    is_ci = any(os.environ.get(var) == "true" or os.environ.get(var) == "1" for var in ci_vars)
    
    git_dir = PROJECT_ROOT / ".git"
    
    # Se não houver pasta .git (ex: export de arquivo limpo) ou se estiver rodando no CI
    if is_ci or not git_dir.exists():
        print("\nℹ️ Ambiente de CI ou repositório sem .git. Pulando a checagem de presença de hooks locais.")
        return
        
    # Local: Deve forçar a presença dos hooks configurados pelo setup_dev.sh
    for hook in ["commit-msg", "pre-push"]:
        hook_path = git_dir / "hooks" / hook
        template_path = PROJECT_ROOT / "packaging" / "git-hooks" / hook
        
        assert hook_path.exists(), (
            f"Git hook local '{hook}' não está instalado em .git/hooks/. "
            f"Por favor, execute './scripts/setup_dev.sh' para configurar seu ambiente local."
        )
        
        # Garante que os hooks instalados são idênticos aos templates
        assert hook_path.read_text(encoding="utf-8") == template_path.read_text(encoding="utf-8"), (
            f"Git hook local '{hook}' está desatualizado. Rode './scripts/setup_dev.sh' para atualizar."
        )

def test_setup_dev_sh_unit(tmp_path):
    """Teste unitário isolado do setup_dev.sh usando tmp_path."""
    # Cria a estrutura mock do projeto
    git_hooks_src = tmp_path / "packaging" / "git-hooks"
    git_hooks_src.mkdir(parents=True)
    
    # Grava templates de hooks mock
    (git_hooks_src / "commit-msg").write_text("dummy commit-msg", encoding="utf-8")
    (git_hooks_src / "pre-push").write_text("dummy pre-push", encoding="utf-8")
    
    # Cria pasta .git mock
    git_hooks_dest = tmp_path / ".git" / "hooks"
    git_hooks_dest.mkdir(parents=True)
    
    # Copia o script de setup original para a pasta de scripts mock do tmp_path
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    
    original_setup = PROJECT_ROOT / "scripts" / "setup_dev.sh"
    setup_content = original_setup.read_text(encoding="utf-8")
    
    setup_dest = scripts_dir / "setup_dev.sh"
    setup_dest.write_text(setup_content, encoding="utf-8")
    setup_dest.chmod(0o755)
    
    # Executa o script dentro do tmp_path usando os.system para evitar o mock de subprocess.run
    import os
    old_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        exit_code = os.system(f"bash {setup_dest}")
        assert exit_code == 0, f"setup_dev.sh falhou com código: {exit_code}"
    finally:
        os.chdir(old_cwd)
    
    # Verifica se os arquivos de hook foram copiados
    installed_commit = git_hooks_dest / "commit-msg"
    installed_push = git_hooks_dest / "pre-push"
    
    assert installed_commit.exists(), "commit-msg não copiado pelo setup_dev.sh"
    assert installed_commit.read_text(encoding="utf-8") == "dummy commit-msg"
    
    assert installed_push.exists(), "pre-push não copiado pelo setup_dev.sh"
    assert installed_push.read_text(encoding="utf-8") == "dummy pre-push"
    
    # Verifica permissão executável (+x) no Linux
    assert os.access(installed_commit, os.X_OK)
    assert os.access(installed_push, os.X_OK)


def test_deb_filename_not_in_sync_check():
    """docs_sync_check.py não deve verificar o filename do .deb — isso é responsabilidade do build_deb.sh."""
    content = (PROJECT_ROOT / "scripts" / "docs_sync_check.py").read_text()
    assert "_all.deb" not in content

