import subprocess

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QCheckBox,
    QPushButton,
    QMessageBox,
    QGroupBox,
    QApplication,
)
from PySide6.QtGui import (
    QFont,
    QDesktopServices,
)
from PySide6.QtCore import QUrl

from database.db import (
    get_database_path,
)

from services.autostart import (
    is_autostart_enabled,
    set_autostart,
)

from services.update_checker import (
    check_for_updates,
    download_installer,
)

from version import (
    APP_NAME,
    APP_VERSION,
)


class SettingsView(QWidget):
    def __init__(
        self,
    ) -> None:
        super().__init__()

        self.layout = QVBoxLayout(
            self
        )

        self.layout.setSpacing(
            18
        )

        # =====================================================
        # ЗАГОЛОВОК
        # =====================================================

        self.title_label = QLabel(
            "Настройки"
        )

        self.title_label.setFont(
            QFont(
                "Segoe UI",
                16,
                QFont.Bold,
            )
        )

        self.layout.addWidget(
            self.title_label
        )

        # =====================================================
        # О ПРОГРАММЕ
        # =====================================================

        self.app_group = QGroupBox(
            "О программе"
        )

        app_layout = QVBoxLayout(
            self.app_group
        )

        self.app_name_label = QLabel()

        self.version_label = QLabel()

        self.check_updates_button = (
            QPushButton(
                "Проверить обновления"
            )
        )

        self.check_updates_button.setMinimumHeight(
            36
        )

        self.check_updates_button.clicked.connect(
            self.check_updates
        )

        app_layout.addWidget(
            self.app_name_label
        )

        app_layout.addWidget(
            self.version_label
        )

        app_layout.addWidget(
            self.check_updates_button
        )

        self.layout.addWidget(
            self.app_group
        )

        # =====================================================
        # АВТОЗАПУСК
        # =====================================================

        self.autostart_group = (
            QGroupBox(
                "Запуск программы"
            )
        )

        autostart_layout = (
            QVBoxLayout(
                self.autostart_group
            )
        )

        self.autostart_checkbox = (
            QCheckBox(
                "Запускать Task Manager "
                "вместе с Windows"
            )
        )

        autostart_layout.addWidget(
            self.autostart_checkbox
        )

        self.layout.addWidget(
            self.autostart_group
        )

        # =====================================================
        # БАЗА ДАННЫХ
        # =====================================================

        self.database_group = (
            QGroupBox(
                "Данные"
            )
        )

        database_layout = (
            QVBoxLayout(
                self.database_group
            )
        )

        self.database_title_label = (
            QLabel(
                "Расположение базы "
                "данных:"
            )
        )

        self.database_label = QLabel()

        self.database_label.setWordWrap(
            True
        )

        database_layout.addWidget(
            self.database_title_label
        )

        database_layout.addWidget(
            self.database_label
        )

        self.layout.addWidget(
            self.database_group
        )

        # =====================================================
        # СОХРАНЕНИЕ
        # =====================================================

        self.save_button = QPushButton(
            "Сохранить настройки"
        )

        self.save_button.setMinimumHeight(
            36
        )

        self.save_button.clicked.connect(
            self.save_settings
        )

        self.layout.addWidget(
            self.save_button
        )

        self.layout.addStretch()

        self.refresh()

    # =========================================================
    # REFRESH
    # =========================================================

    def refresh(
        self,
    ) -> None:
        self.app_name_label.setText(
            f"Приложение: {APP_NAME}"
        )

        self.version_label.setText(
            f"Версия: {APP_VERSION}"
        )

        self.autostart_checkbox.setChecked(
            is_autostart_enabled()
        )

        self.database_label.setText(
            str(
                get_database_path()
            )
        )

    # =========================================================
    # СОХРАНЕНИЕ НАСТРОЕК
    # =========================================================

    def save_settings(
        self,
    ) -> None:
        try:
            set_autostart(
                self.autostart_checkbox.isChecked()
            )

            QMessageBox.information(
                self,
                "Настройки",
                "Настройки сохранены.",
            )

            self.refresh()

        except Exception as error:
            QMessageBox.critical(
                self,
                "Ошибка",
                (
                    "Не удалось сохранить "
                    "настройки:\n"
                    f"{error}"
                ),
            )

    # =========================================================
    # ПРОВЕРКА ОБНОВЛЕНИЙ
    # =========================================================

    def check_updates(
        self,
    ) -> None:
        self.check_updates_button.setEnabled(
            False
        )

        self.check_updates_button.setText(
            "Проверка..."
        )

        try:
            result = (
                check_for_updates(
                    APP_VERSION
                )
            )

            if not result[
                "update_available"
            ]:
                QMessageBox.information(
                    self,
                    "Обновления",
                    (
                        "У вас установлена "
                        "актуальная версия.\n\n"
                        f"Версия: "
                        f"{APP_VERSION}"
                    ),
                )

                return

            latest_version = (
                result[
                    "latest_version"
                ]
            )

            installer_url = (
                result[
                    "installer_url"
                ]
            )

            if not installer_url:
                self.show_manual_update_dialog(
                    result
                )

                return

            message = (
                "Доступна новая версия "
                "Task Manager.\n\n"
                f"Установлена: "
                f"{APP_VERSION}\n"
                f"Новая: "
                f"{latest_version}\n\n"
                "Скачать и запустить "
                "обновление?"
            )

            answer = QMessageBox.question(
                self,
                "Доступно обновление",
                message,
                QMessageBox.Yes
                | QMessageBox.No,
                QMessageBox.Yes,
            )

            if answer != QMessageBox.Yes:
                return

            self.download_and_install_update(
                result
            )

        except Exception as error:
            QMessageBox.warning(
                self,
                "Не удалось проверить "
                "обновления",
                str(error),
            )

        finally:
            self.check_updates_button.setEnabled(
                True
            )

            self.check_updates_button.setText(
                "Проверить обновления"
            )

    # =========================================================
    # СКАЧИВАНИЕ
    # =========================================================

    def download_and_install_update(
        self,
        result: dict,
    ) -> None:
        self.check_updates_button.setText(
            "Скачивание..."
        )

        QApplication.processEvents()

        try:
            installer_path = (
                download_installer(
                    installer_url=result[
                        "installer_url"
                    ],
                    installer_name=result[
                        "installer_name"
                    ],
                    expected_digest=result[
                        "installer_digest"
                    ],
                )
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Ошибка обновления",
                (
                    "Не удалось скачать "
                    "обновление.\n\n"
                    f"{error}"
                ),
            )

            return

        answer = QMessageBox.question(
            self,
            "Обновление скачано",
            (
                "Обновление успешно "
                "скачано.\n\n"
                "Сейчас будет запущен "
                "установщик, а Task Manager "
                "закроется.\n\n"
                "Продолжить?"
            ),
            QMessageBox.Yes
            | QMessageBox.No,
            QMessageBox.Yes,
        )

        if answer != QMessageBox.Yes:
            return

        try:
            subprocess.Popen(
                [
                    str(
                        installer_path
                    )
                ]
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Ошибка",
                (
                    "Не удалось запустить "
                    "установщик.\n\n"
                    f"{error}"
                ),
            )

            return

        QApplication.quit()

    # =========================================================
    # РУЧНОЕ ОБНОВЛЕНИЕ
    # =========================================================

    def show_manual_update_dialog(
        self,
        result: dict,
    ) -> None:
        answer = QMessageBox.question(
            self,
            "Доступно обновление",
            (
                "Новая версия найдена, "
                "но автоматический "
                "установщик в релизе "
                "не найден.\n\n"
                "Открыть страницу "
                "релиза?"
            ),
            QMessageBox.Yes
            | QMessageBox.No,
            QMessageBox.Yes,
        )

        if answer == QMessageBox.Yes:
            release_url = (
                result[
                    "release_url"
                ]
            )

            if release_url:
                QDesktopServices.openUrl(
                    QUrl(
                        release_url
                    )
                )