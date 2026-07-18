/**
 * prefs.js — Painel de Preferências da Extensão RGB Control
 *
 * Responsabilidade única: permitir que o usuário configure as 8 cores de
 * atalho exibidas no painel do GNOME Shell, persistindo em config.json.
 *
 * Roda em processo GTK4 separado (gnome-shell-extension-prefs),
 * sem acesso ao Shell — apenas GJS + GTK4 + Adw.
 */

import { ExtensionPreferences } from 'resource:///org/gnome/Shell/Extensions/js/extensions/prefs.js';
import Adw from 'gi://Adw';
import Gtk from 'gi://Gtk';
import Gio from 'gi://Gio';
import GLib from 'gi://GLib';
import Gdk from 'gi://Gdk';

// ---------------------------------------------------------------------------
// Constantes
// ---------------------------------------------------------------------------

const DEFAULT_COLORS = [
    { name: 'Laranja',  hex: '#FF5500' },
    { name: 'Vermelho', hex: '#FF0000' },
    { name: 'Azul',     hex: '#0000FF' },
    { name: 'Verde',    hex: '#00FF00' },
    { name: 'Ciano',    hex: '#00FFFF' },
    { name: 'Roxo',     hex: '#FF00FF' },
    { name: 'Amarelo',  hex: '#FFFF00' },
    { name: 'Branco',   hex: '#FFFFFF' },
];

// ---------------------------------------------------------------------------
// Helpers de I/O (puro GLib/Gio — sem Python)
// ---------------------------------------------------------------------------

function _getConfigPath() {
    return GLib.build_filenamev([GLib.get_user_config_dir(), 'rgb-control', 'config.json']);
}

function _readColors() {
    const path = _getConfigPath();
    const file = Gio.File.new_for_path(path);
    if (file.query_exists(null)) {
        try {
            const [ok, contents] = file.load_contents(null);
            if (ok) {
                const json = JSON.parse(new TextDecoder('utf-8').decode(contents));
                if (json?.quick_colors?.length === 8) {
                    return json.quick_colors;
                }
            }
        } catch (e) {
            console.error('RGB Control Prefs: erro ao ler config.json:', e);
        }
    }
    return structuredClone(DEFAULT_COLORS);
}

function _saveColors(colors) {
    const path = _getConfigPath();
    const dir = GLib.path_get_dirname(path);
    GLib.mkdir_with_parents(dir, 0o755);

    const data = new TextEncoder().encode(JSON.stringify({ quick_colors: colors }, null, 2));
    const file = Gio.File.new_for_path(path);
    try {
        file.replace_contents(data, null, false, Gio.FileCreateFlags.REPLACE_DESTINATION, null);
    } catch (e) {
        console.error('RGB Control Prefs: erro ao salvar config.json:', e);
    }
}

function _hexFromRgba(rgba) {
    const r = Math.round(rgba.red   * 255).toString(16).padStart(2, '0').toUpperCase();
    const g = Math.round(rgba.green * 255).toString(16).padStart(2, '0').toUpperCase();
    const b = Math.round(rgba.blue  * 255).toString(16).padStart(2, '0').toUpperCase();
    return `#${r}${g}${b}`;
}

const COLOR_NAMES = {
    '#FF5500': 'Laranja',
    '#FF0000': 'Vermelho',
    '#0000FF': 'Azul',
    '#00FF00': 'Verde',
    '#00FFFF': 'Ciano',
    '#FF00FF': 'Roxo',
    '#FFFF00': 'Amarelo',
    '#FFB200': 'Âmbar',
    '#FFFFFF': 'Branco',
    '#000000': 'Desativar',
    '#AA00FF': 'Roxo',
    '#00F2EA': 'Ciano',
};

function _nameFromHex(hex, fallback) {
    return COLOR_NAMES[hex.toUpperCase()] ?? fallback;
}

// ---------------------------------------------------------------------------
// Classe principal
// ---------------------------------------------------------------------------

export default class RgbControlPreferences extends ExtensionPreferences {
    /**
     * Preenche a janela de preferências nativa do GNOME Shell.
     * @param {Adw.PreferencesWindow} window
     */
    fillPreferencesWindow(window) {
        window.set_title('RGB Control — Preferências');
        window.set_default_size(500, 600);

        const page = new Adw.PreferencesPage({
            title: 'Cores de Atalho',
            icon_name: 'preferences-color-symbolic',
        });
        window.add(page);

        const group = new Adw.PreferencesGroup({
            title: 'Cores Rápidas da Extensão',
            description: 'Configure as 8 cores exibidas no painel do GNOME',
        });
        page.add(group);

        const colors = _readColors();

        for (let i = 0; i < 8; i++) {
            const colorData = colors[i];

            const row = new Adw.ActionRow({
                title: `Cor de Atalho ${i + 1}`,
                subtitle: colorData.name,
            });

            const colorDialog = new Gtk.ColorDialog({ modal: true });
            const picker = new Gtk.ColorDialogButton({ dialog: colorDialog });
            picker.set_valign(Gtk.Align.CENTER);

            // Define a cor atual no seletor
            const rgba = new Gdk.RGBA();
            rgba.parse(colorData.hex);
            picker.set_rgba(rgba);

            // Reage a mudanças de cor pelo usuário
            picker.connect('notify::rgba', () => {
                const newRgba = picker.get_rgba();
                const hex = _hexFromRgba(newRgba);
                const name = _nameFromHex(hex, colorData.name);

                // Lê o estado atual, atualiza a entrada e persiste
                const current = _readColors();
                current[i] = { name, hex };
                _saveColors(current);

                row.set_subtitle(name);
            });

            row.add_suffix(picker);
            group.add(row);
        }

        // Rodapé com botão de reset
        const resetGroup = new Adw.PreferencesGroup();
        page.add(resetGroup);

        const resetRow = new Adw.ActionRow({
            title: 'Restaurar Padrões',
            subtitle: 'Volta as 8 cores para a configuração original',
            icon_name: 'edit-undo-symbolic',
        });

        const resetBtn = new Gtk.Button({
            label: 'Restaurar',
            valign: Gtk.Align.CENTER,
            css_classes: ['destructive-action'],
        });

        resetBtn.connect('clicked', () => {
            _saveColors(structuredClone(DEFAULT_COLORS));
            // Fecha e reabre a janela para refletir a mudança
            window.close();
        });

        resetRow.add_suffix(resetBtn);
        resetGroup.add(resetRow);
    }
}
