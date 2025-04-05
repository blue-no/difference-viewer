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

from typing import Literal

from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QKeyEvent, QMouseEvent
from PyQt5.QtWidgets import QBoxLayout, QFrame, QLabel, QPushButton, QWidget

from difference_viewer.app.config import AppConfig, get_resource_icon_path
from difference_viewer.components.main_window.main_vm import MainWindowViewModel
from difference_viewer.widgets.autoresized import AutoResizedMainWindow
from difference_viewer.widgets.patch import patch_button_padding_click_detection


class MainWindow(AutoResizedMainWindow):

    def __init__(self, vm: MainWindowViewModel) -> None:
        super().__init__()
        self._vm = vm
        self._vm.warninig_visiblity_changed.connect(
            lambda t, v: self._update_label_visibility(t, v)
        )
        self._vm.button_state_changed.connect(
            lambda t, e: self._update_button_state(t, e)
        )
        self._vm.window_state_changed.connect(self._update_window_state)
        self._init_ui()

        patch_button_padding_click_detection(self)

    def _init_ui(self) -> None:
        uic.loadUi(AppConfig.resource_directory / "main_window.ui", self)
        self.btnSyncTurnFirst: QPushButton
        self.btnSyncTurnPrev: QPushButton
        self.btnSyncTurnNext: QPushButton
        self.btnSyncTurnLast: QPushButton
        self.btnFitPage: QPushButton
        self.lblSizeWarning: QLabel
        self.lblTypeWarning: QLabel
        self.lytPageL: QBoxLayout
        self.lytPageR: QBoxLayout
        self.frame: QFrame
        self.btnOpenPrefs: QPushButton

        self.btnSyncTurnFirst.setObjectName("accent")
        self.btnSyncTurnPrev.setObjectName("accent")
        self.btnSyncTurnNext.setObjectName("accent")
        self.btnSyncTurnLast.setObjectName("accent")
        self.btnOpenPrefs.setObjectName("icon")
        self.frame.setObjectName("line")

        self.btnSyncTurnFirst.clicked.connect(
            self._vm.turn_first_requested.emit
        )
        self.btnSyncTurnPrev.clicked.connect(self._vm.turn_prev_requested.emit)
        self.btnSyncTurnNext.clicked.connect(self._vm.turn_next_requested.emit)
        self.btnSyncTurnLast.clicked.connect(self._vm.turn_last_requested.emit)

        self.btnFitPage.clicked.connect(self._vm.reset_view_requested.emit)
        self.btnOpenPrefs.clicked.connect(self._vm.open_prefs_requested.emit)

        self.keyPressEvent = self.__key_press_event
        self.mousePressEvent = self.__mouse_press_event

        self.labels = {
            "size": self.lblSizeWarning,
            "type": self.lblTypeWarning,
        }
        self.buttons = {
            "fit": self.btnFitPage,
            "turn": [
                self.btnSyncTurnFirst,
                self.btnSyncTurnPrev,
                self.btnSyncTurnNext,
                self.btnSyncTurnLast,
            ],
        }

    def put_widget(self, widget: QWidget, loc: Literal["L", "R"]) -> None:
        if loc == "L":
            self.lytPageL.addWidget(widget)
        elif loc == "R":
            self.lytPageR.addWidget(widget)
        else:
            raise ValueError(f"Invalid location: {loc}")

    def apply_icon_style(self, name: str) -> None:
        self.btnOpenPrefs.setIcon(
            QIcon(get_resource_icon_path(name + "/gear").as_posix())
        )

    def _update_label_visibility(self, target: str, visible: bool) -> None:
        self.labels[target].setVisible(visible)

    def _update_button_state(self, target: str, enabled: bool) -> None:
        if isinstance(self.buttons[target], list):
            for button in self.buttons[target]:
                button.setEnabled(enabled)
        else:
            self.buttons[target].setEnabled(enabled)

    def _update_window_state(self, enabled: bool) -> None:
        self.setEnabled(enabled)

    def __key_press_event(self, event: QKeyEvent) -> None:
        cmd = event.key()
        if cmd == Qt.Key_Home:
            self.btnSyncTurnFirst.click()
        elif cmd == Qt.Key_PageUp:
            self.btnSyncTurnPrev.click()
        elif cmd == Qt.Key_PageDown:
            self.btnSyncTurnNext.click()
        elif cmd == Qt.Key_End:
            self.btnSyncTurnLast.click()

    def __mouse_press_event(self, event: QMouseEvent) -> None:
        cmd = event.button()
        if cmd == Qt.BackButton:
            self.btnSyncTurnPrev.click()
        elif cmd == Qt.ForwardButton:
            self.btnSyncTurnNext.click()
