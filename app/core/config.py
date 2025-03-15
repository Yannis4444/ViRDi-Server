from pathlib import Path

import yaml

from app.api.endpoints.resources import logger
from app.services.prosumer import Resource
from app.services.resource_mapping import ResourceMapping


def _deep_merge(dict1: dict[str, any], dict2: dict[str, any]) -> dict[str, any]:
    """
    Recursively merge two dictionaries.

    :param dict1: First dictionary.
    :param dict2: Second dictionary to merge into the first.
    :return: Merged dictionary.
    """
    for key, value in dict2.items():
        if isinstance(value, dict) and key in dict1 and isinstance(dict1[key], dict):
            dict1[key] = _deep_merge(dict1[key], value)
        elif isinstance(value, list) and key in dict1 and isinstance(dict1[key], list):
            dict1[key].extend(value)  # Merge lists instead of replacing
        else:
            dict1[key] = value  # Overwrite scalar values

    return dict1


def _read_config(path: str) -> dict:
    """
    Loads all configuration yaml files and creates resources, consumers etc. accordingly

    :returns: The combined config from all files as one json
    """

    logger.info(f"Reading Config in '{path}'")

    combined_config = {}

    for file in Path(path).rglob("*.y*ml"):
        with open(file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            combined_config = _deep_merge(combined_config, data)

    return combined_config

def load_config(path: str):
    config = _read_config(path)

    for resource in config.get("resources", []):
        Resource.create_from_config(resource)

    for game_id, game_config in config.get("games", {}).items():
        for resource_id, mapping in game_config.get("resource_mappings", {}).items():
            ResourceMapping.create_from_config(game_id, resource_id, mapping)
