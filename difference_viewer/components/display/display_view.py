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

from PyQt5 import uic
from PyQt5.QtCore import QPoint, QPointF, QRectF, Qt, pyqtSlot
from PyQt5.QtGui import (
    QDragEnterEvent,
    QDragLeaveEvent,
    QDragMoveEvent,
    QDropEvent,
    QMouseEvent,
    QPixmap,
    QWheelEvent,
)
from PyQt5.QtWidgets import (
    QGraphicsPixmapItem,
    QGraphicsScene,
    QGraphicsView,
    QLabel,
    QWidget,
)

from difference_viewer.app.config import AppConfig
from difference_viewer.components.display.display_vm import DisplayViewModel
from difference_viewer.core.converter import ConverterFactory
from difference_viewer.widgets.patch import patch_button_padding_click_detection


class DisplayView(QWidget):

    def __init__(self, vm: DisplayViewModel) -> None:
        super().__init__()
        self.__logger = logging.getLogger(self.__class__.__name__)
        self._vm = vm
        self._dropped_fp = None

        self.__fit_factor = 0.99
        self.__center_offset = QPointF(0.2, 0.2)

        self._vm.pixmap_updated.connect(self._update_display)
        self._vm.view_reset_requested.connect(self._reset_view)
        self._vm.zoom_requested.connect(self._apply_zoom)
        self._vm.scroll_requested.connect(self._apply_scroll)
        self._init_ui()
        
        patch_button_padding_click_detection(self)

    def _init_ui(self) -> None:
        uic.loadUi(AppConfig.resource_directory / "display.ui", self)
        self.lblMessage: QLabel
        self.gfxView: QGraphicsView

        self.gfxScene = QGraphicsScene(parent=self)
        self.pixmapItem = QGraphicsPixmapItem()

        self.gfxScene.addItem(self.pixmapItem)
        self.gfxView.setScene(self.gfxScene)

        self.lblMessage.dragEnterEvent = self.__drag_enter_event
        self.lblMessage.dragMoveEvent = self.__drag_move_event
        self.lblMessage.dragLeaveEvent = self.__drag_leave_event
        self.lblMessage.dropEvent = self.__drop_event

        self.gfxScene.dragEnterEvent = self.__drag_enter_event
        self.gfxScene.dragMoveEvent = self.__drag_move_event
        self.gfxScene.dragLeaveEvent = self.__drag_leave_event
        self.gfxScene.dropEvent = self.__drop_event

        self.gfxView.wheelEvent = self.__wheel_event
        self.gfxView.originalMouseMoveEvent = self.gfxView.mouseMoveEvent
        self.gfxView.originalScrollContentsBy = self.gfxView.scrollContentsBy
        self.gfxView.mouseMoveEvent = self.__mouse_move_event
        self.gfxView.scrollContentsBy = self.__scroll_contents_by
        self.gfxView.mouseDoubleClickEvent = self.__mouse_double_click_event

        self.gfxView.setObjectName("droppable")
        self.lblMessage.setObjectName("droppable")

    @pyqtSlot(QPixmap)
    def _update_display(self, pixmap: QPixmap) -> None:
        if self.lblMessage is not None:
            self.lblMessage.deleteLater()
            self.lblMessage = None
        rect = QRectF(0, 0, pixmap.width(), pixmap.height())
        self.gfxView.setSceneRect(rect)
        self.gfxScene.setSceneRect(rect)
        self.pixmapItem.setPixmap(pixmap)

    @pyqtSlot(float, QPointF)
    def _apply_zoom(self, scale: float, center: QPointF) -> None:
        relative_scale = scale / self.gfxView.transform().m11()
        self.gfxView.scale(relative_scale, relative_scale)
        self.gfxView.centerOn(center + self.__center_offset)

    @pyqtSlot(int, int)
    def _apply_scroll(self, h_pos: int, v_pos: int) -> None:
        self.gfxView.horizontalScrollBar().setValue(h_pos)
        self.gfxView.verticalScrollBar().setValue(v_pos)

    @pyqtSlot()
    def _reset_view(self) -> None:
        if self.pixmapItem.pixmap().isNull():
            return
        self._vm.zoom_to(
            scale=self._fit_scale(),
            center=self._fit_center(),
        )

    def _fit_scale(self) -> float:
        viewport_size = self.size()
        viewport_width = viewport_size.width()
        viewport_height = viewport_size.height()

        item_rect = self.pixmapItem.boundingRect()
        item_width = item_rect.width()
        item_height = item_rect.height()

        scale_x = viewport_width / item_width
        scale_y = viewport_height / item_height

        return min(scale_x, scale_y) * self.__fit_factor

    def _fit_center(self) -> QPoint:
        item_rect = self.pixmapItem.boundingRect()
        center_x = item_rect.center().x()
        center_y = item_rect.center().y()

        return QPoint(center_x, center_y)

    def __drag_enter_event(self, event: QDragEnterEvent) -> None:
        mime_data = event.mimeData()
        if not mime_data.hasUrls():
            return event.ignore()

        urls = mime_data.urls()
        if len(urls) > 1:
            return event.ignore()

        fp = Path(urls[0].toLocalFile())
        if fp.suffix.lower() not in ConverterFactory.suffixes():
            event.ignore()
            self.__logger.debug(f"File drop event ignored: {fp.suffix}")
            return
        self._dropped_fp = fp

        self.__update_droparea_style(dragging=True)
        event.accept()

    def __drag_move_event(self, event: QDragMoveEvent) -> None:
        event.accept()

    def __drop_event(self, event: QDropEvent) -> None:
        if self._dropped_fp is None:
            return event.ignore()
        self.__logger.debug(
            f"File drop event accepted: {self._dropped_fp.suffix}"
        )
        self._vm.accept_file(self._dropped_fp)

        self.__update_droparea_style(dragging=False)
        event.accept()

    def __drag_leave_event(self, event: QDragLeaveEvent) -> None:
        self.__update_droparea_style(dragging=False)
        event.accept()

    def __wheel_event(self, event: QWheelEvent) -> None:
        mouse_pos = self.gfxView.mapToScene(event.pos())
        view_center = self.gfxView.mapToScene(
            self.gfxView.viewport().rect().center()
        )

        if event.angleDelta().y() >= 0:
            self._vm.zoom_in(
                view_center=view_center,
                mouse_pos=mouse_pos,
            )
        else:
            self._vm.zoom_out(
                view_center=view_center,
                mouse_pos=mouse_pos,
            )

    def __mouse_move_event(self, event: QMouseEvent) -> None:
        self.gfxView.originalMouseMoveEvent(event)
        if event.buttons() == Qt.LeftButton:
            self._vm.scroll_to(
                self.gfxView.horizontalScrollBar().value(),
                self.gfxView.verticalScrollBar().value(),
            )

    def __scroll_contents_by(self, dx: int, dy: int) -> None:
        self.gfxView.originalScrollContentsBy(dx, dy)
        self._vm.scroll_to(
            self.gfxView.horizontalScrollBar().value(),
            self.gfxView.verticalScrollBar().value(),
        )

    def __update_droparea_style(self, dragging: bool) -> None:
        self.gfxView.setProperty("dragging", dragging)
        self.gfxView.style().polish(self.gfxView)

        if self.lblMessage is not None:
            self.lblMessage.setProperty("dragging", dragging)
            self.lblMessage.style().polish(self.lblMessage)

    def __mouse_double_click_event(self, event: QMouseEvent) -> None:
        self._vm.view_reset_requested.emit()
