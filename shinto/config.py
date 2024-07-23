"""Config File handling."""

import configparser
import copy
import io
import json
from enum import Enum
from pathlib import Path
from typing import Any

import yaml


class ConfigType(Enum):
    """Config file types."""

    YAML = "YAML"
    JSON = "JSON"
    INI = "INI"


class ConfigError(Exception):
    """Gets raised when an unsupported config file type is found."""


def remove_none_values(data: dict[str, Any] | list[Any]) -> dict[str, Any] | list[Any]:
    """Remove all None values from a dict or list."""
    if isinstance(data, dict):
        return {
            k: (v if not isinstance(v, list | dict) else remove_none_values(v))
            for k, v in data.items()
            if v is not None
        }
    if isinstance(data, list):
        return [
            (v if not isinstance(v, list | dict) else remove_none_values(v))
            for v in data
            if v is not None
        ]

    msg = f"Unsupported data type: {type(data)}"
    raise ConfigError(msg)


def load_config_file(
    file_path: str,
    defaults: dict[str, Any] | None = None,
    start_element: list[str] | None = None,
    keep_none_values: bool = True,
) -> dict[str, Any]:
    """Load config from file."""
    start_element = start_element or []

    if not isinstance(file_path, str) or not Path(file_path).exists():
        msg = f"Config file not found: {file_path}"
        raise FileNotFoundError(msg)

    file_extension = Path(file_path).suffix.lower()

    config = defaults or {}
    if file_extension in [".yaml", ".yml"]:
        with Path(file_path).open(encoding="utf-8") as yaml_file:
            config.update(yaml.safe_load(yaml_file))
    elif file_extension in [".json", ".js"]:
        with Path(file_path).open(encoding="utf-8") as yaml_file:
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

    if not keep_none_values:
        config = remove_none_values(config)

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


def output_config(configdata: dict, output_config_type: ConfigType = ConfigType.YAML) -> str:
    """Dump config dict to a output_config_type (yaml, json, ini)."""
    config_data = replace_passwords(copy.deepcopy(configdata))

    if output_config_type == ConfigType.YAML:
        output = yaml.dump(config_data)
    elif output_config_type == ConfigType.JSON:
        output = json.dumps(config_data)
    elif output_config_type == ConfigType.INI:
        config = configparser.ConfigParser()
        for section, options in config_data.items():
            config[section] = options
        output_stream = io.StringIO()
        config.write(output_stream)
        output = output_stream.getvalue()

    return output
