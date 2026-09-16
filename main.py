import sys

from PySide6.QtWidgets import QApplication

from database.db import init_db
from ui.main_window import MainWindow


def main() -> None:
    init_db()

    app = QApplication(sys.argv)

    app.setApplicationName("Task Manager")
    app.setOrganizationName("TaskManager")

    # Приложение не завершается,
    # когда главное окно скрыто в трей.
    app.setQuitOnLastWindowClosed(False)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()