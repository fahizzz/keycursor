import threading
import time

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GLib


class TopBarIndicator:
    """Visual indicator at top of screen"""
    def __init__(self):
        self.window = None
        self.visible = False
        self.gtk_ready = False
        self.acceleration_enabled = True
        self.precision_mode = False
        
        self.gtk_thread = threading.Thread(target=self._run_gtk, daemon=True)
        self.gtk_thread.start()
        
        timeout = 0
        while not self.gtk_ready and timeout < 20:
            time.sleep(0.02)
            timeout += 1
        
        if self.gtk_ready:
            time.sleep(0.05)
    
    def show(self):
        if self.window and not self.visible:
            GLib.idle_add(self._do_show)
            self.visible = True
    
    def hide(self):
        if self.window and self.visible:
            GLib.idle_add(self._do_hide)
            self.visible = False
    
    def set_acceleration(self, enabled):
        self.acceleration_enabled = enabled
        if self.window and self.visible:
            GLib.idle_add(self.window.queue_draw)
    
    def set_precision_mode(self, enabled):
        self.precision_mode = enabled
        if self.window and self.visible:
            GLib.idle_add(self.window.queue_draw)
    
    def _do_show(self):
        if self.window:
            self.window.show_all()
    
    def _do_hide(self):
        if self.window:
            self.window.hide()
    
    def cleanup(self):
        if self.window:
            GLib.idle_add(Gtk.main_quit)
    
    def _run_gtk(self):
        indicator = self
        
        class IndicatorWindow(Gtk.Window):
            def __init__(self):
                super().__init__()
                
                settings = Gtk.Settings.get_default()
                if settings:
                    settings.set_property("gtk-enable-animations", False)
                
                display = Gdk.Display.get_default()
                monitor = display.get_primary_monitor()
                
                if monitor is None:
                    monitor = display.get_monitor(0)
                
                geometry = monitor.get_geometry()
                
                self.set_decorated(False)
                self.set_skip_taskbar_hint(True)
                self.set_skip_pager_hint(True)
                self.set_keep_above(True)
                self.set_accept_focus(False)
                self.set_type_hint(Gdk.WindowTypeHint.NOTIFICATION)
                
                bar_height = 7
                self.set_default_size(geometry.width, bar_height)
                self.move(0, 0)
                
                screen = self.get_screen()
                visual = screen.get_rgba_visual()
                if visual:
                    self.set_visual(visual)
                
                self.set_app_paintable(True)
                
                self.drawing_area = Gtk.DrawingArea()
                self.drawing_area.connect('draw', self.on_draw)
                self.add(self.drawing_area)
                
                self.show_all()
                self.hide()
            
            def on_draw(self, widget, cr):
                allocation = widget.get_allocation()
                
                if indicator.precision_mode:
                    cr.set_source_rgba(0.2, 0.8, 0.3, 0.9)
                elif indicator.acceleration_enabled:
                    cr.set_source_rgba(3, 4, 6, 0.9)
                else:
                    cr.set_source_rgba(0.4, 0.2, 0.6, 0.9)
                
                cr.rectangle(0, 0, allocation.width, allocation.height)
                cr.fill()
                return False
        
        try:
            self.window = IndicatorWindow()
            self.gtk_ready = True
            Gtk.main()
        except Exception as e:
            print(f"GTK error: {e}")