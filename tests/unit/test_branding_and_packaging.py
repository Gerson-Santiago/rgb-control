# Pipeline Reference: run_tests.sh — novos arquivos de teste precisam de `git add` (Gate 0 bloqueia arquivos não rastreados).
import unittest
import os
import re

class TestBrandingAndPackagingConsistency(unittest.TestCase):
    """
    Testes para validar a consistência da identidade visual (logo)
    e a conformidade do empacotamento desktop (pareamento GNOME).
    """

    def setUp(self):
        # Caminho absoluto da raiz do projeto para o teste rodar de qualquer pasta
        self.root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    def test_logo_assets_exist(self):
        """Garante que as imagens de logotipo essenciais existem na pasta de assets."""
        svg_path = os.path.join(self.root_dir, "assets", "logo.svg")
        png_path = os.path.join(self.root_dir, "assets", "logo.png")
        
        self.assertTrue(os.path.exists(svg_path), f"Arquivo ausente: {svg_path}")
        self.assertTrue(os.path.exists(png_path), f"Arquivo ausente: {png_path} (necessário para fallback e build)")

    def test_app_code_uses_svg_logo(self):
        """Garante que o código principal da aplicação referencia o SVG e não o PNG antigo."""
        main_py = os.path.join(self.root_dir, "src", "rgb_control", "main.py")
        window_py = os.path.join(self.root_dir, "src", "rgb_control", "window.py")
        
        with open(main_py, "r", encoding="utf-8") as f:
            main_content = f.read()
        self.assertIn("logo.svg", main_content, "main.py deve referenciar logo.svg no splash screen")
        self.assertNotIn("logo.png", main_content, "main.py não deve referenciar o arquivo logo.png legado")

        with open(window_py, "r", encoding="utf-8") as f:
            window_content = f.read()
        self.assertIn("logo.svg", window_content, "window.py deve referenciar logo.svg no painel principal")
        self.assertNotIn("logo.png", window_content, "window.py não deve referenciar o arquivo logo.png legado")

    def test_desktop_file_and_app_id_alignment(self):
        """
        Garante que o nome do arquivo .desktop gerado no build corresponde exatamente
        ao application_id da classe RgbControlApp, necessário para parear o ícone no GNOME Dock.
        """
        main_py = os.path.join(self.root_dir, "src", "rgb_control", "main.py")
        build_deb_sh = os.path.join(self.root_dir, "build_deb.sh")
        
        with open(main_py, "r", encoding="utf-8") as f:
            main_content = f.read()
            
        # Extrai o application_id configurado no construtor
        app_id_match = re.search(r"application_id:\s*str\s*=\s*'([^']+)'", main_content)
        self.assertTrue(app_id_match, "Não foi possível localizar a declaração de application_id no main.py")
        app_id = app_id_match.group(1)
        
        # O arquivo .desktop esperado deve ter o nome <app_id>.desktop
        expected_desktop_filename = f"{app_id}.desktop"

        with open(build_deb_sh, "r", encoding="utf-8") as f:
            build_content = f.read()
            
        # Verifica se o script de build cria o atalho com o nome esperado
        self.assertIn(expected_desktop_filename, build_content, 
                      f"O build_deb.sh deve gerar o arquivo desktop como '{expected_desktop_filename}' "
                      f"para bater com o ID do aplicativo '{app_id}'")

    def test_desktop_icon_resource_copied(self):
        """Garante que o build_deb.sh copia tanto o ícone SVG quanto o PNG correspondentes ao Icon do .desktop."""
        build_deb_sh = os.path.join(self.root_dir, "build_deb.sh")
        
        with open(build_deb_sh, "r", encoding="utf-8") as f:
            build_content = f.read()
            
        # Extrai a linha de definição do Icon= no arquivo .desktop embutido
        icon_match = re.search(r"Icon=([a-zA-Z0-9_\.-]+)", build_content)
        self.assertTrue(icon_match, "Não foi possível localizar a definição 'Icon=' no arquivo .desktop do build_deb.sh")
        icon_name = icon_match.group(1)
        
        # Verifica se o build cria os caminhos com o nome do ícone
        expected_svg_dest = f"scalable/apps/{icon_name}.svg"
        expected_png_dest = f"256x256/apps/{icon_name}.png"
        
        self.assertIn(expected_svg_dest, build_content, f"O build_deb.sh deve copiar o ícone SVG para '{expected_svg_dest}'")
        self.assertIn(expected_png_dest, build_content, f"O build_deb.sh deve copiar o ícone PNG para '{expected_png_dest}'")

    def test_systemd_service_packaged(self):
        """Garante que o arquivo de serviço do daemon existe e é empacotado no build_deb.sh."""
        service_file = os.path.join(self.root_dir, "packaging", "rgb-control-daemon.service")
        self.assertTrue(os.path.exists(service_file), f"Arquivo de serviço ausente: {service_file}")
        
        build_deb_sh = os.path.join(self.root_dir, "build_deb.sh")
        with open(build_deb_sh, "r", encoding="utf-8") as f:
            build_content = f.read()
            
        self.assertIn("rgb-control-daemon.service", build_content, 
                      "O build_deb.sh deve copiar e gerenciar o serviço rgb-control-daemon.service")
