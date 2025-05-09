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

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QColorDialog

from difference_viewer.app.config import AppConfig
from difference_viewer.widgets.patch import patch_button_padding_click_detection


class ColorDialog(QColorDialog):

    def __init__(self, parent=None, default_color: str | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("色の選択")
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        if default_color is not None:
            self.setCurrentColor(QColor(default_color))

        patch_button_padding_click_detection(self)

        qss_fp = AppConfig.resource_directory / "styles" / "dialog.qss"
        try:
            with qss_fp.open("r", encoding="utf-8") as f:
                style = f.read()
            self.setStyleSheet(style)
        except FileNotFoundError:
            pass

    def get_hex(self) -> str:
        return self.selectedColor().name()
