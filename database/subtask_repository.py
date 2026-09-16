import sqlite3
from datetime import datetime
from database.db import DB_PATH


SUBTASK_STATUSES = ["Не начата", "В процессе", "Выполнена", "Отложена"]


def get_subtasks_by_task_id(task_id: int) -> list[tuple]:
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, title, status
        FROM subtasks
        WHERE task_id = ?
        ORDER BY id ASC
        """,
        (task_id,),
    )

    subtasks = cursor.fetchall()
    connection.close()
    return subtasks


def create_subtask(task_id: int, title: str) -> None:
    now = datetime.now().isoformat(timespec="seconds")

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO subtasks (task_id, title, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (task_id, title, "Не начата", now, now),
    )

    connection.commit()
    connection.close()


def update_subtask_status(subtask_id: int, status: str) -> None:
    now = datetime.now().isoformat(timespec="seconds")

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE subtasks
        SET status = ?, updated_at = ?
        WHERE id = ?
        """,
        (status, now, subtask_id),
    )

    connection.commit()
    connection.close()


def delete_subtask(subtask_id: int) -> None:
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("DELETE FROM subtasks WHERE id = ?", (subtask_id,))

    connection.commit()
    connection.close()


def calculate_task_progress(task_id: int) -> int:
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM subtasks WHERE task_id = ?",
        (task_id,),
    )
    total = cursor.fetchone()[0]

    if total == 0:
        connection.close()
        return 0

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM subtasks
        WHERE task_id = ? AND status = 'Выполнена'
        """,
        (task_id,),
    )
    completed = cursor.fetchone()[0]

    progress = int((completed / total) * 100)
    connection.close()
    return progress


def refresh_task_progress(task_id: int) -> int:
    progress = calculate_task_progress(task_id)

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE tasks
        SET progress = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (progress, task_id),
    )

    connection.commit()
    connection.close()
    return progress