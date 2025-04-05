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

from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QComboBox, QLabel, QPushButton, QSpinBox

from difference_viewer.app.config import AppConfig, Theme
from difference_viewer.components.dialog.color_dialog import ColorDialog
from difference_viewer.components.prefs_window.prefs_vm import PrefsViewModel
from difference_viewer.widgets.autoresized import AutoResizedWidget
from difference_viewer.widgets.patch import patch_button_padding_click_detection


class PrefsWindow(AutoResizedWidget):

    def __init__(self, vm: PrefsViewModel) -> None:
        super().__init__(fixSize=True)
        self._vm = vm
        self._init_ui()

        patch_button_padding_click_detection(self)

    def _init_ui(self) -> None:
        uic.loadUi(AppConfig.resource_directory / "prefs_window.ui", self)
        self.btnLineColor: QPushButton
        self.lblLineColor: QLabel
        self.spbLineWidth: QSpinBox
        self.spbBoxPadding: QSpinBox
        self.cbbBoxMergeLevel: QComboBox
        self.cbbTheme: QComboBox
        self.btnOK: QPushButton
        self.btnCancel: QPushButton

        self.setWindowFlags(
            Qt.Window
            | Qt.WindowMinimizeButtonHint
            | Qt.WindowCloseButtonHint
            | Qt.WindowStaysOnTopHint
        )

        self.spbLineWidth.setRange(
            AppConfig.min_line_width,
            AppConfig.max_line_width,
        )
        self.spbBoxPadding.setRange(
            AppConfig.min_bbox_padding,
            AppConfig.max_bbox_padding,
        )
        self.cbbBoxMergeLevel.addItem("なし", 0)
        self.cbbBoxMergeLevel.addItem("1回", 1)
        self.cbbBoxMergeLevel.addItem("2回", 2)
        self.cbbTheme.addItem("ライト", Theme.LIGHT.value)
        self.cbbTheme.addItem("ダーク", Theme.DARK.value)
        self.cbbTheme.addItem("システム設定", Theme.SYSTEM.value)

        self.btnLineColor.setObjectName("icon")
        self.btnOK.setObjectName("accent")

        self.btnLineColor.clicked.connect(self._select_line_color_with_dialog)
        self.spbLineWidth.valueChanged.connect(
            lambda value: self._vm.update_bbox_style(line_width=value)
        )
        self.spbBoxPadding.valueChanged.connect(
            lambda value: self._vm.update_bbox_style(padding=value)
        )
        self.cbbBoxMergeLevel.currentIndexChanged.connect(
            lambda i: self._vm.update_bbox_style(
                merge_level=self.cbbBoxMergeLevel.itemData(i)
            )
        )
        self.cbbTheme.currentIndexChanged.connect(
            lambda i: self._vm.update_theme(self.cbbTheme.itemData(i))
        )

        self.btnOK.clicked.connect(self._save_and_exit)
        self.btnCancel.clicked.connect(self._discard_and_exit)
        self.closeEvent = lambda _: self._discard_and_exit()

        self._set_line_color(self._vm.line_color)
        self.spbLineWidth.setValue(self._vm.line_width)
        self.spbBoxPadding.setValue(self._vm.bbox_padding)
        self.cbbBoxMergeLevel.setCurrentIndex(
            self.cbbBoxMergeLevel.findData(self._vm.bbox_merge_level)
        )
        self.cbbTheme.setCurrentIndex(self.cbbTheme.findData(self._vm.theme))

    def _save_and_exit(self) -> None:
        self._vm.save_config()
        self.close()

    def _discard_and_exit(self) -> None:
        self._vm.reset_config()
        self.close()

    def _select_line_color_with_dialog(self) -> None:
        dialog = ColorDialog(default_color=self._vm.line_color)
        response = dialog.exec_()
        if response == dialog.Rejected:
            return
        color = dialog.get_hex()
        self._set_line_color(color)

    def _set_line_color(self, color: str) -> None:
        self.lblLineColor.setText(color)
        self.btnLineColor.setStyleSheet(f"background-color: {color};")
