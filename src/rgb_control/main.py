import sys
import gi
import os
import traceback
import logging

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, Gio, GLib, Gdk

log_dir = os.path.join(GLib.get_user_cache_dir(), "rgb-control")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "app.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(log_file), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

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
            filename = get_asset_path("logo.svg")
            picture = Gtk.Picture.new_for_filename(filename)
            picture.set_content_fit(Gtk.ContentFit.CONTAIN)
            picture.set_size_request(120, 120)
            picture.add_css_class("splash-logo")
            
            center_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            center_box.set_halign(Gtk.Align.CENTER)
            center_box.set_valign(Gtk.Align.CENTER)
            center_box.set_vexpand(True)
            center_box.append(picture)
            
            box.append(center_box)
        except Exception:
            label = Gtk.Label(label="Carregando RGB Control...")
            label.set_margin_top(50)
            box.append(label)
        
        self.set_child(box)
        self.on_ready = on_ready_callback
        
        # Display splash for 2.5 seconds
        GLib.timeout_add(2500, self._finish_splash)

    def _finish_splash(self):
        try:
            self.on_ready()
            self.destroy()
        except Exception as e:
            err = traceback.format_exc()
            logger.critical(f"CRITICAL CRASH ON UI INIT:\n{err}")
            with open("/tmp/rgb_crash.txt", "w") as f:
                f.write(err)
            self.destroy()
        return False

class RgbControlApp(Adw.Application):
    def __init__(self):
        super().__init__(
            application_id='com.github.sant.rgbcontrol', 
            flags=Gio.ApplicationFlags.FLAGS_NONE
        )

    def do_activate(self):
        if self.get_windows():
            self.get_windows()[0].present()
            return

        # Load external CSS for the whole app
        css_path = get_asset_path("rgb_control/style.css")
        if not os.path.exists(css_path):
            css_path = get_asset_path("style.css")
            
        if os.path.exists(css_path):
            provider = Gtk.CssProvider()
            provider.load_from_path(css_path)
            Gtk.StyleContext.add_provider_for_display(
                Gdk.Display.get_default(),
                provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )

        # Show splash first
        splash = SplashWindow(self, self.on_splash_finished)
        splash.present()

    def on_splash_finished(self):
        win = MainWindow(application=self)
        win.present()

def main():
    import sys
    if "--version" in sys.argv:
        print("RGB Control v1.0.5")
        return 0
    logger.info("Iniciando RGB Control App...")
    app = RgbControlApp()
    return app.run([sys.argv[0]])

if __name__ == '__main__':
    sys.exit(main())
