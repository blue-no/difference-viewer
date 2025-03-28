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

import logging
from pathlib import Path

from PyQt5.QtCore import QObject, QPointF, pyqtSignal
from PyQt5.QtGui import QPixmap

from difference_viewer.app.config import AppConfig, UserConfig
from difference_viewer.components.display.display_model import DisplayModel


class DisplayViewModel(QObject):

    file_accepted = pyqtSignal(Path)
    pixmap_updated = pyqtSignal(QPixmap)
    zoom_requested = pyqtSignal(float, QPointF)
    scroll_requested = pyqtSignal(int, int)
    view_reset_requested = pyqtSignal()

    def __init__(self, model: DisplayModel, config: UserConfig) -> None:
        super().__init__()
        self.__logger = logging.getLogger(self.__class__.__name__)
        self._model = model
        self._config = config
        self._fp = None

        self._model.scale_changed.connect(self.zoom_requested.emit)
        self._model.pos_changed.connect(self.scroll_requested.emit)

    def accept_file(self, fp: Path) -> None:
        self.__logger.debug(f'File dropped: "{fp.as_posix()}"')
        if fp == self._fp:
            return
        self._fp = fp
        self._config.last_opened_folder = fp.parent.as_posix()
        try:
            self._config.save(AppConfig.user_config_file_path())
        except Exception as e:
            pass
        self.file_accepted.emit(fp)

    def update_pixmap(self, pixmap: QPixmap) -> None:
        self.pixmap_updated.emit(pixmap)
        self.reset_view()

    def reset_view(self) -> None:
        self.view_reset_requested.emit()

    def zoom_in(self, view_center: QPointF, mouse_pos: QPointF) -> None:
        factor = AppConfig.zoom_factor
        new_scale = self._model.last_scale * factor
        if new_scale > AppConfig.max_scale:
            new_scale = AppConfig.max_scale
            factor = AppConfig.max_scale / self._model.last_scale
        new_center = mouse_pos + (view_center - mouse_pos) / factor

        self.zoom_to(scale=new_scale, center=new_center)

    def zoom_out(self, view_center: QPointF, mouse_pos: QPointF) -> None:
        factor = 1 / AppConfig.zoom_factor
        new_scale = self._model.last_scale * factor
        if new_scale < AppConfig.min_scale:
            new_scale = AppConfig.min_scale
            factor = AppConfig.min_scale / self._model.last_scale
        new_center = mouse_pos + (view_center - mouse_pos) / factor

        self.zoom_to(scale=new_scale, center=new_center)

    def zoom_to(self, scale: float, center: QPointF) -> None:
        self._model.update_scale(scale, center)

    def scroll_to(self, h_pos: int, v_pos: int) -> None:
        self._model.update_pos(h_pos, v_pos)
