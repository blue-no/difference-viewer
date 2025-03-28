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

from PyQt5.QtCore import QObject, QPointF, pyqtSignal


class DisplayModel(QObject):

    scale_changed = pyqtSignal(float, QPointF)
    pos_changed = pyqtSignal(int, int)

    def __init__(self) -> None:
        super().__init__()
        self._last_scale = None
        self._last_pos = None

    @property
    def last_scale(self) -> float:
        return self._last_scale

    @property
    def last_pos(self) -> tuple[int, int]:
        return self._last_pos

    def update_scale(self, scale, center) -> None:
        self._last_scale = scale
        self._last_scaling_center = center
        self.scale_changed.emit(scale, center)

    def update_pos(self, h_pos, v_pos) -> None:
        self._last_pos = (h_pos, v_pos)
        self.pos_changed.emit(h_pos, v_pos)
