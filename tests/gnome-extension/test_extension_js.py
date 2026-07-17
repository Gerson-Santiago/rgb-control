import unittest
import os
import json
import subprocess

class TestGnomeExtensionIntegration(unittest.TestCase):
    """
    Suite de testes que valida a extensão do GNOME Shell (extension.js)
    rodando-a no interpretador GJS nativo com mocks, além de garantir
    a consistência dos arquivos de empacotamento da extensão.
    """
    
    def setUp(self):
        self.root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.extension_dir = os.path.join(self.root_dir, "gnome-extension")
        self.test_dir = os.path.join(self.root_dir, "tests", "gnome-extension")
        
        self.orig_extension_js = os.path.join(self.extension_dir, "extension.js")
        self.tmp_extension_js = os.path.join(self.test_dir, "extension.tmp.js")
        
        # Garante a limpeza de execuções anteriores abortadas
        if os.path.exists(self.tmp_extension_js):
            try:
                os.remove(self.tmp_extension_js)
            except OSError:
                pass
            
    def tearDown(self):
        if os.path.exists(self.tmp_extension_js):
            try:
                os.remove(self.tmp_extension_js)
            except OSError:
                pass

    def test_gnome_extension_static_files(self):
        """Verifica a consistência e a presença dos arquivos estáticos da extensão."""
        # 1. Verificar se os arquivos fundamentais existem
        metadata_path = os.path.join(self.extension_dir, "metadata.json")
        stylesheet_path = os.path.join(self.extension_dir, "stylesheet.css")
        icon_path = os.path.join(self.extension_dir, "icon.svg")
        
        self.assertTrue(os.path.exists(metadata_path), "metadata.json da extensão ausente")
        self.assertTrue(os.path.exists(stylesheet_path), "stylesheet.css da extensão ausente")
        self.assertTrue(os.path.exists(icon_path), "icon.svg da extensão ausente")
        
        # 2. Validar conteúdo do metadata.json
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
            
        self.assertEqual(metadata.get("uuid"), "rgb-control@sant.github.com", "UUID da extensão incorreto")
        self.assertEqual(metadata.get("name"), "RGB Control Quick Settings", "Nome da extensão incorreto")
        self.assertIn("shell-version", metadata, "Versões do GNOME Shell suportadas devem ser declaradas")
        self.assertTrue(len(metadata["shell-version"]) > 0, "Lista de shell-version não deve ser vazia")
        
        # 3. Validar se o UUID no build_deb.sh coincide com o do metadata.json
        build_deb_path = os.path.join(self.root_dir, "build_deb.sh")
        with open(build_deb_path, "r", encoding="utf-8") as f:
            build_content = f.read()
            
        expected_dir = f"extensions/{metadata['uuid']}"
        self.assertIn(expected_dir, build_content, 
                      f"O build_deb.sh deve copiar a extensão para a pasta correta baseada no UUID ({expected_dir})")

    def test_gnome_extension_gjs_logic(self):
        """Prepara a extensão com imports mockados e executa os testes lógicos no GJS."""
        # 1. Ler o extension.js original
        with open(self.orig_extension_js, "r", encoding="utf-8") as f:
            js_content = f.read()
            
        # 2. Substituir imports reais do Gnome Shell pelos caminhos de mock local
        replacements = {
            "resource:///org/gnome/shell/extensions/extension.js": "./mocks/extension.js",
            "resource:///org/gnome/shell/ui/main.js": "./mocks/main.js",
            "resource:///org/gnome/shell/ui/panelMenu.js": "./mocks/panelMenu.js",
            "resource:///org/gnome/shell/ui/popupMenu.js": "./mocks/popupMenu.js",
            "gi://St": "./mocks/St.js",
            "gi://Clutter": "./mocks/Clutter.js"
        }
        
        modified_content = js_content
        for orig, mock in replacements.items():
            modified_content = modified_content.replace(f"'{orig}'", f"'{mock}'")
            modified_content = modified_content.replace(f'"{orig}"', f'"{mock}"')
            
        # 3. Salvar o arquivo temporário
        with open(self.tmp_extension_js, "w", encoding="utf-8") as f:
            f.write(modified_content)
            
        # 4. Executar os testes via interpretador GJS
        test_runner_path = os.path.join(self.test_dir, "run_gjs_tests.js")
        
        # Rodar o processo na pasta test_dir para resolver imports relativos corretamente
        result = subprocess.run(
            ["gjs", test_runner_path],
            cwd=self.test_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Logar a saída se falhar
        if result.returncode != 0:
            print("\n--- GJS Test Execution Failure ---")
            print("STDOUT:")
            print(result.stdout)
            print("STDERR:")
            print(result.stderr)
            print("----------------------------------")
            
        self.assertEqual(result.returncode, 0, f"GJS testes falharam com código {result.returncode}")
