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
import sys

from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QSplashScreen

from difference_viewer.app.config import AppConfig


def main() -> None:
    logger = logging.getLogger(__name__)

    # initialize qapplication
    logger.info("Starting application")

    app = QApplication(sys.argv)

    def on_app_exit() -> None:
        exit_code = app.quit()
        if exit_code == 0 or exit_code is None:
            logger.info("Exiting application successfully")
        else:
            logger.error(
                f"Exiting application with error: Status code {exit_code}"
            )

    app.aboutToQuit.connect(on_app_exit)

    # show splash screen
    try:
        splash_fp = (
            AppConfig.resource_directory / "images" / "splash_screen.ico"
        )
        if not splash_fp.is_file():
            raise FileNotFoundError(filename=splash_fp)
        pixmap = QPixmap(splash_fp.as_posix())
        splash = QSplashScreen(pixmap)
        splash.show()
    except Exception as e:
        splash = None
        logger.warning(f'Failed to load splash screen: "{e}"')

    # additional imports
    from PyQt5.QtGui import QIcon

    from difference_viewer.app.app import AppController
    from difference_viewer.app.config import (
        Theme,
        UserConfig,
        apply_theme,
        get_system_theme,
    )

    # initialize user config
    AppConfig.working_directory.mkdir(parents=True, exist_ok=True)
    logger.info("Loading user config")
    config = UserConfig.load(AppConfig.user_config_file_path())

    # setup appearance
    theme = Theme(config.theme)
    if theme == Theme.SYSTEM:
        theme = get_system_theme()

    try:
        apply_theme(theme)
    except Exception as e:
        logger.warning(f'Failed to load and apply style sheet: "{e}"')

    try:
        icon_fp = AppConfig.resource_directory / "images" / "favicon.ico"
        app.setWindowIcon(QIcon(icon_fp.as_posix()))
    except Exception as e:
        logger.warning(f'Failed to set icon: "{e}"')

    # run applicaton
    app_controller = AppController(config)
    app_controller.run()

    if splash is not None:
        splash.close()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
