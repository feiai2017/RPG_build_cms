# -*- coding: utf-8 -*-
"""
Centralized application configuration.
"""

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class AppConfig:
    config_root: str
    log_path: str
    app_env: str


def load_config() -> AppConfig:
    config_root = os.getenv("RPG_CONFIG_DIR", ".kiro/rpg_config")
    log_path = os.getenv("RPG_LOG_PATH", str(Path(config_root) / "system.log"))
    app_env = os.getenv("RPG_ENV", "development")
    return AppConfig(
        config_root=config_root,
        log_path=log_path,
        app_env=app_env,
    )


_CONFIG: Optional[AppConfig] = None


def get_app_config() -> AppConfig:
    global _CONFIG
    if _CONFIG is None:
        _CONFIG = load_config()
    return _CONFIG
