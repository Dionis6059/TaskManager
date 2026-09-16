from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QCheckBox,
    QPushButton,
    QMessageBox,
    QGroupBox,
)
from PySide6.QtGui import QFont

from database.db import get_database_path
from services.autostart import (
    is_autostart_enabled,
    set_autostart,
)
from version import APP_NAME, APP_VERSION


class SettingsView(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(18)

        # =====================================================
        # ЗАГОЛОВОК
        # =====================================================

        self.title_label = QLabel("Настройки")

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
        # ПРОГРАММА
        # =====================================================

        self.app_group = QGroupBox(
            "О программе"
        )

        app_layout = QVBoxLayout(
            self.app_group
        )

        self.app_name_label = QLabel()

        self.version_label = QLabel()

        app_layout.addWidget(
            self.app_name_label
        )

        app_layout.addWidget(
            self.version_label
        )

        self.layout.addWidget(
            self.app_group
        )

        # =====================================================
        # АВТОЗАПУСК
        # =====================================================

        self.autostart_group = QGroupBox(
            "Запуск программы"
        )

        autostart_layout = QVBoxLayout(
            self.autostart_group
        )

        self.autostart_checkbox = QCheckBox(
            "Запускать Task Manager вместе с Windows"
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

        self.database_group = QGroupBox(
            "Данные"
        )

        database_layout = QVBoxLayout(
            self.database_group
        )

        self.database_title_label = QLabel(
            "Расположение базы данных:"
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
        # СОХРАНИТЬ
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
    # ОБНОВЛЕНИЕ ДАННЫХ
    # =========================================================

    def refresh(self) -> None:
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
    # СОХРАНЕНИЕ
    # =========================================================

    def save_settings(self) -> None:
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
                    f"настройки:\n{error}"
                ),
            )