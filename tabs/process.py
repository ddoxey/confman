"""
The ProcessesTab renders the process management tab.
"""
import gi

gi.require_version("Gtk", "3.0")

from gi.repository import GLib
from gi.repository import Gtk
from control import Control


class ProcessesTab(Gtk.Box):
    """
    Tab for managing processes listed in config_manager.yaml.
    Provides start, stop, and status widgets for each process.
    """
    UPDATE_INTERVAL = 1000  # Update every 1000 ms (1 second)

    def __init__(self, processes):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.set_margin_start(20)
        self.set_margin_end(20)
        self.set_margin_top(20)
        self.set_margin_bottom(20)

        # Store references to controls and their indicators
        self.controls = []

        # Create widgets for each process
        for process in processes:
            self.add_process_widget(Control(process))

        # Set up periodic updates for process statuses
        GLib.timeout_add(self.UPDATE_INTERVAL, self.update_status_indicators)

    def add_process_widget(self, control):
        """
        Add widgets for managing a single process.
        :param control: Instance of Control
        """
        frame = Gtk.Frame(label=control.get_name())
        frame.set_margin_top(10)
        frame.set_margin_bottom(10)

        # Box for the process controls
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        # Status indicator
        status_indicator = Gtk.DrawingArea()
        status_indicator.set_size_request(20, 20)  # Square size
        status_indicator.set_tooltip_text("Process status indicator")
        status_indicator.connect("draw", self.draw_status_indicator, control)
        hbox.pack_start(status_indicator, expand=False, fill=True, padding=10)

        # Label for the process binary
        label = Gtk.Label(label=f"Process: {control.get_name()}", xalign=0)
        hbox.pack_start(label, expand=True, fill=True, padding=0)

        # Start button
        start_button = Gtk.Button(label="Start")
        start_button.connect("clicked", self.on_start_clicked, control)
        hbox.pack_start(start_button, expand=False, fill=True, padding=0)

        # Stop button
        stop_button = Gtk.Button(label="Stop")
        stop_button.connect("clicked", self.on_stop_clicked, control)
        hbox.pack_start(stop_button, expand=False, fill=True, padding=0)

        # Add the process controls to the tab
        self.pack_start(hbox, expand=False, fill=True, padding=10)

        # Store the control and associated status indicator
        self.controls.append((control, status_indicator))

    def draw_status_indicator(self, widget, cr, control):
        """
        Draw the status indicator as a colored square.
        Green = Running, Yellow = Unsure, Red = Stopped.
        """
        status = control.get_status()

        # Set color based on status
        if status == Control.RUNNING:
            cr.set_source_rgb(0, 1, 0)  # Green
        elif status == Control.JEOPARDY:
            cr.set_source_rgb(1, 1, 0)  # Yellow
        else:
            cr.set_source_rgb(1, 0, 0)  # Red

        cr.rectangle(1, 1, 18, 18)  # Fill indicator
        cr.fill()
        cr.set_source_rgb(0, 0, 0)  # Black border
        cr.set_line_width(1)
        cr.rectangle(0.5, 0.5, 19, 19)  # 1-pixel border
        cr.stroke()

    def update_status_indicators(self):
        """
        Periodically update the status indicators for all processes.
        """
        for _, indicator in self.controls:
            # Trigger a redraw of the status indicator
            indicator.queue_draw()

        # Return True to keep the timeout active
        return True

    def on_start_clicked(self, button, control):
        """
        Start the process.
        """
        return control.start()

    def on_stop_clicked(self, button, control):
        """
        Stop the process.
        """
        return control.stop()
