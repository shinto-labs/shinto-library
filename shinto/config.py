"""Config File handling."""

import configparser
import copy
import io
import json
import os
from typing import Any

import yaml

CONFIG_YAML = "YAML"
CONFIG_JSON = "JSON"
CONFIG_INI = "INI"


class ConfigError(Exception):
    """Gets raised when an unsupported config file type is found."""


def load_config_file(
    file_path: str,
    defaults: dict[str, Any] | None = None,
    start_element: list[str] | None = None,
) -> dict[str, Any]:
    """Load config from file."""
    start_element = start_element or []
    required_params = required_params or []

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Config file not found: {file_path}")

    _, file_extension = os.path.splitext(file_path)
    file_extension = file_extension.lower()

    config = defaults or {}
    if file_extension in [".yaml", ".yml"]:
        with open(file_path, encoding="utf-8") as yaml_file:
            config.update(yaml.safe_load(yaml_file))
    elif file_extension in [".json", ".js"]:
        with open(file_path, encoding="utf-8") as yaml_file:
            config.update(json.load(yaml_file))
    elif file_extension == ".ini":
        config_data = configparser.ConfigParser()
        config_data.read(file_path)
        config.update(
            {section: dict(config_data.items(section)) for section in config_data.sections()},
        )
    else:
        msg = f"Unsupported config file extension: {file_extension}"
        raise ConfigError(msg)

    if len(start_element) > 0:
        for item in start_element:
            try:
                config = config[item]
            except KeyError as e:
                msg = f"Invalid item path in config file: {start_element}."
                raise KeyError(msg) from e

    return config


def replace_passwords(data: dict[str, Any] | list[Any]) -> dict[str, Any] | list[Any]:
    """Replace all passwords in dict object before visualizing it."""
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
    """Dump config dict to a output_config_type (yaml, json, ini)."""
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
