"""Test the config module."""

import tempfile
import unittest
from pathlib import Path

from shinto import config


class TestConfig(unittest.TestCase):
    """Test the config module."""

    @classmethod
    def setUpClass(cls):
        """Set up the test class."""
        cls.temp_dir = tempfile.mkdtemp()

    def test_load_config_file_yaml(self):
        """Test loading a YAML config file."""
        yaml_file_path = Path(self.temp_dir) / "config.yaml"
        with Path(yaml_file_path).open("w") as yaml_file:
            yaml_file.write("test: value")
        self.assertTrue(Path(yaml_file_path).is_file())
        yaml_config = config.load_config_file(yaml_file_path)
        self.assertIsInstance(yaml_config, dict)
        self.assertDictEqual(yaml_config, {"test": "value"})

    def test_load_config_file_json(self):
        """Test loading a JSON config file."""
        json_file_path = Path(self.temp_dir) / "config.json"
        with Path(json_file_path).open("w") as json_file:
            json_file.write('{"test": "value"}')
        self.assertTrue(Path(json_file_path).is_file())
        json_config = config.load_config_file(json_file_path)
        self.assertIsInstance(json_config, dict)
        self.assertDictEqual(json_config, {"test": "value"})

    def test_load_config_file_ini(self):
        """Test loading an INI config file."""
        ini_file_path = Path(self.temp_dir) / "config.ini"
        with Path(ini_file_path).open("w") as ini_file:
            ini_file.write("[test]\nkey = value")
        self.assertTrue(Path(ini_file_path).is_file())
        ini_config = config.load_config_file(ini_file_path)
        self.assertIsInstance(ini_config, dict)
        self.assertDictEqual(ini_config, {"test": {"key": "value"}})

    def test_load_config_file_invalid(self):
        """Test loading an invalid config file."""
        invalid_file_path = Path(self.temp_dir) / "config.invalid"
        with Path(invalid_file_path).open("w") as invalid_file:
            invalid_file.write("invalid config")
        self.assertTrue(Path(invalid_file_path).is_file())
        with self.assertRaises(config.ConfigError):
            config.load_config_file(invalid_file_path)

    def test_load_config_file_non_existent(self):
        """Test loading a non-existent config file."""
        non_existent_file_path = "/path/to/non_existent_config.yaml"
        with self.assertRaises(FileNotFoundError):
            config.load_config_file(non_existent_file_path)

    def test_load_config_file_yaml_nested(self):
        """Test loading a nested config file."""
        nested_yaml_file_path = Path(self.temp_dir) / "nested_config.yaml"
        with Path(nested_yaml_file_path).open("w") as nested_yaml_file:
            nested_yaml_file.write("test:\n  test: value")
        self.assertTrue(Path(nested_yaml_file_path).is_file())
        nested_yaml_config = config.load_config_file(nested_yaml_file_path, start_element=["test"])
        self.assertIsInstance(nested_yaml_config, dict)
        self.assertDictEqual(nested_yaml_config, {"test": "value"})

    def test_load_config_file_yaml_nested_invalid(self):
        """Test loading a nested config file."""
        nested_yaml_file_path = Path(self.temp_dir) / "nested_config.yaml"
        with Path(nested_yaml_file_path).open("w") as nested_yaml_file:
            nested_yaml_file.write("test:\n  test: value")
        self.assertTrue(Path(nested_yaml_file_path).is_file())
        with self.assertRaises(KeyError):
            config.load_config_file(nested_yaml_file_path, start_element=["unknown"])

    def test_load_config_file_yaml_remove_none_values(self):
        """Test loading a YAML config file."""
        yaml_file_path = Path(self.temp_dir) / "config.yaml"
        with Path(yaml_file_path).open("w") as yaml_file:
            yaml_file.write("test: value\ntest2: \ntest3:\n  test4: \n  test5: value")
        self.assertTrue(Path(yaml_file_path).is_file())
        yaml_config = config.load_config_file(yaml_file_path, keep_none_values=False)
        self.assertIsInstance(yaml_config, dict)
        self.assertDictEqual(yaml_config, {"test": "value", "test3": {"test5": "value"}})

    def test_replace_passwords(self):
        """Test replacing passwords in a dictionary."""
        data = {"username": "john_doe", "password": "secret123"}
        replaced_data = config.replace_passwords(data)
        self.assertNotIn("secret123", str(replaced_data))

    def test_replace_passwords_list(self):
        """Test replacing passwords in a dictionary."""
        data = {"username": "john_doe", "passwords": [{"password": "secret123"}]}
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
            },
        }
        yaml_output = config.output_config(yaml_config, config.ConfigType.YAML)
        self.assertIsInstance(yaml_output, str)

        # Test outputting config as JSON
        json_config = {
            "database": {
                "host": "localhost",
                "port": 5432,
                "username": "admin",
                "password": "secret",
            },
        }
        json_output = config.output_config(json_config, config.ConfigType.JSON)
        self.assertIsInstance(json_output, str)

        # Test outputting config as INI
        ini_config = {
            "database": {
                "host": "localhost",
                "port": 5432,
                "username": "admin",
                "password": "secret",
            },
        }
        ini_output = config.output_config(ini_config, config.ConfigType.INI)
        self.assertIsInstance(ini_output, str)


if __name__ == "__main__":
    unittest.main()
