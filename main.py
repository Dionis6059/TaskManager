import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from database.db import init_db
from services.theme_manager import resource_path
from ui.main_window import MainWindow


def main() -> None:
    init_db()

    app = QApplication(sys.argv)

    app.setApplicationName("Task Manager")
    app.setOrganizationName("TaskManager")

    icon_path = resource_path(
        "assets/app_icon.ico"
    )

    if icon_path.exists():
        app.setWindowIcon(
            QIcon(str(icon_path))
        )

    # Приложение не завершается,
    # когда главное окно скрыто в трей.
    app.setQuitOnLastWindowClosed(False)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
