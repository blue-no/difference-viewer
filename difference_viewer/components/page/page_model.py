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

from PyQt5.QtCore import QObject, pyqtProperty, pyqtSignal

from difference_viewer.core.shared_model import PageImage


class PageModel(QObject):

    page_changed = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self._images = []
        self._curr_page = 1

    @property
    def max_page(self) -> int:
        return len(self._images)

    def load(self, page_images: list[PageImage]) -> None:
        self._images = page_images

    @pyqtProperty(int, notify=page_changed)
    def page(self) -> int:
        return self._curr_page

    @page.setter
    def page(self, page: int) -> None:
        self._curr_page = min(max(1, page), self.max_page)
        self.page_changed.emit()

    def current_image(self) -> PageImage:
        return self._images[self._curr_page - 1]
