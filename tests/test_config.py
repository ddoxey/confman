import unittest
import os
import json
from config import Config  # Updated to reflect the renamed file

class TestConfig(unittest.TestCase):
    def setUp(self):
        """
        Create temporary JSON and YAML files for testing in /tmp.
        """
        self.json_file = "/tmp/test_config.json"
        self.yaml_file = "/tmp/test_config.yaml"

        # Sample JSON data
        self.json_data = {"name": "John Doe", "age": "30", "email": "john.doe@example.com"}
        with open(self.json_file, "w") as f:
            json.dump(self.json_data, f, indent=4)

        # Sample YAML data with multi-line comments
        self.yaml_data = """
# This is a multi-line comment
# for the user's full name
name: John Doe

# Another multi-line
# comment for age
age: '30'

email: john.doe@example.com  # The user's email address
        """
        with open(self.yaml_file, "w") as f:
            f.write(self.yaml_data)

    def tearDown(self):
        """
        Keep the files for debugging purposes (no deletion).
        """
        print(f"JSON file: {self.json_file}")
        print(f"YAML file: {self.yaml_file}")

    def test_json_read(self):
        """
        Test reading a JSON file.
        """
        config = Config(self.json_file)
        data = config.read()
        self.assertEqual(data, self.json_data)

    def test_json_write(self):
        """
        Test writing to a JSON file.
        """
        config = Config(self.json_file)
        updated_data = {"name": "Jane Doe", "age": "25", "email": "jane.doe@example.com"}
        config.write(updated_data)

        # Verify the file contents
        with open(self.json_file, "r") as f:
            data = json.load(f)
        self.assertEqual(data, updated_data)

    def test_yaml_read_with_comments(self):
        """
        Test reading a YAML file with comments, including multi-line comments.
        """
        config = Config(self.yaml_file)
        data = config.read()

        # Verify data
        self.assertEqual(data["name"], "John Doe")
        self.assertEqual(data["age"], "30")
        self.assertEqual(data["email"], "john.doe@example.com")

        # Verify extracted comments
        self.assertEqual(config.comments["name"], "This is a multi-line comment\nfor the user's full name")
        self.assertEqual(config.comments["age"], "Another multi-line\ncomment for age")
        self.assertEqual(config.comments["email"], "The user's email address")

    def test_yaml_write_with_comments(self):
        """
        Test writing to a YAML file with comments, including multi-line comments.
        """
        config = Config(self.yaml_file)
        data = config.read()

        # Modify the data and update comments manually
        data["age"] = "35"
        config.comments["age"] = "Updated multi-line\ncomment for age"
        config.comments["email"] = "The user's email address"

        # Write back to the YAML file
        config.write(data)

        # Reload the file and verify
        with open(self.yaml_file, "r") as f:
            lines = f.readlines()
        # Verify multi-line comments are restored correctly
        expected_output = """
# This is a multi-line comment
# for the user's full name
name: John Doe

# Updated multi-line
# comment for age
age: '35'

email: john.doe@example.com  # The user's email address
        """
        self.assertEqual("".join(lines).strip(), expected_output.strip())


if __name__ == "__main__":
    unittest.main()
