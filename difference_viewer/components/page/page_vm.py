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

import numpy as np
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QApplication

from difference_viewer.app.config import AppConfig, UserConfig
from difference_viewer.components.dialog.file_dialog import FileOpenDialog
from difference_viewer.components.dialog.loading_dialog import LoadingDialog
from difference_viewer.components.dialog.message_dialog import ErrorDialog
from difference_viewer.components.page.page_model import PageModel
from difference_viewer.core.converter import ConverterFactory
from difference_viewer.core.shared_model import IterationWorker, PageImage


class PageViewModel(QObject):

    loading_started = pyqtSignal()
    loading_finished = pyqtSignal()
    loading_canceled = pyqtSignal()
    image_updated = pyqtSignal()

    def __init__(self, model: PageModel, config: UserConfig) -> None:
        super().__init__()
        self.__logger = logging.getLogger(self.__class__.__name__)
        self._model = model
        self._config = config
        self._file_path = Path()

        self._model.page_changed.connect(self.image_updated.emit)

    def load_file_with_dialog(self) -> None:
        dialog = FileOpenDialog(
            filetypes=ConverterFactory.suffixes(),
            directory=self._config.last_opened_folder,
        )
        response = dialog.exec_()
        self._config.last_opened_folder = dialog.directory().path()
        if response == FileOpenDialog.Rejected:
            return

        fp = Path(dialog.selectedFiles()[0])
        self.__logger.debug(f'File selected from dialog: "{fp.as_posix()}"')
        self.load_file(fp)

        try:
            self._config.save(AppConfig.user_config_file_path())
        except Exception as e:
            pass

    def load_file(self, fp: Path) -> None:
        self.__logger.info("Loading file")
        try:
            converter = ConverterFactory.create(fp)
            worker = IterationWorker(iterable=converter.iter_image)
            dialog = LoadingDialog()
            pages = []
            first_iter = True

            def _on_yielded(img: np.ndarray) -> None:
                nonlocal first_iter
                if first_iter:
                    dialog.setMaximum(converter.length())
                    first_iter = False
                pages.append(PageImage(img, loading_size=AppConfig.page_size))
                dialog.update()

            def _on_finished() -> None:
                self._file_path = fp
                worker.deleteLater()
                dialog.finalize()
                dialog.close()
                self._model.load(pages)
                self.__logger.info("File loaded successfully")
                self.loading_finished.emit()
                self.turn_first()

            def _on_aborted() -> None:
                worker.abort()
                worker.wait()
                worker.deleteLater()
                dialog.close()
                self.__logger.info("File loading canceled")
                self.loading_canceled.emit()

            worker.yielded.connect(_on_yielded)
            worker.finished.connect(_on_finished)
            dialog.canceled.connect(_on_aborted)
            self.loading_started.emit()
            dialog.show()
            QApplication.processEvents()
            worker.start()

        except Exception as e:
            self.__logger.error(f"Error occurred while loading file: {e}")
            dialog.close()
            worker.deleteLater()

            if isinstance(e, FileNotFoundError):
                ErrorDialog("ファイルが存在しません。").show()
            else:
                ErrorDialog("ファイル読み込み中にエラーが発生しました").show()

    def reload_file(self) -> None:
        self.load_file(self._file_path)

    def turn_first(self) -> None:
        self.turn_page(1)

    def turn_prev(self) -> None:
        self.turn_page(self._model.page - 1)

    def turn_next(self) -> None:
        self.turn_page(self._model.page + 1)

    def turn_last(self) -> None:
        self.turn_page(self._model.max_page)

    def turn_page(self, page: int) -> None:
        if 1 <= page <= self._model.max_page:
            self._model.page = page
            self.__logger.debug(f"Page turned: {page} (id: {id(self)})")

    def has_image(self) -> bool:
        return self._model.max_page > 0

    @property
    def image(self) -> PageImage:
        return self._model.current_image()

    @property
    def page(self) -> int:
        return self._model.page

    @property
    def max_page(self) -> int:
        return self._model.max_page

    @property
    def file_path(self) -> str:
        return self._file_path.as_posix()

    @property
    def file_suffix(self) -> str:
        return self._file_path.suffix
