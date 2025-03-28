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
import os
from datetime import datetime

import psutil

from difference_viewer.app.config import AppConfig


class CustomFormatter(logging.Formatter):

    def format(self, record: logging.LogRecord) -> str:
        record.name = record.name.ljust(16)
        return super().format(record)

    def formatTime(
        self,
        record: logging.LogRecord,
        datefmt: str | None = None,
    ) -> str:
        ct = datetime.fromtimestamp(record.created)
        formatted_time = (
            ct.strftime("%H:%M:%S") + f".{int(record.msecs*1000):06d}"
        )
        return formatted_time


def setup_logger() -> None:
    logging.getLogger("PyQt5").setLevel(logging.CRITICAL)
    logging.getLogger("PIL").setLevel(logging.CRITICAL)

    log_dir = AppConfig.log_directory / AppConfig.user_name
    formatter = CustomFormatter(
        "%(asctime)s\t%(levelname)s\t%(name)s\t%(message)s",
        datefmt="%H:%M:%S",
    )
    handlers = []

    try:
        log_dir.mkdir(parents=True, exist_ok=True)

        file_name = str(datetime.today().date())
        file_handler = logging.FileHandler(
            f"{log_dir / file_name}.log",
            mode="a",
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)
    except PermissionError:
        pass

    process_name = psutil.Process(os.getpid()).name().lower()
    if process_name == "python.exe":
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        handlers.append(stream_handler)

    logging.basicConfig(level=AppConfig.log_level, handlers=handlers)
