import os
import shutil
import sqlite3
import sys
from pathlib import Path


APP_NAME = "TaskManager"


def get_app_data_dir() -> Path:
    """
    Возвращает постоянную папку для пользовательских данных.

    Windows:
    C:\\Users\\Имя\\AppData\\Local\\TaskManager\\

    Если LOCALAPPDATA по какой-то причине недоступен,
    используется домашняя папка пользователя.
    """

    local_app_data = os.getenv("LOCALAPPDATA")

    if local_app_data:
        app_data_dir = Path(local_app_data) / APP_NAME
    else:
        app_data_dir = Path.home() / APP_NAME

    app_data_dir.mkdir(parents=True, exist_ok=True)

    return app_data_dir


APP_DATA_DIR = get_app_data_dir()

DATA_DIR = APP_DATA_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "tasks.db"


def get_project_root() -> Path:
    """
    Определяет папку проекта при запуске через Python.

    При запуске из исходников:
    database/db.py -> database -> корень проекта
    """
    return Path(__file__).resolve().parent.parent


def get_legacy_database_candidates() -> list[Path]:
    """
    Список мест, где могла находиться старая база
    до перехода на AppData.
    """

    candidates = []

    # Старая база проекта:
    # ежедневник/data/tasks.db
    project_root = get_project_root()
    candidates.append(project_root / "data" / "tasks.db")

    # На случай запуска из другой рабочей директории.
    candidates.append(Path.cwd() / "data" / "tasks.db")

    # На случай старой сборки рядом с exe.
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        candidates.append(exe_dir / "data" / "tasks.db")

    # Убираем дубликаты.
    unique_candidates = []

    for candidate in candidates:
        candidate = candidate.resolve()

        if candidate not in unique_candidates:
            unique_candidates.append(candidate)

    return unique_candidates


def migrate_old_database() -> None:
    """
    Если новой базы в AppData ещё нет,
    пытается автоматически перенести старую базу.

    Существующая новая база никогда не перезаписывается.
    """

    if DB_PATH.exists():
        return

    for old_db_path in get_legacy_database_candidates():

        # Не пытаемся копировать файл сам в себя.
        if old_db_path == DB_PATH.resolve():
            continue

        if old_db_path.exists() and old_db_path.is_file():
            try:
                shutil.copy2(old_db_path, DB_PATH)

                print(
                    f"Старая база перенесена:\n"
                    f"{old_db_path}\n"
                    f"->\n"
                    f"{DB_PATH}"
                )

                return

            except Exception as error:
                print(
                    f"Не удалось перенести базу "
                    f"{old_db_path}: {error}"
                )


def init_db() -> None:
    """
    Подготавливает базу данных.

    1. Переносит старую базу, если она существует.
    2. Создаёт новую базу, если её ещё нет.
    3. Создаёт необходимые таблицы.
    """

    migrate_old_database()

    connection = sqlite3.connect(DB_PATH)

    # Включаем поддержку внешних ключей.
    connection.execute("PRAGMA foreign_keys = ON")

    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            category TEXT,
            tags TEXT,
            base_priority TEXT NOT NULL,
            current_priority TEXT NOT NULL,
            status TEXT NOT NULL,
            deadline TEXT,
            has_deadline INTEGER NOT NULL DEFAULT 0,
            progress INTEGER NOT NULL DEFAULT 0,
            is_recurring INTEGER NOT NULL DEFAULT 0,
            recurring_type TEXT,
            archived INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS subtasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Не начата',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,

            FOREIGN KEY (task_id)
            REFERENCES tasks(id)
            ON DELETE CASCADE
        )
        """
    )

    connection.commit()
    connection.close()


def get_database_path() -> Path:
    """
    Можно использовать позже в настройках программы,
    чтобы показать пользователю расположение базы.
    """
    return DB_PATH