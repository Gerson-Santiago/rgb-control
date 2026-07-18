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
 
            // Botão de Configurações no Cabeçalho
            this._settingsBtn = new St.Button({
                style_class: 'rgb-settings-btn',
                reactive: true,
                can_focus: true,
                track_hover: true,
                y_align: Clutter.ActorAlign.CENTER
            });
            this._settingsBtn.set_accessible_name('Configurar Cores');
            
            let settingsIcon = new St.Icon({
                icon_name: 'emblem-system-symbolic',
                style_class: 'rgb-settings-icon',
                style: 'width: 16px; height: 16px; margin: auto;'
            });
            this._settingsBtn.set_child(settingsIcon);
            
            this._settingsBtn.connect('enter-event', () => {
                if (this._titleLabel) {
                    this._titleLabel.set_text('RGB Control (Configurar)');
                }
            });
            this._settingsBtn.connect('leave-event', () => {
                if (this._titleLabel) {
                    this._titleLabel.set_text('RGB Control');
                }
            });
            this._settingsBtn.connect('clicked', () => {
                this._extension.openPreferences();
            });
            headerLayout.add_child(this._settingsBtn);

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
                vertical: true,
                x_expand: true,
                x_align: Clutter.ActorAlign.CENTER
            });
            this._colorsContainerItem.add_child(this._colorsBox);
            this.menu.addMenuItem(this._colorsContainerItem);
            
            this.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());

            // Botão Abrir App Completo
            let openAppItem = new PopupMenu.PopupImageMenuItem('Configurar Cores', 'preferences-color-symbolic');
            openAppItem.connect('activate', () => {
                this._extension.openPreferences();
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
            { name: 'Azul', hex: '#0000FF' },
            { name: 'Verde', hex: '#00FF00' },
            { name: 'Ciano', hex: '#00FFFF' },
            { name: 'Roxo', hex: '#FF00FF' },
            { name: 'Amarelo', hex: '#FFFF00' },
            { name: 'Branco', hex: '#FFFFFF' }
        ];

        let file = Gio.File.new_for_path(this._configPath);
        if (file.query_exists(null)) {
            try {
                let [success, contents] = file.load_contents(null);
                if (success) {
                    let decoder = new TextDecoder('utf-8');
                    let json = JSON.parse(decoder.decode(contents));
                    if (json && json.quick_colors && json.quick_colors.length === 8) {
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
 
        // Criar duas linhas de layout horizontal
        let row1 = new St.BoxLayout({
            style: 'spacing: 12px;',
            vertical: false,
            x_expand: true,
            x_align: Clutter.ActorAlign.CENTER
        });
        let row2 = new St.BoxLayout({
            style: 'spacing: 12px; margin-top: 8px;',
            vertical: false,
            x_expand: true,
            x_align: Clutter.ActorAlign.CENTER
        });
 
        this._colorsBox.add_child(row1);
        this._colorsBox.add_child(row2);
 
        colors.forEach((colorData, index) => {
            let button = this._createColorButton(colorData);
            if (button) {
                if (index < 4) {
                    row1.add_child(button);
                } else {
                    row2.add_child(button);
                }
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
