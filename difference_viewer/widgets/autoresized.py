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

from PyQt5.QtWidgets import QMainWindow, QWidget


class AutoResizedWidget(QWidget):
    def __init__(self, parent=None, fixSize: bool = False, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.__fix_size = fixSize

    def show(self) -> None:
        super().show()

        self.__handler = self.windowHandle()
        self.__base_dpi = self.__get_current_screen_dpi()
        self.__base_width = self.width()
        self.__base_height = self.height()

        self.__handler.screenChanged.connect(self.__adjust_windowsize_for_dpi)
        self.__adjust_windowsize_for_dpi()

    def __get_current_screen_dpi(self) -> None:
        return self.__handler.screen().logicalDotsPerInch()

    def __adjust_windowsize_for_dpi(self) -> None:
        dpi = self.__get_current_screen_dpi() / self.__base_dpi
        new_width = int(self.__base_width * dpi)
        new_height = int(self.__base_height * dpi)
        if self.__fix_size:
            self.setMinimumSize(new_width, new_height)
            self.setMaximumSize(new_width, new_height)


class AutoResizedMainWindow(QMainWindow, AutoResizedWidget):
    pass
