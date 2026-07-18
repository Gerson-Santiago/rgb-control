import { Extension } from 'resource:///org/gnome/shell/extensions/extension.js';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import * as PanelMenu from 'resource:///org/gnome/shell/ui/panelMenu.js';
import * as PopupMenu from 'resource:///org/gnome/shell/ui/popupMenu.js';
import St from 'gi://St';
import Gio from 'gi://Gio';
import GLib from 'gi://GLib';
import Clutter from 'gi://Clutter';
import GObject from 'gi://GObject';

const RgbControlIndicator = GObject.registerClass(
class RgbControlIndicator extends PanelMenu.Button {
    _init(extension) {
        super._init(0.0, 'RGB Control Indicator', false);
        this._extension = extension;

        // Criar o ícone discreto no painel
        this._icon = new St.Icon({
            icon_name: 'lightbulb-symbolic',
            style_class: 'system-status-icon'
        });
        this.add_child(this._icon);

        // Criar o menu popup
        this._createMenu();
        
        // Caminho do arquivo de configuração
        this._configPath = GLib.build_filenamev([GLib.get_user_config_dir(), 'rgb-control', 'config.json']);
        
        // Carregar configurações e monitorar mudanças
        this._loadConfig();
        this._setupConfigMonitor();
    }

    _createColorButton(colorData) {
        try {
            const hexColor = colorData.hex.startsWith('#') ? colorData.hex : `#${colorData.hex}`;
            let button = new St.Button({
                style_class: 'rgb-color-btn',
                style: `background-color: ${hexColor};`,
                reactive: true,
                can_focus: true,
                track_hover: true
            });

            // Acessibilidade (Leitores de tela)
            try {
                button.set_accessible_name(colorData.name);
            } catch (e) {
                console.warn('RGB Control Extension: Erro ao definir accessible_name', e);
            }

            // Feedback visual dinâmico no título do menu ao passar o mouse (hover)
            button.connect('enter-event', () => {
                if (this._titleLabel) {
                    this._titleLabel.set_text(`RGB Control (${colorData.name})`);
                }
            });

            button.connect('leave-event', () => {
                if (this._titleLabel) {
                    this._titleLabel.set_text('RGB Control');
                }
            });

            button.connect('clicked', () => {
                this._runColorCommand(hexColor);
            });

            return button;
        } catch (err) {
            logError(err, 'RGB Control Extension: Erro ao instanciar botão de cor');
            return null;
        }
    }

    _createMenu() {
        try {
            // Cabeçalho Customizado (Layout Horizontal)
            let headerItem = new PopupMenu.PopupBaseMenuItem({ reactive: false });
            headerItem.add_style_class_name('rgb-header-box');
            
            let headerLayout = new St.BoxLayout({
                vertical: false,
                x_expand: true
            });

            this._titleLabel = new St.Label({
                text: 'RGB Control',
                style_class: 'rgb-header-title',
                y_align: Clutter.ActorAlign.CENTER,
                x_expand: true
            });
            headerLayout.add_child(this._titleLabel);

            // Botão Liga/Desligar Moderno no Cabeçalho
            this._powerBtn = new St.Button({
                style_class: 'rgb-power-btn',
                reactive: true,
                can_focus: true,
                track_hover: true,
                y_align: Clutter.ActorAlign.CENTER
            });
            this._powerBtn.set_accessible_name('Desligar LEDs');
            
            let powerIcon = new St.Icon({
                icon_name: 'system-shutdown-symbolic',
                style_class: 'rgb-power-icon',
                style: 'width: 16px; height: 16px; margin: auto;'
            });
            this._powerBtn.set_child(powerIcon);
            
            this._powerBtn.connect('enter-event', () => {
                if (this._titleLabel) {
                    this._titleLabel.set_text('RGB Control (Desligar)');
                }
            });
            this._powerBtn.connect('leave-event', () => {
                if (this._titleLabel) {
                    this._titleLabel.set_text('RGB Control');
                }
            });
            this._powerBtn.connect('clicked', () => {
                this._runColorCommand('000000');
            });

            headerLayout.add_child(this._powerBtn);
            headerItem.add_child(headerLayout);
            this.menu.addMenuItem(headerItem);

            this.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());

            // Título Seção: Cores Rápidas
            let quickLabelItem = new PopupMenu.PopupBaseMenuItem({ reactive: false });
            quickLabelItem.add_child(new St.Label({
                text: 'Cores Rápidas (Configuradas)',
                style_class: 'rgb-section-label'
            }));
            this.menu.addMenuItem(quickLabelItem);

            // Container para botões de cores rápidas (Layout Horizontal)
            this._colorsContainerItem = new PopupMenu.PopupBaseMenuItem({ reactive: false });
            this._colorsBox = new St.BoxLayout({
                style: 'spacing: 12px; padding: 6px 12px;',
                vertical: false,
                x_expand: true,
                x_align: Clutter.ActorAlign.CENTER
            });
            this._colorsContainerItem.add_child(this._colorsBox);
            this.menu.addMenuItem(this._colorsContainerItem);
            
            this.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());

            // Título Seção: Cores Predefinidas (MAIS CORES)
            let presetLabelItem = new PopupMenu.PopupBaseMenuItem({ reactive: false });
            presetLabelItem.add_child(new St.Label({
                text: 'Paleta Estendida (Presets)',
                style_class: 'rgb-section-label'
            }));
            this.menu.addMenuItem(presetLabelItem);

            // Container para botões de cores predefinidas
            this._presetsContainerItem = new PopupMenu.PopupBaseMenuItem({ reactive: false });
            this._presetsBox = new St.BoxLayout({
                style: 'spacing: 12px; padding: 6px 12px;',
                vertical: false,
                x_expand: true,
                x_align: Clutter.ActorAlign.CENTER
            });
            
            // Adicionar cores predefinidas estéticas (MAIS CORES)
            const presetColors = [
                { name: 'Verde', hex: '#00FF00' },
                { name: 'Ciano', hex: '#00FFFF' },
                { name: 'Roxo', hex: '#FF00FF' },
                { name: 'Amarelo', hex: '#FFFF00' },
                { name: 'Branco', hex: '#FFFFFF' }
            ];
            
            presetColors.forEach(colorData => {
                let button = this._createColorButton(colorData);
                if (button) {
                    this._presetsBox.add_child(button);
                }
            });

            this._presetsContainerItem.add_child(this._presetsBox);
            this.menu.addMenuItem(this._presetsContainerItem);

            this.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());

            // Botão Abrir App Completo
            let openAppItem = new PopupMenu.PopupImageMenuItem('Abrir App Completo', 'preferences-system-symbolic');
            openAppItem.connect('activate', () => {
                this._runAppCommand();
            });
            this.menu.addMenuItem(openAppItem);
        } catch (e) {
            logError(e, 'RGB Control Extension: Erro ao inicializar layout do menu');
        }
    }

    _loadConfig() {
        let colors = [
            { name: 'Laranja', hex: '#FF5500' },
            { name: 'Vermelho', hex: '#FF0000' },
            { name: 'Azul', hex: '#0000FF' }
        ];

        let file = Gio.File.new_for_path(this._configPath);
        if (file.query_exists(null)) {
            try {
                let [success, contents] = file.load_contents(null);
                if (success) {
                    let decoder = new TextDecoder('utf-8');
                    let json = JSON.parse(decoder.decode(contents));
                    if (json && json.quick_colors && json.quick_colors.length === 3) {
                        colors = json.quick_colors;
                    }
                }
            } catch (e) {
                console.error('RGB Control Extension: Erro ao ler config.json', e);
            }
        }
        
        this._updateQuickColorButtons(colors);
    }

    _updateQuickColorButtons(colors) {
        // Limpar botões antigos
        this._colorsBox.destroy_all_children();

        // Reconstruir botões com a nova lógica DRY
        colors.forEach(colorData => {
            let button = this._createColorButton(colorData);
            if (button) {
                this._colorsBox.add_child(button);
            }
        });
    }

    _setupConfigMonitor() {
        let file = Gio.File.new_for_path(this._configPath);
        let parentDir = file.get_parent();

        if (!parentDir.query_exists(null)) {
            try {
                parentDir.make_directory_with_parents(null);
            } catch (e) {
                console.error('RGB Control Extension: Erro ao criar diretório pai', e);
            }
        }

        try {
            this._monitor = parentDir.monitor_directory(Gio.FileMonitorFlags.NONE, null);
            this._monitorId = this._monitor.connect('changed', (mon, changedFile, other, eventType) => {
                if (changedFile && changedFile.get_path() === this._configPath &&
                    (eventType === Gio.FileMonitorEvent.CHANGED || eventType === Gio.FileMonitorEvent.CREATED || eventType === Gio.FileMonitorEvent.CHANGES_DONE_HINT)) {
                    this._loadConfig();
                }
            });
        } catch (e) {
            console.error('RGB Control Extension: Erro ao registrar file monitor', e);
        }
    }

    _runColorCommand(hex) {
        let cleanHex = hex.replace('#', '');
        try {
            let proc = new Gio.Subprocess({
                argv: ['/usr/bin/rgb.sh', cleanHex],
                flags: Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_PIPE,
            });
            proc.init(null);
            proc.wait_async(null, (source, res) => {
                try {
                    proc.wait_finish(res);
                } catch (e) {
                    log('RGB Control Extension: rgb.sh failed: ' + e);
                }
            });
        } catch (e) {
            log('RGB Control Extension: Erro ao rodar rgb.sh: ' + e);
        }
    }

    _runAppCommand() {
        try {
            let proc = new Gio.Subprocess({
                argv: ['/usr/bin/rgb-control'],
                flags: Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_PIPE,
            });
            proc.init(null);
            proc.wait_async(null, (source, res) => {
                try {
                    proc.wait_finish(res);
                } catch (e) {
                    log('RGB Control Extension: rgb-control failed: ' + e);
                }
            });
        } catch (e) {
            log('RGB Control Extension: Erro ao rodar rgb-control: ' + e);
        }
    }

    destroy() {
        if (this._monitor) {
            if (this._monitorId) {
                this._monitor.disconnect(this._monitorId);
            }
            this._monitor.cancel();
            this._monitor = null;
        }
        super.destroy();
    }
});

export default class RgbControlExtension extends Extension {
    enable() {
        this._indicator = new RgbControlIndicator(this);
        Main.panel.addToStatusArea(this.uuid, this._indicator);
    }

    disable() {
        if (this._indicator) {
            this._indicator.destroy();
            this._indicator = null;
        }
    }
}
