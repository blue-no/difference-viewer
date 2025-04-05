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

from difference_viewer.app.config import Theme, UserConfig, apply_theme
from difference_viewer.components.display.display_model import DisplayModel
from difference_viewer.components.display.display_view import DisplayView
from difference_viewer.components.display.display_vm import DisplayViewModel
from difference_viewer.components.main_window.main_view import MainWindow
from difference_viewer.components.main_window.main_vm import MainWindowViewModel
from difference_viewer.components.page.page_model import PageModel
from difference_viewer.components.page.page_view import PageView
from difference_viewer.components.page.page_vm import PageViewModel
from difference_viewer.components.prefs_window.prefs_view import PrefsWindow
from difference_viewer.components.prefs_window.prefs_vm import PrefsViewModel
from difference_viewer.core.imaging import (
    DifferenceDetector,
    add_rect_padding,
    draw_rect_contours,
    hex_to_rgb,
)
from difference_viewer.core.shared_model import ndarray_to_pixmap


class AppController:

    def __init__(self, user_config: UserConfig) -> None:
        self.__logger = logging.getLogger(self.__class__.__name__)

        self._user_config = user_config
        self._drawer = DifferenceDetector()

        self.__logger.debug("Initializing UI components")

        # initialize display component
        self.display_model = DisplayModel()

        self.display_vm1 = DisplayViewModel(self.display_model, user_config)
        self.display_vm2 = DisplayViewModel(self.display_model, user_config)

        self.display_view1 = DisplayView(self.display_vm1)
        self.display_view2 = DisplayView(self.display_vm2)

        # initialize page component
        self.page_model1 = PageModel()
        self.page_model2 = PageModel()

        self.page_vm1 = PageViewModel(self.page_model1, user_config)
        self.page_vm2 = PageViewModel(self.page_model2, user_config)

        self.page_view1 = PageView(self.page_vm1)
        self.page_view2 = PageView(self.page_vm2)

        # initialize main window
        self.main_vm = MainWindowViewModel()
        self.main_window = MainWindow(self.main_vm)

        # initialize preferences window
        self.prefs_vm = PrefsViewModel(user_config)
        self.prefs_window = PrefsWindow(self.prefs_vm)

        # setup signals for file loading
        self.display_vm1.file_accepted.connect(self.page_vm1.load_file)
        self.display_vm2.file_accepted.connect(self.page_vm2.load_file)

        self.page_vm1.loading_started.connect(
            lambda: self.main_vm.switch_window_state(False)
        )
        self.page_vm2.loading_started.connect(
            lambda: self.main_vm.switch_window_state(False)
        )
        self.page_vm1.loading_finished.connect(
            lambda: self.main_vm.switch_window_state(True)
        )
        self.page_vm2.loading_finished.connect(
            lambda: self.main_vm.switch_window_state(True)
        )
        self.page_vm1.loading_canceled.connect(
            lambda: self.main_vm.switch_window_state(True)
        )
        self.page_vm2.loading_canceled.connect(
            lambda: self.main_vm.switch_window_state(True)
        )
        self.page_vm1.loading_finished.connect(self._update_widgets_state)
        self.page_vm2.loading_finished.connect(self._update_widgets_state)

        # setup signals for sync page turning
        self.main_vm.turn_first_requested.connect(self.page_vm1.turn_first)
        self.main_vm.turn_first_requested.connect(self.page_vm2.turn_first)
        self.main_vm.turn_prev_requested.connect(self.page_vm1.turn_prev)
        self.main_vm.turn_prev_requested.connect(self.page_vm2.turn_prev)
        self.main_vm.turn_next_requested.connect(self.page_vm1.turn_next)
        self.main_vm.turn_next_requested.connect(self.page_vm2.turn_next)
        self.main_vm.turn_last_requested.connect(self.page_vm1.turn_last)
        self.main_vm.turn_last_requested.connect(self.page_vm2.turn_last)
        self.main_vm.reset_view_requested.connect(self.display_vm1.reset_view)
        self.main_vm.reset_view_requested.connect(self.display_vm2.reset_view)

        # setup signals for difference display
        self.page_vm1.image_updated.connect(self._update_display)
        self.page_vm2.image_updated.connect(self._update_display)
        self.prefs_vm.bbox_style_changed.connect(self._update_display)

        # setup signals for windows
        self.main_vm.open_prefs_requested.connect(self.prefs_window.show)
        self.prefs_vm.window_style_changed.connect(self._update_theme)

        # initialize UI state
        self.page_view1.put_widget(self.display_view1)
        self.page_view2.put_widget(self.display_view2)

        self.main_window.put_widget(self.page_view1, loc="L")
        self.main_window.put_widget(self.page_view2, loc="R")

        self.main_vm.switch_button_state("fit", False)
        self.main_vm.switch_button_state("turn", False)
        self.main_vm.switch_warning_visibility("size", False)
        self.main_vm.switch_warning_visibility("type", False)

        self._update_theme()

        self.__logger.debug("UI components initialized")

    def run(self) -> None:
        self.main_window.show()
        self.__logger.debug("Main window opened")

    def _update_display(self) -> None:
        has_img_l = self.page_vm1.has_image()
        has_img_r = self.page_vm2.has_image()

        if has_img_l:
            img_l = self.page_vm1.image
        if has_img_r:
            img_r = self.page_vm2.image

        if has_img_l and has_img_r:
            if img_l.shape != img_r.shape:
                self.main_vm.switch_warning_visibility("size", True)
                self.display_vm1.update_pixmap(ndarray_to_pixmap(img_l.data))
                self.display_vm2.update_pixmap(ndarray_to_pixmap(img_r.data))
                return
            else:
                self.main_vm.switch_warning_visibility("size", False)

            rects_l, rects_r = self._drawer.get_bboxes(
                img1=img_l.data,
                img2=img_r.data,
                n_merge=self._user_config.bbox_merge_level,
            )
            diff_l = draw_rect_contours(
                img=img_l.data,
                rects=add_rect_padding(
                    rects_l,
                    pad_x=self._user_config.bbox_padding,
                    pad_y=self._user_config.bbox_padding,
                ),
                color=hex_to_rgb(self._user_config.line_color),
                width=self._user_config.line_width,
            )
            diff_r = draw_rect_contours(
                img=img_r.data,
                rects=add_rect_padding(
                    rects_r,
                    pad_x=self._user_config.bbox_padding,
                    pad_y=self._user_config.bbox_padding,
                ),
                color=hex_to_rgb(self._user_config.line_color),
                width=self._user_config.line_width,
            )
            self.display_vm1.update_pixmap(ndarray_to_pixmap(diff_l))
            self.display_vm2.update_pixmap(ndarray_to_pixmap(diff_r))
            return

        if has_img_l:
            self.display_vm1.update_pixmap(ndarray_to_pixmap(img_l.data))
        if has_img_r:
            self.display_vm2.update_pixmap(ndarray_to_pixmap(img_r.data))

    def _update_widgets_state(self) -> None:
        has_img_l = self.page_vm1.has_image()
        has_img_r = self.page_vm2.has_image()

        if not has_img_l or not has_img_r:
            self.main_vm.switch_button_state("fit", True)
            return

        self.main_vm.switch_button_state("turn", True)
        suffix_l = self.page_vm1.file_suffix
        suffix_r = self.page_vm2.file_suffix
        if suffix_l != suffix_r:
            self.main_vm.switch_warning_visibility("type", True)
        else:
            self.main_vm.switch_warning_visibility("type", False)

    def _update_theme(self) -> None:
        theme_str = Theme(self._user_config.theme).resolved_str()
        apply_theme(theme_str)
        self.page_view1.apply_icon_style(theme_str)
        self.page_view2.apply_icon_style(theme_str)
        self.main_window.apply_icon_style(theme_str)
