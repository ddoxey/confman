import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


class ConfigTab(Gtk.Box):
    def __init__(self, config):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.set_margin_start(20)
        self.set_margin_end(20)
        self.set_margin_top(20)
        self.set_margin_bottom(20)

        self.config = config
        self.data = self.config.read()
        self.entries = {}

        # Create a scrollable panel
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.set_min_content_height(400)

        # Container for dynamic fields
        self.entry_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        scrolled_window.add(self.entry_box)
        self.pack_start(scrolled_window, expand=True, fill=True, padding=0)

        # Add dynamic entry fields
        for key, value in self.data.items():
            self.add_config_field(key, value)

        # Save button
        save_button = Gtk.Button(label="Save")
        save_button.set_halign(Gtk.Align.CENTER)
        save_button.connect("clicked", self.on_save_clicked)
        self.pack_start(save_button, expand=False, fill=False, padding=10)

    def add_section_header(self, section_name, section_data):
        """
        Add a section header and render its fields.
        """
        # Section header (bold label)
        header = Gtk.Label()
        header.set_markup(f"<b>{section_name}</b>")
        header.set_xalign(0)
        self.entry_box.pack_start(header, expand=False, fill=True, padding=10)

        # Render nested fields within the section
        for key, value in section_data.items():
            if isinstance(value, dict):
                # Nested dictionary as expandable group
                self.add_nested_dict_field(f"{section_name}.{key}", value)
            elif isinstance(value, bool):
                # Boolean switch for boolean fields
                self.add_boolean_switch(self.entry_box, f"{section_name}.{key}", key, value)
            else:
                # Scalar fields
                self.add_single_field(f"{section_name}.{key}", value)

    def add_config_field(self, key, value):
        """
        Add fields dynamically based on data type.
        - Top-level keys act as section headers if the value is a dictionary.
        """
        if isinstance(value, dict):
            # Render as a section header with nested fields
            self.add_section_header(key, value)
        elif isinstance(value, list):
            self.add_list_field(key, value)
        else:
            self.add_single_field(key, value)

    def add_nested_dict_field(self, key, nested_dict):
        """
        Add a nested dictionary as an expandable section.
        """
        expander = Gtk.Expander(label=key.title())
        group_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        for sub_key, sub_value in nested_dict.items():
            self.add_config_field(f"{key}.{sub_key}", sub_value)

        expander.add(group_box)
        self.entry_box.pack_start(expander, expand=False, fill=True, padding=0)

    def add_boolean_dict_field(self, key, boolean_dict):
        """
        Add a dictionary of boolean values with switches.
        """
        expander = Gtk.Expander(label=key.title())
        boolean_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        for sub_key, sub_value in boolean_dict.items():
            self.add_boolean_switch(boolean_box, f"{key}.{sub_key}", sub_key, sub_value)

        expander.add(boolean_box)
        self.entry_box.pack_start(expander, expand=False, fill=True, padding=0)

    def add_list_field(self, key, value_list):
        """
        Add a list field with a dynamic '+' button for adding entries.
        """
        expander = Gtk.Expander(label=key.title())
        list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        # Function to add a new list entry dynamically
        def add_list_entry(value=""):
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            entry = Gtk.Entry()
            entry.set_text(str(value))
            hbox.pack_start(entry, expand=True, fill=True, padding=0)
            list_box.pack_start(hbox, expand=False, fill=True, padding=0)
            self.entries[f"{key}[{len(self.entries)}]"] = entry
            self.show_all()

        # Populate existing list items
        for idx, item in enumerate(value_list):
            add_list_entry(item)

        # Add '+' button
        add_button = Gtk.Button(label="+")
        add_button.connect("clicked", lambda btn: add_list_entry())
        list_box.pack_start(add_button, expand=False, fill=False, padding=0)

        expander.add(list_box)
        self.entry_box.pack_start(expander, expand=False, fill=True, padding=0)

    def add_single_field(self, key, value):
        """
        Add a single key-value pair as an entry field.
        """
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        label = Gtk.Label(label=key.split(".")[-1].title(), xalign=0)
        entry = Gtk.Entry()
        entry.set_text(str(value))
        hbox.pack_start(label, expand=False, fill=True, padding=0)
        hbox.pack_start(entry, expand=True, fill=True, padding=0)
        self.entry_box.pack_start(hbox, expand=False, fill=True, padding=0)
        self.entries[key] = entry

    def add_boolean_switch(self, container, key, label_text, value):
        """
        Helper to add a boolean switch with a label.
        """
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        label = Gtk.Label(label=label_text, xalign=0)
        switch = Gtk.Switch()
        switch.set_active(bool(value))

        hbox.pack_start(label, expand=False, fill=True, padding=0)
        hbox.pack_start(switch, expand=False, fill=True, padding=0)
        container.pack_start(hbox, expand=False, fill=True, padding=0)

        # Store reference for saving
        self.entries[key] = switch

    def on_save_clicked(self, widget):
        """
        Save updated data to the configuration file.
        """
        def update_data(data, entries, prefix=""):
            if isinstance(data, dict):
                for key, value in data.items():
                    full_key = f"{prefix}.{key}" if prefix else key
                    if isinstance(value, dict) or isinstance(value, list):
                        update_data(value, entries, full_key)
                    else:
                        widget = entries.get(full_key)
                        if widget:
                            if isinstance(widget, Gtk.Switch):
                                data[key] = widget.get_active()
                            else:
                                data[key] = widget.get_text()
            elif isinstance(data, list):
                for idx, item in enumerate(data):
                    full_key = f"{prefix}[{idx}]"
                    widget = entries.get(full_key)
                    if widget:
                        data[idx] = widget.get_text()

        update_data(self.data, self.entries)
        self.config.write(self.data)
        print(f"Configuration saved to {self.config.file_path}")
