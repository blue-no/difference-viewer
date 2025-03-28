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

from PyQt5.QtCore import QObject, pyqtSignal


class MainWindowViewModel(QObject):
    warninig_visiblity_changed = pyqtSignal(str, bool)
    button_state_changed = pyqtSignal(str, bool)
    window_state_changed = pyqtSignal(bool)

    turn_first_requested = pyqtSignal()
    turn_prev_requested = pyqtSignal()
    turn_next_requested = pyqtSignal()
    turn_last_requested = pyqtSignal()
    reset_view_requested = pyqtSignal()
    open_prefs_requested = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()

    def switch_warning_visibility(
        self,
        target: Literal["size", "type"],
        visible: bool,
    ) -> None:
        self.warninig_visiblity_changed.emit(target, visible)

    def switch_button_state(
        self,
        target: Literal["fit", "turn"],
        enabled: bool,
    ) -> None:
        self.button_state_changed.emit(target, enabled)

    def switch_window_state(self, enabled: bool) -> None:
        self.window_state_changed.emit(enabled)
