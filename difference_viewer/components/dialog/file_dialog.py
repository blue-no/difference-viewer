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

from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFileDialog


class FileOpenDialog(QFileDialog):

    def __init__(
        self,
        filetypes: list[str],
        directory: str | None = None,
    ) -> None:
        super().__init__()
        filter = " ".join([f"*{t.lower()} *{t.upper()}" for t in filetypes])
        if directory is None or not Path(directory).exists():
            directory = Path.home().as_posix()

        super().__init__(
            caption="ファイルを開く",
            filter=f"ファイル ({filter})",
            directory=directory,
        )
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
