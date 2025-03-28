# Copyright (C) 2025 Blueno
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

from __future__ import annotations

import getpass
import json
import logging
import os
import re
import winreg
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any, ClassVar

from PyQt5.QtWidgets import QApplication


class Theme(Enum):

    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


def get_system_theme() -> Theme:
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            if value == 0:
                return Theme.DARK
            else:
                return Theme.LIGHT
    except Exception:
        return Theme.LIGHT


def apply_theme(theme: Theme) -> None:
    if theme == Theme.SYSTEM:
        theme = get_system_theme()
    qss_fp = AppConfig.resource_directory / "styles" / (theme.value + ".qss")
    with qss_fp.open("r", encoding="utf-8") as f:
        style = f.read()
    QApplication.instance().setStyleSheet(style)


class AppConfig:

    app_name = "Difference Viewer"
    src_name = "difference_viewer"
    user_name = getpass.getuser()
    user_config_name = "user_config.json"
    app_config_name = "config.json"

    root_directory = Path(__file__).parent.parent.parent
    working_directory = Path(os.environ.get("LOCALAPPDATA")) / app_name
    log_directory = root_directory / "log"
    resource_directory = root_directory / src_name / "resources"

    log_level = logging.DEBUG
    max_scale = 10.0
    min_scale = 0.1
    zoom_factor = 1.15
    page_size = (2560, 2560)
    max_line_width = 15
    min_line_width = 1
    max_bbox_padding = 20
    min_bbox_padding = -10
    bbox_merge_levels = [0, 1, 2, 3]

    __logger = logging.getLogger("AppConfig")

    @classmethod
    def override_config_from_json(cls, fp: Path) -> None:
        try:
            with fp.open("r") as f:
                data = json.loads(f.read())
                for key, value in data.items():
                    if hasattr(cls, key):
                        type_ = type(getattr(cls, key))
                        value = _replace_env_vars(value)
                        setattr(cls, key, type_(value))
                    else:
                        cls.__logger.warning(f"Invalid key skipped: {key}")

        except Exception as e:
            cls.__logger.warning(
                f"Failed to override config from file: {str(e)}"
            )

    @classmethod
    def app_config_file_path(cls) -> Path:
        return cls.root_directory / cls.app_config_name

    @classmethod
    def user_config_file_path(cls) -> Path:
        return cls.working_directory / cls.user_config_name


@dataclass
class UserConfig:

    last_opened_folder: str
    line_color: str
    line_width: int
    bbox_padding: int
    bbox_merge_level: int
    theme: str

    __logger: ClassVar[logging.Logger] = logging.getLogger("UserConfig")

    @classmethod
    def load(cls, fp: Path) -> UserConfig:
        try:
            with fp.open("r") as f:
                jsn: dict[str, Any] = json.load(f)
            data = cls._load_default()
            for key, value in jsn.items():
                if not hasattr(data, key):
                    cls.__logger.warning(
                        f"Key skipped while loading user config: {key}"
                    )
                    continue
                if type(getattr(data, key)) != type(value):
                    cls.__logger.warning(
                        f"Default value will be used for key: {key}"
                    )
                    continue
                setattr(data, key, value)
            cls.__logger.info("Custom user config loaded")

        except Exception as e:
            cls.__logger.warning(f"Failed to load user config: {str(e)}")
            data = cls._load_default()
            try:
                data.save(fp)
            except Exception:
                pass

        return data

    def save(self, fp: Path) -> None:
        if not fp.parent.exists():
            fp.parent.mkdir(parents=True)
        try:
            with fp.open("w") as f:
                json.dump(asdict(self), f, indent=4)
            self.__logger.info("User config saved")
        except Exception as e:
            self.__logger.warning(f"Failed to save user config: {str(e)}")
            raise e

    @classmethod
    def _load_default(cls) -> UserConfig:
        data = cls(
            last_opened_folder=Path.home().as_posix(),
            line_color="#FF4081",
            line_width=3,
            bbox_padding=5,
            bbox_merge_level=1,
            theme="system",
        )
        cls.__logger.info("Default config loaded")
        return data


def _replace_env_vars(input_str):
    pattern = r"%([^%]+)%"

    def replace_match(match):
        var_name = match.group(1)
        return os.getenv(var_name, "")

    result = re.sub(pattern, replace_match, input_str)
    return result
