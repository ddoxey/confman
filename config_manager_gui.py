import gi
import yaml
import re
from config import Config  # Import the Config module
from gi.repository import Gtk, Gdk

gi.require_version("Gtk", "3.0")


class ConfigManagerApp(Gtk.Window):
    """
    Main application window for managing configuration files.
    Provides a tabbed interface for editing multiple configuration files.
    """

    def __init__(self, config_file="config_manager.yaml"):
        super().__init__(title="Configuration Manager")
        self.set_default_size(600, 400)

        # Apply custom CSS for styling
        self.apply_css("style.css")

        # Load configuration YAML file
        self.config_file = config_file
        self.manager_config, self.tab_labels = self.load_manager_config()

        # Main container: Notebook for tabs
        self.notebook = Gtk.Notebook()
        self.notebook.get_style_context().add_class("notebook")
        self.add(self.notebook)

        # Add tabs dynamically using file paths
        for key, file_path in self.manager_config.items():
            tab_label = self.tab_labels[file_path]
            self.notebook.append_page(ConfigTab(file_path), Gtk.Label(label=tab_label))

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
        Load the configuration manager YAML file and generate tab labels.
        :return: Tuple containing configuration data and tab labels.
        """
        manager_config = Config(self.config_file)
        config_data = manager_config.read()

        tab_labels = {}
        for key, value in config_data.items():
            # Strip enclosing quotes from file paths
            if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
            # Generate labels from comments or file names
            full_comment = manager_config.comments.get(key, "")
            tab_labels[value] = (
                full_comment.strip()
                or re.sub(r"[_\W]+", " ", value.split("/")[-1].rsplit(".", 1)[0]).strip().title()
            )

        return config_data, tab_labels


class ConfigTab(Gtk.Box):
    """
    Tab widget for editing a single configuration file.
    Dynamically generates input fields based on the file structure.
    """

    def __init__(self, config_file):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.set_margin_start(20)
        self.set_margin_end(20)
        self.set_margin_top(20)
        self.set_margin_bottom(20)

        self.config_file = config_file
        self.config = Config(self.config_file)

        # Load configuration file data
        self.data = self.config.read()

        # Create a scrollable container for input fields
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.set_min_content_height(400)

        self.entry_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        scrolled_window.add(self.entry_box)
        self.pack_start(scrolled_window, expand=True, fill=True, padding=0)

        # Generate input fields dynamically
        self.entries = {}
        for key, value in self.data.items():
            self.add_config_field(key, value)

        # Add a Save button
        self.save_button = Gtk.Button(label="Save")
        self.save_button.set_halign(Gtk.Align.CENTER)
        self.save_button.set_valign(Gtk.Align.CENTER)
        self.save_button.connect("clicked", self.on_save_clicked)
        self.pack_start(self.save_button, expand=False, fill=False, padding=10)

    def add_config_field(self, key, value):
        """
        Add input fields or groups based on the data structure.
        """
        if isinstance(value, dict):
            self._add_dict_field(key, value)
        elif isinstance(value, list):
            self._add_list_field(key, value)
        else:
            self._add_single_field(key, value)

    def _add_dict_field(self, key, value_dict):
        """
        Add an expandable group for a dictionary field.
        """
        expander = Gtk.Expander(label=key.title())
        group_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        for sub_key, sub_value in value_dict.items():
            self._add_nested_field(group_box, sub_key, sub_value)
        expander.add(group_box)
        self.entry_box.pack_start(expander, expand=False, fill=True, padding=0)

    def _add_list_field(self, key, value_list):
        """
        Add a UI for handling list fields.
        """
        expander = Gtk.Expander(label=key.title())
        list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        for idx, item in enumerate(value_list):
            item_expander = Gtk.Expander(label=f"{key.title()} Entry {idx + 1}")
            item_expander.set_expanded(True)
            item_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            for sub_key, sub_value in item.items():
                self._add_nested_field(item_box, f"{key}[{idx}].{sub_key}", sub_value)
            item_expander.add(item_box)
            list_box.pack_start(item_expander, expand=False, fill=True, padding=0)
        expander.add(list_box)
        self.entry_box.pack_start(expander, expand=False, fill=True, padding=0)

    def _add_nested_field(self, parent_box, key, value):
        """
        Add an input field for a nested data item.
        """
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        if key in self.config.comments:
            comment_label = Gtk.Label(label=self.config.comments[key])
            comment_label.set_xalign(0)
            comment_label.get_style_context().add_class("dim-label")
            vbox.pack_start(comment_label, expand=False, fill=True, padding=0)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        label = Gtk.Label(label=key.split(".")[-1].title(), xalign=0)
        entry = Gtk.Entry()
        entry.set_text(str(value))
        hbox.pack_start(label, expand=False, fill=True, padding=0)
        hbox.pack_start(entry, expand=True, fill=True, padding=0)
        vbox.pack_start(hbox, expand=False, fill=True, padding=0)
        parent_box.pack_start(vbox, expand=False, fill=True, padding=0)
        self.entries[key] = entry

    def _add_single_field(self, key, value):
        """
        Add a single input field for scalar data.
        """
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        label = Gtk.Label(label=key.title(), xalign=0)
        entry = Gtk.Entry()
        entry.set_text(str(value))
        hbox.pack_start(label, expand=False, fill=True, padding=0)
        hbox.pack_start(entry, expand=True, fill=True, padding=0)
        self.entry_box.pack_start(hbox, expand=False, fill=True, padding=0)
        self.entries[key] = entry

    def on_save_clicked(self, widget):
        """
        Save changes made in the UI back to the configuration file.
        """
        def update_data(data, entries, prefix=""):
            if isinstance(data, dict):
                for key, value in data.items():
                    full_key = f"{prefix}.{key}" if prefix else key
                    if isinstance(value, (dict, list)):
                        update_data(value, entries, full_key)
                    elif full_key in entries:
                        data[key] = entries[full_key].get_text()
            elif isinstance(data, list):
                for idx, item in enumerate(data):
                    update_data(item, entries, f"{prefix}[{idx}]")

        update_data(self.data, self.entries)
        self.config.write(self.data)
        print(f"Configuration saved to {self.config_file}")


if __name__ == "__main__":
    app = ConfigManagerApp()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    Gtk.main()
