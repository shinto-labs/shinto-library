"""Config File handling."""

from __future__ import annotations

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


def _merge_dicts(d1: dict, d2: dict) -> dict:
    """
    Recursively merge two dictionaries.

    Overwrites values in d2 with values in d1.

    Args:
        d1 (dict): The first dictionary.
        d2 (dict): The second dictionary.

    Returns:
        dict: The merged dictionary.

    """
    for key, value in d1.items():
        if key in d2:
            if isinstance(d2[key], dict) and isinstance(value, dict):
                d2[key] = _merge_dicts(value, d2[key])
            elif isinstance(d2[key], dict) or isinstance(value, dict):
                msg = f"Cannot merge {type(value)} with {type(d2[key])} on key: {key}"
                raise ValueError(msg)
            else:
                d2[key] = value
        else:
            d2[key] = value

    return d2


def _read_config_file(file_path: str) -> dict[str, Any]:
    """
    Read config file and return as dict.

    Supported file types: YAML, JSON, INI.

    Args:
        file_path (str): The path to the config file.

    Returns:
        dict: The config data.

    """
    file_extension = Path(file_path).suffix.lower()
    if file_extension in [".yaml", ".yml"]:
        with Path(file_path).open(encoding="utf-8") as yaml_file:
            return yaml.safe_load(yaml_file)
    elif file_extension in [".json", ".js"]:
        with Path(file_path).open(encoding="utf-8") as yaml_file:
            return json.load(yaml_file)
    elif file_extension == ".ini":
        config_data = configparser.ConfigParser()
        config_data.read(file_path)
        return {section: dict(config_data.items(section)) for section in config_data.sections()}
    else:
        msg = f"Unsupported config file extension: {file_extension}"
        raise ConfigError(msg)


def load_config_file(
    file_path: str,
    defaults: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Load config from file.

    Args:
        file_path (str): The path to the config file.
        defaults (dict): If provided, the default values to merge with the config file.

    Returns:
        dict: The config data.

    """
    defaults = copy.deepcopy(defaults) or {}

    if not file_path or not Path(file_path).exists():
        msg = f"Config file not found: {file_path}."
        raise FileNotFoundError(msg)

    config = _read_config_file(file_path)

    return _merge_dicts(config, defaults)


def _mask_sensitive_keys(
    data: dict[str, Any] | list[Any],
    sensitive_keys: list[str] | None = None,
) -> dict[str, Any] | list[Any]:
    """
    Replace sensitive keys in a dictionary with ****.

    Args:
        data (dict | list): The data to mask.
        sensitive_keys (list):
            The sensitive keys to mask. Defaults to ["password", "pass", "passwd"].

    Returns:
        (dict | list): The masked data.

    """
    if sensitive_keys is None:
        sensitive_keys = ["password", "pass", "passwd"]
    if isinstance(data, dict):
        for key, value in data.items():
            if key.lower() in sensitive_keys:
                data[key] = "****"
            else:
                data[key] = _mask_sensitive_keys(value)
    elif isinstance(data, list):
        data = [_mask_sensitive_keys(item) for item in data]
    return data


def output_config(
    configdata: dict,
    output_config_type: ConfigType = ConfigType.YAML,
    sensitive_keys: list[str] | None = None,
) -> str:
    """
    Dump config dict to a output_config_type (yaml, json, ini).

    Args:
        configdata (dict): The config data to dump.
        output_config_type (ConfigType): The output config type.
        sensitive_keys (list):
            The sensitive keys to mask. Defaults to ["password", "pass", "passwd"].

    Returns:
        str: The dumped config data.

    """
    config_data = _mask_sensitive_keys(copy.deepcopy(configdata), sensitive_keys)

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
