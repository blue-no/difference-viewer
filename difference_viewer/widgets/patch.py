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

from PyQt5.QtCore import QPoint
from PyQt5.QtWidgets import QPushButton, QWidget


def patch_button_padding_click_detection(widget: QWidget) -> None:
    for child in widget.findChildren(QPushButton):

        def make_handler(button: QPushButton) -> callable:
            def handler(pos: QPoint) -> bool:
                return True

            return handler

        child.hitButton = make_handler(child)
