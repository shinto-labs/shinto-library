"""Config File handling."""

from __future__ import annotations

import configparser
import copy
import io
import json
import os
import re
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


def _substitute_env_vars(
    config_data: str,
    raise_on_missing: bool = False,
) -> dict[str, Any] | list[Any] | str:
    """
    Recursively substitute environment variables in config data.

    Supports ${VAR_NAME} and ${VAR_NAME:default_value} syntax.

    Args:
        config_data: The config data as a string.
        raise_on_missing: If True, raises KeyError for missing env vars without defaults.

    Returns:
        The data with environment variables substituted.

    Raises:
        KeyError: If raise_on_missing is True and an env var is missing without a default.

    """
    if not isinstance(config_data, str):
        raise TypeError("Config data must be a string for environment variable substitution")
    pattern = re.compile(r"\$\{([^}:]+)(?::(-?)([^}]*))?\}")
    matches = pattern.findall(config_data)
    for var_name, default_prefix, default_value in matches:
        env_value = os.environ.get(var_name)
        if env_value is not None:
            config_data = config_data.replace(f"${{{var_name}}}", env_value)
            config_data = config_data.replace(
                f"${{{var_name}:{default_prefix}{default_value}}}", env_value
            )
        elif default_value is not None:
            config_data = config_data.replace(
                f"${{{var_name}:{default_prefix}{default_value}}}", default_value
            )
        elif raise_on_missing:
            msg = f"Environment variable '{var_name}' not found and no default provided"
            raise KeyError(msg)

    return config_data


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


def _read_config_file(file_path: str, config_data: str) -> dict[str, Any]:
    """
    Read config file and return as dict.

    Supported file types: YAML, JSON, INI.

    Args:
        file_path (str): The path to the config file.
        config_data (str): The config data as a string.

    Returns:
        dict: The config data.

    """
    file_extension = Path(file_path).suffix.lower()
    if file_extension in [".yaml", ".yml"]:
        return yaml.safe_load(config_data)
    if file_extension in [".json", ".js"]:
        return json.loads(config_data)
    if file_extension == ".ini":
        config = configparser.ConfigParser()
        config.read_string(config_data)
        return {section: dict(config[section]) for section in config.sections()}

    msg = f"Unsupported config file extension: {file_extension}"
    raise ConfigError(msg)


def load_config_file(
    file_path: str,
    defaults: dict[str, Any] | None = None,
    substitute_env_vars: bool = True,
    raise_on_missing_env: bool = False,
) -> dict[str, Any]:
    """
    Load config from file.

    Args:
        file_path (str): The path to the config file.
        defaults (dict): If provided, the default values to merge with the config file.
        substitute_env_vars (bool): If True, substitute environment variables in config values.
        raise_on_missing_env (bool): If True, raise error for missing env vars without defaults.

    Returns:
        dict: The config data.

    """
    defaults = copy.deepcopy(defaults) or {}

    if not file_path or not Path(file_path).exists():
        msg = f"Config file not found: {file_path}."
        raise FileNotFoundError(msg)

    config_data = Path(file_path).read_text(encoding="utf-8")

    if substitute_env_vars:
        config_data = _substitute_env_vars(config_data, raise_on_missing_env)

    config = _read_config_file(file_path, config_data) or {}

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
