import RgbControlExtension from './extension.tmp.js';
import Gio from 'gi://Gio';
import GLib from 'gi://GLib';
import system from 'system';
import * as Main from './mocks/main.js';

// Funções utilitárias de asserção
function assertEquals(actual, expected, message) {
    if (actual !== expected) {
        throw new Error(`${message || 'Assertion failed'}: expected ${expected}, got ${actual}`);
    }
}

function assertTrue(actual, message) {
    if (!actual) {
        throw new Error(`${message || 'Assertion failed'}: expected true, got ${actual}`);
    }
}

function runTests() {
    console.log("🧪 Rodando testes JS no GJS...");

    // Caminho da config fake para o teste
    const tempConfigPath = GLib.build_filenamev([GLib.get_tmp_dir(), 'rgb-control-test-config.json']);

    // Deleta config anterior se houver
    let file = Gio.File.new_for_path(tempConfigPath);
    if (file.query_exists(null)) {
        try {
            file.delete(null);
        } catch (e) {
            // Ignora se não conseguir deletar
        }
    }

    const metadata = {
        uuid: 'rgb-control@sant.github.com',
        name: 'RGB Control Quick Settings',
        description: 'Acesso rápido e discreto às cores predefinidas'
    };

    // Instancia a extensão
    const extension = new RgbControlExtension(metadata);
    
    // Antes de ativar, o indicator é nulo/indefinido
    assertEquals(extension._indicator, undefined, "Indicator deve ser indefinido no início");

    // Redireciona o caminho de configuração da extensão para o temporário de testes
    const originalNewForPath = Gio.File.new_for_path;
    Gio.File.new_for_path = function(path) {
        if (path && path.includes('config.json')) {
            return originalNewForPath(tempConfigPath);
        }
        return originalNewForPath(path);
    };

    try {
        // Ativa a extensão
        extension.enable();

        const indicator = extension._indicator;
        assertTrue(indicator !== null && indicator !== undefined, "Indicator deve ser instanciado após enable()");
        assertEquals(Main.panel.statusArea[metadata.uuid], indicator, "Indicator deve ser adicionado ao status area");

        // Mockar comandos de subprocesso para evitar execução real de comandos e testar chamadas
        let colorCommandsRun = [];
        let appCommandsRun = 0;
        indicator._runColorCommand = (hex) => {
            colorCommandsRun.push(hex);
        };
        indicator._runAppCommand = () => {
            appCommandsRun++;
        };

        // 1. Validar carregamento da configuração padrão (quando o arquivo não existe)
        // Cores padrão: Laranja (#FF5500), Vermelho (#FF0000), Azul (#0000FF)
        const buttons = indicator._colorsBox.children;
        assertEquals(buttons.length, 3, "Devem ser criados 3 botões por padrão");
        assertTrue(buttons[0].style.includes('#FF5500'), "Primeiro botão deve ser Laranja");
        assertTrue(buttons[1].style.includes('#FF0000'), "Segundo botão deve ser Vermelho");
        assertTrue(buttons[2].style.includes('#0000FF'), "Terceiro botão deve ser Azul");

        // 2. Testar hover (enter-event / leave-event)
        buttons[0].signals['enter-event']();
        assertEquals(indicator._titleLabel.text, "RGB Control (Laranja)", "Título deve mostrar Laranja no enter-event");

        buttons[0].signals['leave-event']();
        assertEquals(indicator._titleLabel.text, "RGB Control", "Título deve resetar no leave-event");

        // 3. Testar clique em botão de cor rápida
        buttons[0].signals['clicked']();
        assertEquals(colorCommandsRun.length, 1, "Deve rodar o comando de cor");
        assertEquals(colorCommandsRun[0], '#FF5500', "Deve passar a cor laranja");

        // 4. Testar clique no botão moderno de Desligar (Power Button) no cabeçalho
        const powerBtn = indicator._powerBtn;
        assertTrue(powerBtn !== undefined, "Botão power deve ser criado");
        powerBtn.signals['clicked']();
        assertEquals(colorCommandsRun[colorCommandsRun.length - 1], '000000', "Deve rodar o comando de desligar (000000)");

        // 5. Testar clique em "Abrir App Completo"
        const openAppItem = indicator.menu.items.find(item => item.text === 'Abrir App Completo');
        assertTrue(openAppItem !== undefined, "OpenAppItem deve ser criado");
        openAppItem.signals['activate']();
        assertEquals(appCommandsRun, 1, "Deve rodar o comando de abrir app");

        // 6. Testar carregamento de configuração personalizada
        const customConfig = {
            quick_colors: [
                { name: "Verde", hex: "#00FF00" },
                { name: "Amarelo", hex: "#FFFF00" },
                { name: "Ciano", hex: "#00FFFF" }
            ]
        };
        
        // Grava config fake
        GLib.file_set_contents(tempConfigPath, JSON.stringify(customConfig));

        // Chama o recarregamento manual para testar _loadConfig com novo JSON
        indicator._loadConfig();

        const newButtons = indicator._colorsBox.children;
        assertEquals(newButtons.length, 3, "Devem ser criados 3 novos botões");
        assertTrue(newButtons[0].style.includes('#00FF00'), "Novo primeiro botão deve ser Verde");
        assertTrue(newButtons[1].style.includes('#FFFF00'), "Novo segundo botão deve ser Amarelo");
        assertTrue(newButtons[2].style.includes('#00FFFF'), "Novo terceiro botão deve ser Ciano");

        // Testar hover com a nova cor
        newButtons[0].signals['enter-event']();
        assertEquals(indicator._titleLabel.text, "RGB Control (Verde)", "Título deve mostrar Verde no enter-event");
        newButtons[0].signals['leave-event']();

        // Testar clique na nova cor
        newButtons[0].signals['clicked']();
        assertEquals(colorCommandsRun[colorCommandsRun.length - 1], '#00FF00', "Deve rodar o comando com a nova cor verde");

        // 7. Testar comportamento com JSON inválido (deve manter ou reverter para o padrão)
        GLib.file_set_contents(tempConfigPath, "{invalid json}");

        indicator._loadConfig();
        const fallbackButtons = indicator._colorsBox.children;
        assertEquals(fallbackButtons.length, 3, "Deve reverter para 3 botões");
        assertTrue(fallbackButtons[0].style.includes('#FF5500'), "Primeiro botão deve voltar a ser Laranja");

        // 8. Testar desativação da extensão
        extension.disable();
        assertEquals(extension._indicator, null, "Indicator deve ser nulo após disable()");
    } finally {
        // Limpa arquivo temporário de config
        if (file.query_exists(null)) {
            try {
                file.delete(null);
            } catch (e) {
                // Ignora
            }
        }
        // Restaura o Gio.File.new_for_path original
        Gio.File.new_for_path = originalNewForPath;
    }

    console.log("✅ Todos os testes JS passaram com sucesso!");
}

try {
    runTests();
    system.exit(0);
} catch (e) {
    console.error("❌ Falha nos testes GJS:", e);
    console.error(e.stack || e.message || e);
    system.exit(1);
}
