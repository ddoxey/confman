import gi
from gi.repository import Gtk

gi.require_version("Gtk", "3.0")

from gi.repository import Gtk

class ConfigTab(Gtk.Box):
    """
    Tab widget for editing a single configuration file.
    Dynamically generates input fields based on the file structure.
    """

    def __init__(self, config_instance):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.set_margin_start(20)
        self.set_margin_end(20)
        self.set_margin_top(20)
        self.set_margin_bottom(20)

        self.config = config_instance
        self.data = self.config.read()
        self.comments = self.config.get_comments()  # Retrieve comments from the Config instance

        # Generate UI fields
        self.entries = {}
        for key, value in self.data.items():
            self.add_config_field(key, value)

    def add_config_field(self, key, value):
        """
        Add a configuration field, handling nested dictionaries and lists.
        """
        if isinstance(value, dict):
            self.add_nested_dict(key, value)
        elif isinstance(value, list):
            self.add_list_field(key, value)
        else:
            self.add_single_field(key, value)

    def add_nested_dict(self, key, value):
        """
        Render a dictionary as a collapsible section.
        """
        expander = Gtk.Expander(label=key.title())
        nested_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        for sub_key, sub_value in value.items():
            self.add_config_field_to_container(nested_box, f"{key}.{sub_key}", sub_value)

        expander.add(nested_box)
        self.pack_start(expander, expand=False, fill=True, padding=0)

    def add_list_field(self, key, value_list):
        """
        Render a list, such as "Work History".
        """
        expander = Gtk.Expander(label=key.title())
        list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        for idx, item in enumerate(value_list):
            if isinstance(item, dict):
                item_expander = Gtk.Expander(label=f"{key.title()} Entry {idx + 1}")
                item_expander.set_expanded(True)

                item_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
                for sub_key, sub_value in item.items():
                    self.add_config_field_to_container(item_box, f"{key}[{idx}].{sub_key}", sub_value)

                item_expander.add(item_box)
                list_box.pack_start(item_expander, expand=False, fill=True, padding=0)
            else:
                self.add_config_field_to_container(list_box, f"{key}[{idx}]", item)

        expander.add(list_box)
        self.pack_start(expander, expand=False, fill=True, padding=0)

    def add_single_field(self, key, value):
        """
        Add a single input field for scalar values.
        """
        self.add_config_field_to_container(self, key, value)

    def add_config_field_to_container(self, container, key, value):
        """
        Helper function to add fields to a specific container.
        """
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)

        # Add comment header if available
        if key in self.comments:
            comment_label = Gtk.Label(label=self.comments[key])
            comment_label.set_xalign(0)
            comment_label.get_style_context().add_class("dim-label")
            vbox.pack_start(comment_label, expand=False, fill=True, padding=0)

        # Add input field
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        label = Gtk.Label(label=key.split(".")[-1].replace("_", " ").title(), xalign=0)
        entry = Gtk.Entry()
        entry.set_text(str(value))
        hbox.pack_start(label, expand=False, fill=True, padding=0)
        hbox.pack_start(entry, expand=True, fill=True, padding=0)
        vbox.pack_start(hbox, expand=False, fill=True, padding=0)

        # Store entry for later use
        self.entries[key] = entry
        container.pack_start(vbox, expand=False, fill=True, padding=0)
