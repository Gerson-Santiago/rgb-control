import os
from typing import Any
import gi  # type: ignore[import-untyped]
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gdk  # type: ignore[import-untyped]
from rgb_control.backend import Backend


class LogViewerWindow(Adw.Window): # type: ignore[misc]
    def __init__(self, parent: Gtk.Window, backend: Backend) -> None:
        super().__init__(transient_for=parent, modal=False)
        self.set_title("Visualizador de Logs")
        self.set_default_size(650, 500)
        self.backend = backend
        
        # Conteúdo principal
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_content(box)
        
        # HeaderBar do modal
        header = Adw.HeaderBar()
        header.set_show_back_button(False)
        box.append(header)
        
        # Barra de ferramentas para controles
        control_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        control_bar.set_margin_start(12)
        control_bar.set_margin_end(12)
        control_bar.set_margin_top(8)
        control_bar.set_margin_bottom(8)
        
        # Rótulo para indicar o arquivo exibido
        self.lbl_title = Gtk.Label(label="Log do Aplicativo (GUI)")
        self.lbl_title.add_css_class("dim-label")
        control_bar.append(self.lbl_title)
        
        # Espaçador
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        control_bar.append(spacer)
        
        # Botão Atualizar
        self.btn_refresh = Gtk.Button()
        self.btn_refresh.set_icon_name("view-refresh-symbolic")
        self.btn_refresh.set_tooltip_text("Atualizar logs")
        self.btn_refresh.connect("clicked", lambda b: self.refresh_logs())
        control_bar.append(self.btn_refresh)
        
        # Botão Copiar
        self.btn_copy = Gtk.Button()
        self.btn_copy.set_icon_name("edit-copy-symbolic")
        self.btn_copy.set_tooltip_text("Copiar para a área de transferência")
        self.btn_copy.connect("clicked", self.on_copy_clicked)
        control_bar.append(self.btn_copy)
        
        # Botão Limpar
        self.btn_clear = Gtk.Button()
        self.btn_clear.set_icon_name("user-trash-symbolic")
        self.btn_clear.set_tooltip_text("Limpar logs do arquivo")
        self.btn_clear.add_css_class("destructive-action")
        self.btn_clear.connect("clicked", self.on_clear_clicked)
        control_bar.append(self.btn_clear)
        
        box.append(control_bar)
        
        # TextView para exibição
        self.scrolled = Gtk.ScrolledWindow()
        self.scrolled.set_vexpand(True)
        self.scrolled.set_hexpand(True)
        self.scrolled.set_margin_start(12)
        self.scrolled.set_margin_end(12)
        self.scrolled.set_margin_bottom(12)
        self.scrolled.add_css_class("card")
        
        self.text_view = Gtk.TextView()
        self.text_view.set_editable(False)
        self.text_view.set_monospace(True)
        self.text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.text_view.set_margin_top(8)
        self.text_view.set_margin_bottom(8)
        self.text_view.set_margin_start(8)
        self.text_view.set_margin_end(8)
        
        self.scrolled.set_child(self.text_view)
        box.append(self.scrolled)
        
        # Carregar logs
        self.refresh_logs()
        
        # Conectar sinal de fechamento para limpar o timeout
        self.connect("destroy", self.on_destroy)
        
        # Iniciar auto-refresh a cada 1.5s
        self._refresh_timeout_id = GLib.timeout_add(1500, self.auto_refresh_logs)
        
    def get_selected_log_path(self) -> str:
        return self.backend.get_gui_log_path()

    def refresh_logs(self) -> None:
        path = self.get_selected_log_path()
        content = self.backend.read_log_file(path)
        
        buffer = self.text_view.get_buffer()
        buffer.set_text(content)
        
        # Rolar para o fim após o GTK renderizar
        GLib.idle_add(self.scroll_to_bottom)

    def scroll_to_bottom(self) -> bool:
        adj = self.scrolled.get_vadjustment()
        adj.set_value(adj.get_upper() - adj.get_page_size())
        return False



    def on_copy_clicked(self, button: Gtk.Button) -> None:
        buffer = self.text_view.get_buffer()
        start, end = buffer.get_bounds()
        text = buffer.get_text(start, end, True)
        
        clipboard = Gdk.Display.get_default().get_clipboard()
        clipboard.set_text(text)
        
        # Feedback visual
        button.set_icon_name("object-select-symbolic")
        GLib.timeout_add(1000, lambda: button.set_icon_name("edit-copy-symbolic") or False)

    def on_clear_clicked(self, button: Gtk.Button) -> None:
        dialog = Adw.MessageDialog(
            transient_for=self,
            heading="Limpar Logs",
            body="Tem certeza que deseja apagar todo o conteúdo deste arquivo de log? Esta operação não pode ser desfeita."
        )
        dialog.add_response("cancel", "Cancelar")
        dialog.add_response("clear", "Limpar")
        dialog.set_response_appearance("clear", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("cancel")
        dialog.set_close_attempt_response_id("cancel")
        
        def on_response(d: Adw.MessageDialog, response_id: str) -> None:
            if response_id == "clear":
                path = self.get_selected_log_path()
                self.backend.clear_log_file(path)
                self.refresh_logs()
            d.destroy()
            
        dialog.connect("response", on_response)
        dialog.present()

    def on_destroy(self, widget: Any) -> None:
        if hasattr(self, '_refresh_timeout_id') and self._refresh_timeout_id:
            GLib.source_remove(self._refresh_timeout_id)
            self._refresh_timeout_id = None

    def auto_refresh_logs(self) -> bool:
        if not self.get_visible() and not os.environ.get("PYTEST_CURRENT_TEST"):
            return False
            
        path = self.get_selected_log_path()
        content = self.backend.read_log_file(path)
        
        buffer = self.text_view.get_buffer()
        start, end = buffer.get_bounds()
        current_text = buffer.get_text(start, end, True)
        
        if content != current_text:
            adj = self.scrolled.get_vadjustment()
            is_at_bottom = adj.get_value() >= (adj.get_upper() - adj.get_page_size() - 10)
            
            buffer.set_text(content)
            
            if is_at_bottom:
                GLib.idle_add(self.scroll_to_bottom)
                
        return True
