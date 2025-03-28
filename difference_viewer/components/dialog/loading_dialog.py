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
from PyQt5.QtWidgets import QProgressDialog


class LoadingDialog(QProgressDialog):

    def __init__(self) -> None:
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.setMinimumWidth(300)
        self.setWindowTitle("ページ読込")
        self.setLabelText("ページ読込中...")
        self.setCancelButtonText("キャンセル")
        self.setMinimumDuration(0)
        self.setAutoReset(False)
        self.setAutoClose(False)
        self.setValue(0)

    def update(self) -> None:
        self.setValue(min(self.value() + 1, self.maximum()))

    def finalize(self) -> None:
        self.setValue(self.maximum())
