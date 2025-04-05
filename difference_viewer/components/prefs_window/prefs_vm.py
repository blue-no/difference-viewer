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

from dataclasses import asdict

from PyQt5.QtCore import QObject, pyqtSignal

from difference_viewer.app.config import AppConfig, UserConfig


class PrefsViewModel(QObject):
    bbox_style_changed = pyqtSignal()
    window_style_changed = pyqtSignal()

    def __init__(self, config: UserConfig) -> None:
        super().__init__()
        self._config = config
        self._default_config = UserConfig(**asdict(config))

    def update_bbox_style(
        self,
        line_color: str | None = None,
        line_width: int | None = None,
        padding: str | None = None,
        merge_level: int | None = None,
    ) -> None:
        if line_color is not None:
            self._config.line_color = line_color
        if line_width is not None:
            if (
                AppConfig.min_line_width
                <= line_width
                <= AppConfig.max_line_width
            ):
                self._config.line_width = line_width
        if padding is not None:
            if (
                AppConfig.min_bbox_padding
                <= padding
                <= AppConfig.max_bbox_padding
            ):
                self._config.bbox_padding = padding
        if merge_level is not None:
            if merge_level in AppConfig.bbox_merge_levels:
                self._config.bbox_merge_level = merge_level
        self.bbox_style_changed.emit()

    def update_window_style(self, theme: str) -> None:
        self._config.theme = theme
        self.window_style_changed.emit()

    def save_config(self) -> None:
        self._config.save(AppConfig.user_config_file_path())
        self._default_config = UserConfig(**asdict(self._config))

    def reset_config(self) -> None:
        self.update_bbox_style(
            line_color=self._default_config.line_color,
            line_width=self._default_config.line_width,
            padding=self._default_config.bbox_padding,
            merge_level=self._default_config.bbox_merge_level,
        )
        self.update_window_style(self._default_config.theme)

    @property
    def line_color(self) -> str:
        return self._config.line_color

    @property
    def line_width(self) -> int:
        return self._config.line_width

    @property
    def bbox_padding(self) -> int:
        return self._config.bbox_padding

    @property
    def bbox_merge_level(self) -> int:
        return self._config.bbox_merge_level

    @property
    def theme(self) -> str:
        return self._config.theme
