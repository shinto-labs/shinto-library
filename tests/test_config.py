"""Test the config module."""

import os
import tempfile
import unittest
from pathlib import Path

from shinto.config import (
    ConfigError,
    ConfigType,
    _mask_sensitive_keys,
    _substitute_env_vars,
    load_config_file,
    output_config,
)

TEST_CONFIG = """
database:
  host: ${DB_HOST}
  port: ${DB_PORT}
  name: ${DB_NAME:default_db}

service:
  container_name: ${BIFROST_CONTAINER_NAME}
  timeout: ${TIMEOUT:30}

static_value: "no_substitution"
"""


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
        yaml_config = load_config_file(yaml_file_path)
        self.assertIsInstance(yaml_config, dict)
        self.assertDictEqual(yaml_config, {"test": "value"})

    def test_load_config_file_json(self):
        """Test loading a JSON config file."""
        json_file_path = Path(self.temp_dir) / "config.json"
        with Path(json_file_path).open("w") as json_file:
            json_file.write('{"test": "value"}')
        self.assertTrue(Path(json_file_path).is_file())
        json_config = load_config_file(json_file_path)
        self.assertIsInstance(json_config, dict)
        self.assertDictEqual(json_config, {"test": "value"})

    def test_load_config_file_ini(self):
        """Test loading an INI config file."""
        ini_file_path = Path(self.temp_dir) / "config.ini"
        with Path(ini_file_path).open("w") as ini_file:
            ini_file.write("[test]\nkey = value")
        self.assertTrue(Path(ini_file_path).is_file())
        ini_config = load_config_file(ini_file_path)
        self.assertIsInstance(ini_config, dict)
        self.assertDictEqual(ini_config, {"test": {"key": "value"}})

    def test_load_config_file_invalid(self):
        """Test loading an invalid config file."""
        invalid_file_path = Path(self.temp_dir) / "config.invalid"
        with Path(invalid_file_path).open("w") as invalid_file:
            invalid_file.write("invalid config")
        self.assertTrue(Path(invalid_file_path).is_file())
        with self.assertRaises(ConfigError):
            load_config_file(invalid_file_path)

    def test_load_config_file_non_existent(self):
        """Test loading a non-existent config file."""
        non_existent_file_path = "/path/to/non_existent_config.yaml"
        with self.assertRaises(FileNotFoundError):
            load_config_file(non_existent_file_path)

    def test_load_config_file_yaml_with_defaults(self):
        """Test loading a YAML config file with default values."""
        yaml_file_path = Path(self.temp_dir) / "config.yaml"
        with Path(yaml_file_path).open("w") as yaml_file:
            yaml_file.write("test: \n  key: value\ntest2: value3")
        self.assertTrue(Path(yaml_file_path).is_file())
        yaml_config = load_config_file(
            yaml_file_path, defaults={"test": {"key2": "value2"}, "test2": "value4"}
        )
        self.assertIsInstance(yaml_config, dict)
        self.assertDictEqual(
            yaml_config, {"test": {"key": "value", "key2": "value2"}, "test2": "value3"}
        )

    def test_load_config_file_yaml_with_invalid_defaults(self):
        """Test loading a YAML config file with invalid default values."""
        yaml_file_path = Path(self.temp_dir) / "config.yaml"
        with Path(yaml_file_path).open("w") as yaml_file:
            yaml_file.write("test: \n  key: value")
        self.assertTrue(Path(yaml_file_path).is_file())
        with self.assertRaises(ValueError):
            load_config_file(yaml_file_path, defaults={"test": {"key": {"key2": "value2"}}})

    def test_replace_passwords(self):
        """Test replacing passwords in a dictionary."""
        data = {"username": "john_doe", "password": "secret123"}
        replaced_data = _mask_sensitive_keys(data)
        self.assertNotIn("secret123", str(replaced_data))

    def test_replace_passwords_list(self):
        """Test replacing passwords in a dictionary."""
        data = {"username": "john_doe", "passwords": [{"password": "secret123"}]}
        replaced_data = _mask_sensitive_keys(data)
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
        yaml_output = output_config(yaml_config, ConfigType.YAML)
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
        json_output = output_config(json_config, ConfigType.JSON)
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
        ini_output = output_config(ini_config, ConfigType.INI)
        self.assertIsInstance(ini_output, str)

    def test_substitute_env_vars_simple(self):
        """Test substituting simple environment variables."""
        # Set test environment variables
        os.environ["TEST_VAR"] = "test_value"
        os.environ["BIFROST_CONTAINER_NAME"] = "my-container"

        try:
            # Test string substitution
            result = _substitute_env_vars("Container: ${BIFROST_CONTAINER_NAME}")
            self.assertEqual(result, "Container: my-container")

            # Test dict substitution
            data = {
                "container_name": "${BIFROST_CONTAINER_NAME}",
                "test_key": "${TEST_VAR}",
                "no_var": "regular_value",
            }
            result = _substitute_env_vars(data)
            expected = {
                "container_name": "my-container",
                "test_key": "test_value",
                "no_var": "regular_value",
            }
            self.assertEqual(result, expected)

            # Test list substitution
            data = ["${TEST_VAR}", "normal", {"nested": "${BIFROST_CONTAINER_NAME}"}]
            result = _substitute_env_vars(data)
            expected = ["test_value", "normal", {"nested": "my-container"}]
            self.assertEqual(result, expected)

        finally:
            # Clean up environment variables
            del os.environ["TEST_VAR"]
            del os.environ["BIFROST_CONTAINER_NAME"]

    def test_substitute_env_vars_with_defaults(self):
        """Test substituting environment variables with default values."""
        # Ensure the env var doesn't exist
        if "NONEXISTENT_VAR" in os.environ:
            del os.environ["NONEXISTENT_VAR"]

        # Test with default value
        result = _substitute_env_vars("Value: ${NONEXISTENT_VAR:default_value}")
        self.assertEqual(result, "Value: default_value")

        # Test empty default
        result = _substitute_env_vars("Value: ${NONEXISTENT_VAR:}")
        self.assertEqual(result, "Value: ")

    def test_substitute_env_vars_missing_no_default(self):
        """Test behavior with missing env vars and no defaults."""
        # Ensure the env var doesn't exist
        if "NONEXISTENT_VAR" in os.environ:
            del os.environ["NONEXISTENT_VAR"]

        # Test with raise_on_missing=False (default behavior)
        result = _substitute_env_vars("Value: ${NONEXISTENT_VAR}")
        self.assertEqual(result, "Value: ${NONEXISTENT_VAR}")

        # Test with raise_on_missing=True
        with self.assertRaises(KeyError) as context:
            _substitute_env_vars("Value: ${NONEXISTENT_VAR}", raise_on_missing=True)
        self.assertIn("NONEXISTENT_VAR", str(context.exception))

    def test_load_config_file_with_env_vars(self):
        """Test loading config file with environment variable substitution."""
        # Set test environment variables
        os.environ["DB_HOST"] = "localhost"
        os.environ["DB_PORT"] = "5432"
        os.environ["BIFROST_CONTAINER_NAME"] = "bifrost-service"

        try:
            # Create test YAML file with env vars
            yaml_file_path = Path(self.temp_dir) / "config_with_env.yaml"
            with yaml_file_path.open("w") as yaml_file:
                yaml_file.write(TEST_CONFIG)

            # Load config with env var substitution enabled (default)
            config = load_config_file(str(yaml_file_path))
            expected = {
                "database": {"host": "localhost", "port": "5432", "name": "default_db"},
                "service": {"container_name": "bifrost-service", "timeout": "30"},
                "static_value": "no_substitution",
            }
            self.assertEqual(config, expected)

            # Load config with env var substitution disabled
            config_no_sub = load_config_file(str(yaml_file_path), substitute_env_vars=False)
            expected_placeholder = "${BIFROST_CONTAINER_NAME}"
            self.assertEqual(config_no_sub["service"]["container_name"], expected_placeholder)

        finally:
            # Clean up environment variables
            for var in ["DB_HOST", "DB_PORT", "BIFROST_CONTAINER_NAME"]:
                if var in os.environ:
                    del os.environ[var]

    def test_load_config_file_env_vars_with_missing_required(self):
        """Test loading config file with missing required env vars."""
        # Ensure the env var doesn't exist
        if "REQUIRED_VAR" in os.environ:
            del os.environ["REQUIRED_VAR"]

        # Create test YAML file with required env var
        yaml_file_path = Path(self.temp_dir) / "config_required_env.yaml"
        with yaml_file_path.open("w") as yaml_file:
            yaml_file.write("required_value: ${REQUIRED_VAR}")

        # Test with raise_on_missing_env=True
        with self.assertRaises(KeyError):
            load_config_file(str(yaml_file_path), raise_on_missing_env=True)

        # Test with raise_on_missing_env=False (default)
        config = load_config_file(str(yaml_file_path), raise_on_missing_env=False)
        self.assertEqual(config["required_value"], "${REQUIRED_VAR}")


if __name__ == "__main__":
    unittest.main()
