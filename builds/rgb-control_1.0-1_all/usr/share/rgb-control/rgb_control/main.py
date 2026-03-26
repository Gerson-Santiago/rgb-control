import sys
import gi
import os

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, Gio, GLib

try:
    from rgb_control.window import MainWindow, get_asset_path
except ImportError:
    from window import MainWindow, get_asset_path

class SplashWindow(Gtk.Window):
    def __init__(self, application, on_ready_callback):
        super().__init__(application=application)
        self.set_title("Loading RGB Control...")
        self.set_default_size(400, 300)
        self.set_decorated(False)
        self.set_resizable(False)
        
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        try:
            filename = get_asset_path("544bd05c31a56c8347682a790975c619.gif")
            picture = Gtk.Picture.new_for_filename(filename)
            picture.set_content_fit(Gtk.ContentFit.CONTAIN)
            box.append(picture)
        except Exception:
            label = Gtk.Label(label="Carregando RGB Control...")
            label.set_margin_top(50)
            box.append(label)
        
        self.set_child(box)
        self.on_ready = on_ready_callback
        
        # Display splash for 2.5 seconds
        GLib.timeout_add(2500, self._finish_splash)

    def _finish_splash(self):
        self.destroy()
        self.on_ready()
        return False

class RgbControlApp(Adw.Application):
    def __init__(self):
        super().__init__(
            application_id='com.github.sant.rgbcontrol', 
            flags=Gio.ApplicationFlags.FLAGS_NONE
        )

    def do_activate(self):
        # Show splash first
        splash = SplashWindow(self, self.on_splash_finished)
        splash.present()

    def on_splash_finished(self):
        win = self.props.active_window
        if not win or isinstance(win, SplashWindow):
            win = MainWindow(application=self)
        win.present()

def main():
    app = RgbControlApp()
    return app.run(sys.argv)

if __name__ == '__main__':
    sys.exit(main())
