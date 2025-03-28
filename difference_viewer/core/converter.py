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
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Generator, Type

import cv2
import numpy as np

from difference_viewer.app.config import AppConfig


def imread(fp: Path | str) -> np.ndarray:
    fp = Path(fp)
    if not fp.is_file():
        raise FileNotFoundError
    b = np.fromfile(fp.as_posix(), dtype=np.uint8)
    return cv2.imdecode(b, cv2.IMREAD_COLOR)


def convert_to_rgb(image: np.ndarray, swap_channel: bool = False) -> np.ndarray:
    if len(image.shape) == 2:
        image_dst = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
    elif image.shape[2] == 4:
        image_dst = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
    else:
        image_dst = image

    if swap_channel:
        return cv2.cvtColor(image_dst, cv2.COLOR_BGR2RGB)
    return image_dst


class BaseConverter(ABC):

    @abstractmethod
    def length(self) -> int:
        pass

    @abstractmethod
    def iter_image(self) -> Generator[np.ndarray, None, None]:
        pass


class PPTConverter(BaseConverter):

    def __init__(self, fp: Path) -> None:
        self.__fp = fp
        self.__len = None
        self.__dir = AppConfig.working_directory.joinpath(".tmp")

    def length(self) -> int | None:
        return self.__len

    def iter_image(self) -> Generator[np.ndarray, None, None]:
        if not self.__fp.exists():
            raise FileNotFoundError(f"{self.__fp} not found.")
        self.__dir.mkdir(parents=True, exist_ok=True)

        pythoncom.CoInitialize()
        powerpoint = client.DispatchEx("Powerpoint.Application")
        presentation = None
        try:
            presentation = powerpoint.Presentations.Open(
                self.__fp.absolute().as_posix(),
                ReadOnly=True,
                Untitled=False,
                WithWindow=False,
            )
            self.__len = len(presentation.Slides)

            for i, slide in enumerate(presentation.Slides, start=1):
                img_fn = Path("ppt_" + str(i).zfill(4)).with_suffix(".png")
                img_fp = self.__dir / img_fn
                slide.Export(img_fp.absolute(), ".PNG")

                img = imread(img_fp.as_posix())
                img = convert_to_rgb(img, swap_channel=True)
                yield img
                img_fp.unlink(missing_ok=True)
        except Exception as e:
            raise e
        finally:
            if presentation is not None:
                presentation.Close()
            pythoncom.CoUninitialize()


class TIFConverter(BaseConverter):

    def __init__(self, fp: Path) -> None:
        self.__fp = fp
        self.__len = None

    def length(self) -> int | None:
        return self.__len

    def iter_image(self) -> Generator[np.ndarray, None, None]:
        if not self.__fp.exists():
            raise FileNotFoundError(f"{self.__fp} not found.")

        try:
            image: Image.Image = Image.open(self.__fp.as_posix())
            self.__len = image.n_frames

            for i in range(self.__len):
                image.seek(i)
                img = np.array(image.copy())
                if img.dtype == np.bool8:
                    img = img.astype(dtype=np.uint8) * 255
                    img = convert_to_rgb(img)
                yield img
        finally:
            image.close()


class PDFConverter(BaseConverter):

    def __init__(self, fp: Path) -> None:
        self.__fp = fp
        self.__len = None

    def length(self) -> int | None:
        return self.__len

    def iter_image(self) -> Generator[np.ndarray, None, None]:
        if not self.__fp.exists():
            raise FileNotFoundError(f"{self.__fp} not found.")
        matrix = pymupdf.Matrix(2.0, 2.0)

        try:
            pdf = pymupdf.open(self.__fp)
            self.__len = len(pdf)

            for i in range(self.length()):
                pixmap = pdf.load_page(i).get_pixmap(matrix=matrix)
                img = np.frombuffer(pixmap.samples, dtype=np.uint8).reshape(
                    pixmap.height,
                    pixmap.width,
                    pixmap.n,
                )
                yield img
        finally:
            pdf.close()


class XDWConverter(BaseConverter):

    def __init__(self, fp: Path) -> None:
        self.__fp = fp
        self.__len = None
        self.__dir = AppConfig.working_directory.joinpath(".tmp")

    def length(self) -> int:
        return self.__len

    def iter_image(self) -> Generator[np.ndarray, None, None]:
        if not self.__fp.exists():
            raise FileNotFoundError(f"{self.__fp} not found.")
        self.__dir.mkdir(parents=True, exist_ok=True)

        try:
            docu: xdwlib.Document | xdwlib.Binder = xdwlib.xdwopen(
                self.__fp.as_posix()
            )
            self.__len = int(docu.pages)
            for i, page in enumerate(docu, start=1):
                page: xdwlib.Page
                img_fn = Path("xdw_" + str(i).zfill(4)).with_suffix(".tiff")
                img_fp = self.__dir / img_fn
                page.export_image(
                    img_fp.absolute().as_posix(),
                    format="TIFF",
                    compress="NOCOMPRESS",
                )

                img = np.array(Image.open(img_fp.as_posix()))
                img = convert_to_rgb(img)
                yield img
                img_fp.unlink(missing_ok=True)
        finally:
            docu.close()


class ConverterFactory:
    __dict: dict[str, Type[BaseConverter]] = {}
    __logger: logging.Logger = logging.getLogger("ConverterFactory")

    @classmethod
    def register(
        cls,
        converter: Type[BaseConverter],
        suffixes: list[str],
    ) -> None:
        for suffix in suffixes:
            cls.__dict[suffix.lower()] = converter
        cls.__logger.debug(f"File types registered: {tuple(suffixes)}")

    @classmethod
    def create(cls, fp: Path) -> BaseConverter | None:
        suffix = fp.suffix.lower()
        if suffix not in cls.__dict.keys():
            return None
        return cls.__dict[suffix](fp)

    @classmethod
    def suffixes(cls) -> list[str]:
        return cls.__dict.keys()


try:
    import pythoncom
    from win32com import client

    ConverterFactory.register(PPTConverter, [".ppt", ".pptx"])
except ImportError:
    pass

try:
    from PIL import Image

    ConverterFactory.register(TIFConverter, [".tif", ".tiff"])
except ImportError:
    pass

try:
    import pymupdf

    ConverterFactory.register(PDFConverter, [".pdf"])
except ImportError:
    pass

if "Image" in dir():
    try:
        import xdwlib

        ConverterFactory.register(XDWConverter, [".xdw", ".xbd"])
    except ImportError:
        pass
    except FileNotFoundError:
        pass
