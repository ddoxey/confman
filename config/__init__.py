import json
import yaml
import re
from collections import OrderedDict

class Config:
    def __init__(self, file_path: str):
        """
        Initialize the Config class with a file path.
        :param file_path: Path to the configuration file.
        """
        self.file_path = file_path
        self.file_type = self._detect_file_type()
        self.comments = {}

    def get_filename(self):
        """
        Return the file path of the configuration file.
        """
        return self.file_path

    def _detect_file_type(self) -> str:
        """
        Detect the file type (JSON or YAML) based on the file extension.
        :return: 'json' or 'yaml'
        :raises ValueError: If the file extension is not supported.
        """
        if self.file_path.endswith(".json"):
            return "json"
        elif self.file_path.endswith((".yaml", ".yml")):
            return "yaml"
        else:
            raise ValueError(f"Unsupported file type (not .json or .yaml/.yml): {self.file_path}")

    def read(self):
        """
        Read the configuration file and return its content as an OrderedDict.
        For YAML, comments are captured and stored separately.
        :return: OrderedDict representing the content of the file.
        """
        if self.file_type == "json":
            with open(self.file_path, "r") as file:
                return json.load(file, object_pairs_hook=OrderedDict)
        elif self.file_type == "yaml":
            with open(self.file_path, "r") as file:
                raw_lines = file.readlines()

            # Extract comments and load YAML data
            self._extract_comments(raw_lines)
            yaml_content = "\n".join(line for line in raw_lines if not line.strip().startswith("#"))
            return yaml.load(yaml_content, Loader=yaml.SafeLoader)

    def write(self, data):
        """
        Write the given data to the configuration file in the same order it was read.
        For YAML, comments are restored during writing.
        :param data: OrderedDict to be serialized and written to the file.
        """
        if self.file_type == "json":
            with open(self.file_path, "w") as file:
                json.dump(data, file, indent=4)
        elif self.file_type == "yaml":
            yaml_lines = []
            for key, value in data.items():
                serialized_value = yaml.dump({key: value}, default_flow_style=False).strip()
                yaml_lines.append(serialized_value)

            yaml_content = "\n".join(yaml_lines)
            final_content = self._restore_comments(yaml_content)
            with open(self.file_path, "w") as file:
                file.write(final_content)

    def get_comments(self):
        """
        Return a copy of the comments parsed from the configuration.
        """
        return self.comments.copy()

    def get_comment(self, name):
        """
        Return the requested comment or empty string if it doesn't exist. 
        """
        return self.comments.get(name, "")

    def _extract_comments(self, raw_lines):
        """
        Extract comments from YAML lines and store them, including multi-line and inline comments.
        :param raw_lines: List of lines from the YAML file.
        """
        self.comments = {}
        current_comment_lines = []
        for i, line in enumerate(raw_lines):
            if line.strip().startswith("#"):
                current_comment_lines.append(line.strip("# ").strip())
            else:
                key_match = re.match(r"^\s*([\w\-]+)\s*:", line)
                if key_match:
                    key = key_match.group(1)
                    if current_comment_lines:
                        self.comments[key] = "\n".join(current_comment_lines)
                        current_comment_lines = []
                    # Check for inline comments
                    if "#" in line:
                        inline_comment = line.split("#", 1)[1].strip()
                        self.comments[key] = f"{self.comments.get(key, '')}\n{inline_comment}".strip()

    def _restore_comments(self, yaml_content):
        """
        Restore comments into the YAML content during writing, preserving order, inline comments,
        and adding blank lines between entries.
        :param yaml_content: Serialized YAML string without comments.
        :return: YAML string with comments restored.
        """
        yaml_lines = yaml_content.splitlines()
        final_lines = []
        for line in yaml_lines:
            key_match = re.match(r"^\s*([\w\-]+)\s*:", line)
            if key_match:
                key = key_match.group(1)
                if key in self.comments:
                    # Add multi-line comments before the key
                    comment_lines = [
                        f"# {comment}" for comment in self.comments[key].split("\n") if not comment.startswith("#")
                    ]
                    if "\n" in self.comments[key]:
                        final_lines.extend(comment_lines)
                    else:
                        # Inline comment: Append to the same line
                        line += f"  # {self.comments[key]}"
            final_lines.append(line)
            # Add a blank line after each key-value pair
            if key_match:
                final_lines.append("")
        # Remove trailing blank line
        if final_lines and not final_lines[-1].strip():
            final_lines.pop()
        return "\n".join(final_lines)
