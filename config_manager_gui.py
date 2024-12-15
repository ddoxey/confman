"""
The GUI application for managing configuration and process state.
"""
import re
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

from config import Config
from tabs.config import ConfigTab
from tabs.process import ProcessesTab


class ConfigManagerApp(Gtk.Window):
    """
    Main application window for managing configuration files.
    Provides a tabbed interface for editing multiple configuration files.
    """

    def __init__(self, config_file='config_manager.yaml'):
        super().__init__(title='Configuration Manager')
        self.set_default_size(600, 400)

        # Apply custom CSS for styling
        self.apply_css('style.css')

        # Main container: Notebook for tabs
        self.notebook = Gtk.Notebook()
        self.notebook.get_style_context().add_class('notebook')
        self.add(self.notebook)

        # Load configuration YAML file
        self.config_file = config_file
        self.load_manager_config()

    def apply_css(self, css_file):
        """
        Apply custom CSS styles to the application.
        :param css_file: Path to the CSS file.
        """
        css_provider = Gtk.CssProvider()
        css_provider.load_from_path(css_file)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def load_manager_config(self):
        """
        Load the configuration manager file and create tabs dynamically.
        """
        self.manager_config = Config(self.config_file)
        entries = self.manager_config.read()
        if 'processes' in entries:
            # Processes is first tab
            self.notebook.append_page(ProcessesTab(entries['processes']),
                                      Gtk.Label(label='Processes'))
            del entries['processes']

        for field_name, value in entries.items():
            # Determine tab label
            tab_label = self.manager_config.get_comment(field_name)
            if len(tab_label) == 0:
                if isinstance(value, list):
                    tab_label = field_name.replace('_', ' ').title()
                elif isinstance(value, str):
                    filestem = value.split('/')[-1].rsplit('.', 1)[0]
                    tab_label = re.sub(r'[_\W]+',
                                       ' ',
                                       filestem).strip().title()
                else:
                    tab_label = field_name.replace('_', ' ').title()

            # Add ConfigTab for other configurations
            self.notebook.append_page(ConfigTab(Config(value)),
                                      Gtk.Label(label=tab_label))


if __name__ == '__main__':
    app = ConfigManagerApp()
    app.connect('destroy', Gtk.main_quit)
    app.show_all()
    Gtk.main()
