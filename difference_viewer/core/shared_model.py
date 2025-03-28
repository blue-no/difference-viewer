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

from typing import Any, Callable, Generator

import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap

try:
    from PIL import Image

    def _hq_resize(image: np.ndarray, h: int, w: int) -> np.ndarray:
        pil_image = Image.fromarray(image.astype(np.uint8))
        return np.array(pil_image.resize((w, h), Image.LANCZOS))

except ImportError:
    import cv2

    def _hq_resize(image: np.ndarray, h: int, w: int) -> np.ndarray:
        return cv2.resize(image, (h, w), interpolation=cv2.INTER_AREA)


def ndarray_to_pixmap(arr: np.ndarray) -> QPixmap:
    h, w = arr.shape[:2]
    return QPixmap(QImage(arr.data, w, h, 3 * w, QImage.Format_RGB888))


class PageImage:

    def __init__(
        self,
        image: np.ndarray,
        loading_size: tuple[int, int] | None = None,
    ) -> None:
        h, w = image.shape[:2]
        if loading_size is not None:
            load_h, load_w = loading_size
            scale = min(load_h / h, load_w / w)
            new_h, new_w = int(h * scale), int(w * scale)
            self._image = _hq_resize(image, new_h, new_w)
        else:
            self._image = image
        self._default_shape = (h, w)

    @property
    def shape(self) -> tuple[int, int]:
        return self._default_shape

    @property
    def data(self) -> np.ndarray:
        return self._image


class IterationWorker(QThread):

    yielded = pyqtSignal(object)
    finished = pyqtSignal()
    aborted = pyqtSignal()

    def __init__(
        self,
        iterable: Callable[[], Generator[Any, None, None]],
    ) -> None:
        super().__init__()
        self._iterable_target = iterable
        self._is_aborted = False

    def run(self) -> None:
        try:
            for ret in self._iterable_target():
                if self._is_aborted:
                    self.aborted.emit()
                    return

                self.yielded.emit(ret)
            self.finished.emit()
        except Exception as e:
            raise e

    def abort(self) -> None:
        self._is_aborted = True
