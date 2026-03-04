"""
Configuration loading utilities for vision pipeline.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional


def load_vision_config(path: str = "configs/vision.yaml") -> Dict[str, Any]:
    """
    Load vision pipeline configuration from YAML file.
    
    Expected YAML structure:
    ```
    sam:
      config_path: "configs/sam2/sam2.1_hiera_l.yaml"
      checkpoint_path: "checkpoints/sam2.1_hiera_large.pt"
      device: "cuda"
    furniture:
      table_min_area: 5000.0
      table_max_area: 50000.0
      chair_min_area: 2000.0
      chair_max_area: 20000.0
    ```
    
    Args:
        path: Path to vision config YAML file (default: configs/vision.yaml)
    
    Returns:
        Dictionary with 'sam' and 'furniture' keys containing configurations
    
    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If YAML parsing fails
    """
    config_path = Path(path)
    
    if not config_path.exists():
        raise FileNotFoundError(f"Vision config file not found: {path}")
    
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    
    if config is None:
        config = {}
    
    # Ensure required sections exist with defaults
    if "sam" not in config:
        config["sam"] = {}
    
    if "furniture" not in config:
        config["furniture"] = {}
    
    # Apply SAM2.1 defaults if not specified
    sam_config = config["sam"]
    sam_config.setdefault("config_path", "configs/sam2/sam2.1_hiera_l.yaml")
    sam_config.setdefault("checkpoint_path", "checkpoints/sam2.1_hiera_large.pt")
    sam_config.setdefault("device", "cuda")
    
    # Apply furniture filtering defaults if not specified
    furniture_config = config["furniture"]
    furniture_config.setdefault("table_min_area", 5000.0)
    furniture_config.setdefault("table_max_area", 50000.0)
    furniture_config.setdefault("chair_min_area", 2000.0)
    furniture_config.setdefault("chair_max_area", 20000.0)
    
    return config


def get_sam_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract SAM configuration from vision config.
    
    Args:
        config: Dictionary returned by load_vision_config()
    
    Returns:
        Dictionary with 'config_path', 'checkpoint_path', 'device'
    """
    return config.get("sam", {})


def get_furniture_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract furniture filtering configuration from vision config.
    
    Args:
        config: Dictionary returned by load_vision_config()
    
    Returns:
        Dictionary with 'table_min_area', 'table_max_area', 'chair_min_area', 'chair_max_area'
    """
    return config.get("furniture", {})
