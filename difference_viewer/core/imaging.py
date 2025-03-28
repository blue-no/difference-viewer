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

from collections import namedtuple
from typing import Sequence

import cv2
import numpy as np

Rect = namedtuple("Rect", ["x", "y", "w", "h"])


def rgb_to_hex(rgb: tuple) -> str:
    return "#{:02x}{:02x}{:02x}".format(*rgb).upper()


def hex_to_rgb(hex_color: str) -> tuple:
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


class DifferenceDetector:

    def __init__(self) -> None:
        self._bg_rgb = [255, 255, 255]

    def get_bboxes(
        self,
        img1: np.ndarray,
        img2: np.ndarray,
        n_merge: int = 0,
    ) -> list[list[Rect]]:
        diff_mask = create_diff_binary_mask(img1, img2)
        diff_cnts = extract_contours(diff_mask)
        h, w = img1.shape[:2]
        diff_rects = create_contour_bounding_rects(diff_cnts)
        filt_rects = filter_rects(diff_rects, min_width=2)

        ret = []
        for img in (img1, img2):

            rects = []
            bg_judge_rects = add_rect_padding(filt_rects, pad_x=-15, pad_y=-15)
            for fr, br in zip(filt_rects, bg_judge_rects):
                if np.all(clip_image_rect(img, br) == self._bg_rgb):
                    continue
                rects.append(fr)

            for _ in range(n_merge):
                enlarged_rects = add_rect_padding(rects, pad_x=10, pad_y=10)
                merged_mask = create_merged_rects_binary_mask(
                    enlarged_rects,
                    img_size=(h, w),
                )
                merged_cnts = extract_contours(merged_mask)
                merged_rects = create_contour_bounding_rects(merged_cnts)
                rects = add_rect_padding(merged_rects, pad_x=-10, pad_y=-10)

            ret.append(rects)

        return ret


def draw_contours(
    img: np.ndarray,
    cnts: list[np.ndarray],
    color: tuple[int, int, int],
    width: int,
) -> np.ndarray:
    dst = img.copy()
    cv2.drawContours(
        dst,
        cnts,
        contourIdx=-1,
        color=color,
        thickness=width,
    )
    return dst


def draw_rect_contours(
    img: np.ndarray,
    rects: Sequence[Rect],
    color: tuple[int, int, int] = (0, 0, 0),
    width: int = 1,
) -> np.ndarray:
    dst = img.copy()
    for rect in rects:
        cv2.rectangle(
            dst,
            (rect.x, rect.y),
            (rect.x + rect.w, rect.y + rect.h),
            color,
            thickness=width,
            lineType=cv2.LINE_AA,
        )
    return dst


def extract_contours(bin_mask: np.ndarray) -> list[np.ndarray]:
    cnts, _ = cv2.findContours(
        bin_mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_NONE,
    )
    return cnts


def filter_rects(
    rects: list[Rect],
    min_area: int = 0,
    min_width: int = 0,
) -> list[Rect]:
    rects = list(filter(lambda rect: rect.w * rect.h >= min_area, rects))
    rects = list(filter(lambda rect: rect.w >= min_width, rects))
    rects = list(filter(lambda rect: rect.h >= min_width, rects))
    return rects


def create_diff_binary_mask(
    img1: np.ndarray,
    img2: np.ndarray,
) -> np.ndarray:
    if img1.shape != img2.shape:
        raise ValueError("Images must have same size")
    if img1.ndim == 3:
        img1 = cv2.cvtColor(img1, cv2.COLOR_RGB2GRAY)
    if img2.ndim == 3:
        img2 = cv2.cvtColor(img2, cv2.COLOR_RGB2GRAY)

    diff = np.abs(img1.astype(np.int64) - img2.astype(np.int64))
    diff = diff.astype(np.uint8)
    _, bin_ = cv2.threshold(diff, 0, 255, cv2.THRESH_BINARY)
    return bin_


def create_merged_rects_binary_mask(
    rects: Sequence[Rect],
    img_size: tuple[int, int],
) -> np.ndarray:
    mask = np.zeros(img_size, dtype=np.uint8)
    for rect in rects:
        cv2.rectangle(
            mask,
            (rect.x, rect.y),
            (rect.x + rect.w, rect.y + rect.h),
            255,
            thickness=cv2.FILLED,
        )
    return mask


def create_contour_bounding_rects(cnts: list[np.ndarray]) -> list[Rect]:
    rects = list(Rect(*cv2.boundingRect(cnt)) for cnt in cnts)
    return rects


def add_rect_padding(
    rects: list[Rect],
    pad_x: int,
    pad_y: int,
    max_x: int = 1e6,
    max_y: int = 1e6,
) -> Rect:
    ret = []
    for rec in rects:
        x1, x2 = max(0, rec.x - pad_x), min(max_x, rec.x + rec.w + pad_x)
        y1, y2 = max(0, rec.y - pad_y), min(max_y, rec.y + rec.h + pad_y)
        if x1 > x2:
            x1 = int((x1 + x2) * 0.5)
            x2 = x1 + 1
        if y1 > y2:
            y1 = int((y1 + y2) * 0.5)
            y2 = y1 + 1
        ret.append(Rect(x1, y1, x2 - x1, y2 - y1))
    return ret


def clip_image_rect(img: np.ndarray, rect: Rect) -> np.ndarray:
    return img[rect.y : rect.y + rect.h, rect.x : rect.x + rect.w]
