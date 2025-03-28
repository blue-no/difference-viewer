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
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from difference_viewer.app.config import AppConfig
from difference_viewer.components.page.page_vm import PageViewModel


class PageView(QWidget):

    def __init__(self, vm: PageViewModel) -> None:
        super().__init__()
        self._vm = vm
        self._vm.loading_finished.connect(self._enable_widgets)
        self._vm.loading_finished.connect(self._update_file_info)
        self._vm.image_updated.connect(self._update_page_info)

        self._init_ui()

    def _init_ui(self) -> None:
        uic.loadUi(AppConfig.resource_directory / "page.ui", self)
        self.btnSelectFile: QPushButton
        self.txtFilePath: QLineEdit
        self.btnReload: QPushButton
        self.btnTurnFirst: QPushButton
        self.btnTurnPrev: QPushButton
        self.btnTurnNext: QPushButton
        self.btnTurnLast: QPushButton
        self.txtCurPage: QLineEdit
        self.lblTotalPage: QLabel
        self.lytPage: QVBoxLayout

        self.page_validator = QIntValidator()
        self.txtCurPage.setValidator(self.page_validator)

        self.btnSelectFile.clicked.connect(self._vm.load_file_with_dialog)
        self.btnReload.clicked.connect(self._vm.reload_file)
        self.btnTurnFirst.clicked.connect(self._vm.turn_first)
        self.btnTurnPrev.clicked.connect(self._vm.turn_prev)
        self.btnTurnNext.clicked.connect(self._vm.turn_next)
        self.btnTurnLast.clicked.connect(self._vm.turn_last)
        self.txtCurPage.editingFinished.connect(self._on_page_editing_finished)

        self.btnSelectFile.setObjectName("folder")
        self.btnReload.setObjectName("reload")

        self.txtFilePath.setReadOnly(True)
        self.lblTotalPage.setText("-")
        self._disable_widgets()

    def put_widget(self, widget: QWidget) -> None:
        self.lytPage.addWidget(widget)

    @pyqtSlot()
    def _update_file_info(self) -> None:
        self.lblTotalPage.setText(str(self._vm.max_page))
        self.txtFilePath.setText(self._vm.file_path)

    @pyqtSlot()
    def _update_page_info(self) -> None:
        self.txtCurPage.setText(str(self._vm.page))

    def _disable_widgets(self) -> None:
        self.btnTurnFirst.setEnabled(False)
        self.btnTurnPrev.setEnabled(False)
        self.btnTurnNext.setEnabled(False)
        self.btnTurnLast.setEnabled(False)
        self.txtCurPage.setEnabled(False)
        self.btnReload.setEnabled(False)

    @pyqtSlot()
    def _enable_widgets(self) -> None:
        self.btnTurnFirst.setEnabled(True)
        self.btnTurnPrev.setEnabled(True)
        self.btnTurnNext.setEnabled(True)
        self.btnTurnLast.setEnabled(True)
        self.txtCurPage.setEnabled(True)
        self.btnReload.setEnabled(True)

    def _on_page_editing_finished(self) -> None:
        page = int(self.txtCurPage.text())
        if 1 <= page <= self._vm.max_page:
            self._vm.turn_page(page)
            return
        self.txtCurPage.setText(str(self._vm.page))
