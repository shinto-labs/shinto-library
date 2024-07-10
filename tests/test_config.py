import unittest
from shinto import config

# FILEPATH: /home/tommy/work/shintolabs/shinto-library/tests/test_config.py


class TestConfig(unittest.TestCase):
    def test_load_config_file(self):
        # Test loading a YAML config file
        yaml_file_path = "/path/to/config.yaml"
        yaml_config = config.load_config_file(yaml_file_path)
        self.assertIsInstance(yaml_config, dict)
        
        # Test loading a JSON config file
        json_file_path = "/path/to/config.json"
        json_config = config.load_config_file(json_file_path)
        self.assertIsInstance(json_config, dict)
        
        # Test loading an INI config file
        ini_file_path = "/path/to/config.ini"
        ini_config = config.load_config_file(ini_file_path)
        self.assertIsInstance(ini_config, dict)
        
        # Test loading a non-existent config file
        non_existent_file_path = "/path/to/non_existent_config.yaml"
        with self.assertRaises(FileNotFoundError):
            config.load_config_file(non_existent_file_path)
    
    def test_replace_passwords(self):
        # Test replacing passwords in a dictionary
        data = {
            "username": "john_doe",
            "password": "secret123"
        }
        replaced_data = config.replace_passwords(data)
        self.assertNotIn("secret123", str(replaced_data))
    
    def test_output_config(self):
        # Test outputting config as YAML
        yaml_config = {
            "database": {
                "host": "localhost",
                "port": 5432,
                "username": "admin",
                "password": "secret"
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
                "password": "secret"
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
                "password": "secret"
            }
        }
        ini_output = config.output_config(ini_config, config.CONFIG_INI)
        self.assertIsInstance(ini_output, str)

if __name__ == "__main__":
    unittest.main()