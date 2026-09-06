from pathlib import Path
import yaml
import logging
from . import logging_config

logger = logging.getLogger(__name__)

class ConfigError(Exception):
    pass

BASE_DIR= Path(__file__).resolve().parent.parent
CONFIG_DIR= BASE_DIR / "config"

def load_config(filename):
    file_path= CONFIG_DIR / filename
    try:
        with open(file_path, "r") as file:
            data= yaml.safe_load(file)
        if data is None:
            logger.error(f"Config file is empty: {filename} at {file_path}")
            raise ConfigError(f"{filename} at {file_path} is empty")
        logger.info(f"Loaded {filename}")
        return data
    except FileNotFoundError as e:
        logger.error(f"Config file not found: {file_path}")
        raise ConfigError(f"{file_path} not found") from e
    except yaml.YAMLError as e:
        logger.error(f"Invalid YAML in config file: {filename}")
        raise ConfigError(f"Invalid YAML in {filename}: {e}") from e
    
def load_countries():
    data = load_config("countries.yaml")
    return data["countries"]

def load_commodities():
    data = load_config("commodities.yaml")
    return data["commodities"]

def load_settings():
    return load_config("settings.yaml")

if __name__=="__main__":
    c = load_countries()
    print(c)