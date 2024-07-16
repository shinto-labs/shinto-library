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


def _verify_data(data: dict[str, Any], required_params: list[str] | dict[str, Any], depth: int = 0) -> dict[str, Any]:
    """
    Verify the presence of required parameters within data.

    Args:
        data (dict): The config data to verify.
        required_params (list | dict): The required parameters to verify.
            Should be  list of required parameter names.
            Optionally could be a tree dict with keys as the required parameter names and values as None or a dict.
        depth (int): The depth of the current recursion.

    Raises:
        KeyError: If a required parameter is not found in the data.
        ValueError: If the value of a required parameter is not None or a dict.

    Example:
    -------
    data = {"key1": "value1", "key2": {"key3": "value3"}}

    required_params = { "key1": None, "key2": {"key3": None}}

    _verify_data(data, required_params)

    """
    if isinstance(required_params, list) and depth == 0:
        required_params = {key: None for key in required_params}
    for key, value in required_params.items():
        if key not in data:
            raise KeyError(f"Required parameter not found in config: {key}")

        if isinstance(value, dict):
            _verify_data(data[key], value, depth + 1)
        elif value is not None:
            raise ValueError(f"Invalid value for required parameter: {key}. Must be dict or None.")
    return data


def load_config_file(
    file_path: str,
    defaults: dict[str, Any] | None = None,
    start_element: list[str] | None = None,
    required_params: list[str] | dict[str, Any] | None = None,
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

    if len(required_params) > 0:
        _verify_data(config, required_params)

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
