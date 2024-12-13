import gi

gi.require_version("Gtk", "3.0")

from gi.repository import Gtk
from control import Control


class ProcessesTab(Gtk.Box):
    """
    Tab for managing processes listed in config_manager.yaml.
    Provides start, stop, and status widgets for each process.
    """

    def __init__(self, processes):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.set_margin_start(20)
        self.set_margin_end(20)
        self.set_margin_top(20)
        self.set_margin_bottom(20)

        # Create widgets for each process
        for process in processes:
            self.add_process_widget(process)

    def add_process_widget(self, process_data):
        """
        Add widgets for managing a single process.
        :param process_data: Dictionary containing 'bin', 'children', and 'cwd'.
        """
        frame = Gtk.Frame(label=process_data['bin'])
        frame.set_margin_top(10)
        frame.set_margin_bottom(10)

        # Box for the process controls
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        bin_name = process_data.get("bin", "Unknown")
        cwd = process_data.get("cwd", None)

        # Process control instance
        control = Control(bin_name, cwd)

        # Status indicator
        status_indicator = Gtk.DrawingArea()
        status_indicator.set_size_request(20, 20)  # Square size
        status_indicator.set_tooltip_text("Process status indicator")
        status_indicator.connect("draw", self.draw_status_indicator, process_data)
        hbox.pack_start(status_indicator, expand=False, fill=True, padding=10)

        # Label for the process binary
        label = Gtk.Label(label=f"Process: {bin_name}", xalign=0)
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

    def draw_status_indicator(self, widget, cr, process):
        """
        Draw the status indicator as a colored square.
        Green = Running, Yellow = Unsure, Red = Stopped.
        """
        status = self.get_process_status(process)

        # Set color based on status
        if status == "running":
            cr.set_source_rgb(0, 1, 0)  # Green
        elif status == "jeopardy":
            cr.set_source_rgb(1, 1, 0)  # Yellow
        else:
            cr.set_source_rgb(1, 0, 0)  # Red

        # Draw filled square
        cr.rectangle(1, 1, 18, 18)  # Slightly smaller to account for border
        cr.fill()

        # Set border color (black) and line width
        cr.set_source_rgb(0, 0, 0)  # Black
        cr.set_line_width(1)

        # Draw border
        cr.rectangle(0.5, 0.5, 19, 19)  # Coordinates for 1-pixel border
        cr.stroke()

    def get_process_status(self, process):
        """
        Determine the status of the process.
        This is a placeholder; implement real logic here.
        """
        # TODO: Replace with real status check
        return "unsure"  # Placeholder: Return "running", "stopped"

    def on_start_clicked(self, button, control):
        """
        Start the process.
        """
        message = control.start()
        print(message)

    def on_stop_clicked(self, button, control):
        """
        Stop the process.
        """
        message = control.stop()
        print(message)

    def on_status_clicked(self, button, control):
        """
        Check the status of the process.
        """
        status = "running" if control.is_running() else "stopped"
        print(f"Process {control.bin_name} is {status}.")
