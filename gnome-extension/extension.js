import { Extension } from 'resource:///org/gnome/shell/extensions/extension.js';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import * as PanelMenu from 'resource:///org/gnome/shell/ui/panelMenu.js';
import * as PopupMenu from 'resource:///org/gnome/shell/ui/popupMenu.js';
import St from 'gi://St';
import Gio from 'gi://Gio';
import GLib from 'gi://GLib';
import Clutter from 'gi://Clutter';
import GObject from 'gi://GObject';

const ExtensionUtils = imports.misc.extensionUtils;

const RgbControlIndicator = GObject.registerClass(
class RgbControlIndicator extends PanelMenu.Button {
    _init(extension) {
        super._init(0.0, 'RGB Control Indicator', false);
        this._extension = extension;

        // Criar o ícone discreto no painel
        this._icon = new St.Icon({
            icon_name: 'lightbulb-symbolic',
            icon_type: St.IconType.SYMBOLIC,
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

    _createMenu() {
        // Título/Cabeçalho do menu
        let titleItem = new PopupMenu.PopupMenuItem('RGB Control', { reactive: false });
        this.menu.addMenuItem(titleItem);
        this.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());

        // Seção para botões de cores rápidas (Layout Horizontal)
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

        // Botão Desligar LEDs
        let turnOffItem = new PopupMenu.PopupImageMenuItem('Desligar LEDs', 'display-brightness-off-symbolic');
        turnOffItem.connect('activate', () => {
            this._runColorCommand('000000');
        });
        this.menu.addMenuItem(turnOffItem);

        // Botão Abrir App Completo
        let openAppItem = new PopupMenu.PopupImageMenuItem('Abrir App Completo', 'preferences-system-symbolic');
        openAppItem.connect('activate', () => {
            this._runAppCommand();
        });
        this.menu.addMenuItem(openAppItem);
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

        // Adicionar novos botões circulares coloridos
        colors.forEach(colorData => {
            // Cria um botão estilizado como círculo com borda e sombra
            let button = new St.Button({
                style: `background-color: ${colorData.hex}; width: 40px; height: 40px; border-radius: 20px; border: 2px solid rgba(255,255,255,0.25); box-shadow: 0 2px 4px rgba(0,0,0,0.2);`,
                reactive: true,
                can_focus: true,
                track_hover: true
            });
            button.set_tooltip_text(colorData.name);

            button.connect('clicked', () => {
                this._runColorCommand(colorData.hex);
            });

            this._colorsBox.add_child(button);
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
