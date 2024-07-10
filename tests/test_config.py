"""Test the config module."""

import os
import tempfile
import unittest

from shinto import config

temp_dir = ""


def setUpModule():
    """Set up a tmp folder."""
    global temp_dir
    temp_dir = tempfile.mkdtemp()


class TestConfig(unittest.TestCase):
    """Test the config module."""

    def test_load_config_file(self):
        """Test loading config files."""
        # Test loading a YAML config file
        yaml_file_path = os.path.join(temp_dir, "config.yaml")
        open(yaml_file_path, "w").write("test: value")
        self.assertTrue(os.path.isfile(yaml_file_path))
        yaml_config = config.load_config_file(yaml_file_path)
        self.assertIsInstance(yaml_config, dict)
        self.assertDictEqual(yaml_config, {"test": "value"})

        # Test loading a JSON config file
        json_file_path = os.path.join(temp_dir, "config.json")
        open(json_file_path, "w").write('{"test": "value"}')
        self.assertTrue(os.path.isfile(json_file_path))
        json_config = config.load_config_file(json_file_path)
        self.assertIsInstance(json_config, dict)
        self.assertDictEqual(json_config, {"test": "value"})

        # Test loading an INI config file
        ini_file_path = os.path.join(temp_dir, "config.ini")
        open(ini_file_path, "w").write("[test]\nkey = value")
        self.assertTrue(os.path.isfile(ini_file_path))
        ini_config = config.load_config_file(ini_file_path)
        self.assertIsInstance(ini_config, dict)
        self.assertDictEqual(ini_config, {"test": {"key": "value"}})

        # Test loading a non-existent config file
        non_existent_file_path = "/path/to/non_existent_config.yaml"
        with self.assertRaises(FileNotFoundError):
            config.load_config_file(non_existent_file_path)

    def test_replace_passwords(self):
        """Test replacing passwords in a dictionary."""
        data = {"username": "john_doe", "password": "secret123"}
        replaced_data = config.replace_passwords(data)
        self.assertNotIn("secret123", str(replaced_data))

    def test_output_config(self):
        """Test outputting config as YAML."""
        yaml_config = {
            "database": {
                "host": "localhost",
                "port": 5432,
                "username": "admin",
                "password": "secret",
            }
        }
        yaml_output = config.output_config(yaml_config, config.CONFIG_YAML)
        self.assertIsInstance(yaml_output, str)

        # Test outputting config as JSON
        json_config = {
            "database": {
                "host": "localhost",
                "port": 5432,
                "username": "admin",
                "password": "secret",
            }
        }
        json_output = config.output_config(json_config, config.CONFIG_JSON)
        self.assertIsInstance(json_output, str)

        # Test outputting config as INI
        ini_config = {
            "database": {
                "host": "localhost",
                "port": 5432,
                "username": "admin",
                "password": "secret",
            }
        }
        ini_output = config.output_config(ini_config, config.CONFIG_INI)
        self.assertIsInstance(ini_output, str)


if __name__ == "__main__":
    unittest.main()
