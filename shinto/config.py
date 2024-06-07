"""
Config File handling
"""
import os
import io
import json
import copy
import configparser

import yaml


CONFIG_YAML = 'YAML'
CONFIG_JSON = 'JSON'
CONFIG_INI  = 'INI'


class ConfigError(Exception):
    """
    Gets raised when an unsupported config file type is found
    """


def load_config_file(file_path: str, defaults = None) -> dict:
    """
    Load config from file
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Config file not found: {file_path}")

    _, file_extension = os.path.splitext(file_path)
    file_extension = file_extension.lower()

    config_data = defaults
    if file_extension in ['.yaml', '.yml']:
        with open(file_path, "r", encoding="utf-8") as yaml_file:
            config_data.update(yaml.safe_load(yaml_file))
    elif file_extension in ['.json', '.js']:
        with open(file_path, "r", encoding="utf-8") as yaml_file:
            config_data.update(json.load(yaml_file))
    elif file_extension == ".ini":
        config = configparser.ConfigParser()
        config.read(file_path)
        config_data.update({section: dict(config.items(section)) for section in config.sections()})
    else:
        raise ConfigError(f"Unsupported config file extension: {file_extension}")

    return config_data


def replace_passwords(data):
    """
    Replace all passwords in dict object before visualizing it.
    """
    if isinstance(data, dict):
        for key, value in data.items():
            if key.lower() in ["password", "pass", "passwd"]:
                data[key] = "****"
            else:
                data[key] = replace_passwords(value)
    elif isinstance(data, list):
        data = [replace_passwords(item) for item in data]
    return data


def output_config(configdata: dict, output_config_type: str = CONFIG_YAML) -> str:
    """
    Dump config dict to a output_config_type (yaml, json, ini)
    """

    config_data = replace_passwords(copy.deepcopy(configdata))

    if output_config_type == CONFIG_YAML:
        output = yaml.dump(config_data)
    elif output_config_type == CONFIG_JSON:
        output = json.dumps(config_data)
    elif output_config_type == CONFIG_INI:
        config = configparser.ConfigParser()
        for section, options in config_data.items():
            config[section] = options
        output_stream = io.StringIO()
        config.write(output_stream)
        output = output_stream.getvalue()
    else:
        raise ConfigError(f"Unsupported config output type: {output_config_type}")

    return output
