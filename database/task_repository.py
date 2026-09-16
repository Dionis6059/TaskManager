import sqlite3
from datetime import datetime, date, timedelta
from database.db import DB_PATH


PRIORITY_ORDER = {
    "Низкий": 1,
    "Средний": 2,
    "Высокий": 3,
    "Срочный": 4,
    "Критический": 5,
}

RECURRING_OPTIONS = [
    "Нет",
    "Каждый день",
    "Каждую неделю",
    "Каждый месяц",
]


def get_higher_priority(priority_1: str, priority_2: str) -> str:
    if PRIORITY_ORDER.get(priority_1, 1) >= PRIORITY_ORDER.get(priority_2, 1):
        return priority_1
    return priority_2


def calculate_current_priority(
    base_priority: str,
    deadline: str | None,
    has_deadline: int,
    status: str,
) -> str:
    if status == "Выполнена":
        return base_priority

    if not has_deadline or not deadline:
        return base_priority

    today = date.today()

    try:
        deadline_date = datetime.strptime(deadline, "%Y-%m-%d").date()
    except ValueError:
        return base_priority

    days_left = (deadline_date - today).days

    if days_left < 0:
        return "Критический"
    if days_left <= 1:
        return get_higher_priority(base_priority, "Срочный")
    if days_left <= 3:
        return get_higher_priority(base_priority, "Высокий")
    if days_left <= 7:
        return get_higher_priority(base_priority, "Средний")

    return base_priority


def calculate_next_deadline(deadline: str | None, recurring_type: str) -> str | None:
    base_date = date.today()

    if deadline:
        try:
            base_date = datetime.strptime(deadline, "%Y-%m-%d").date()
        except ValueError:
            base_date = date.today()

    if recurring_type == "Каждый день":
        next_date = base_date + timedelta(days=1)
    elif recurring_type == "Каждую неделю":
        next_date = base_date + timedelta(days=7)
    elif recurring_type == "Каждый месяц":
        next_date = base_date + timedelta(days=30)
    else:
        return None

    return next_date.isoformat()


def refresh_all_current_priorities() -> None:
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, base_priority, deadline, has_deadline, status
        FROM tasks
        """
    )
    tasks = cursor.fetchall()

    for task_id, base_priority, deadline, has_deadline, status in tasks:
        current_priority = calculate_current_priority(
            base_priority=base_priority,
            deadline=deadline,
            has_deadline=has_deadline,
            status=status,
        )

        cursor.execute(
            """
            UPDATE tasks
            SET current_priority = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                current_priority,
                datetime.now().isoformat(timespec="seconds"),
                task_id,
            ),
        )

    connection.commit()
    connection.close()


def create_task(
    title: str,
    description: str,
    category: str,
    tags: str,
    base_priority: str,
    status: str,
    deadline: str | None,
    has_deadline: int,
    is_recurring: int,
    recurring_type: str | None,
) -> None:
    now = datetime.now().isoformat(timespec="seconds")
    current_priority = calculate_current_priority(
        base_priority=base_priority,
        deadline=deadline,
        has_deadline=has_deadline,
        status=status,
    )

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO tasks (
            title,
            description,
            category,
            tags,
            base_priority,
            current_priority,
            status,
            deadline,
            has_deadline,
            progress,
            is_recurring,
            recurring_type,
            archived,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            title,
            description,
            category,
            tags,
            base_priority,
            current_priority,
            status,
            deadline,
            has_deadline,
            0,
            is_recurring,
            recurring_type,
            0,
            now,
            now,
        ),
    )

    connection.commit()
    connection.close()


def create_next_recurring_task_from_existing(task_id: int) -> None:
    task = get_task_by_id(task_id)

    if not task:
        return

    (
        _task_id,
        title,
        description,
        category,
        tags,
        base_priority,
        current_priority,
        status,
        deadline,
        has_deadline,
        progress,
        is_recurring,
        recurring_type,
        archived,
        created_at,
        updated_at,
    ) = task

    if not is_recurring or not recurring_type or recurring_type == "Нет":
        return

    next_deadline = calculate_next_deadline(deadline, recurring_type)
    next_has_deadline = 1 if next_deadline else 0

    create_task(
        title=title,
        description=description,
        category=category,
        tags=tags,
        base_priority=base_priority,
        status="Не начата",
        deadline=next_deadline,
        has_deadline=next_has_deadline,
        is_recurring=1,
        recurring_type=recurring_type,
    )


def _base_tasks_query(where_clause: str, params: tuple) -> list[tuple]:
    refresh_all_current_priorities()

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    query = f"""
        SELECT
            id,
            title,
            category,
            tags,
            base_priority,
            current_priority,
            status,
            deadline,
            has_deadline,
            progress,
            is_recurring,
            recurring_type
        FROM tasks
        {where_clause}
        ORDER BY
            CASE current_priority
                WHEN 'Критический' THEN 5
                WHEN 'Срочный' THEN 4
                WHEN 'Высокий' THEN 3
                WHEN 'Средний' THEN 2
                WHEN 'Низкий' THEN 1
                ELSE 0
            END DESC,
            id DESC
    """

    cursor.execute(query, params)
    tasks = cursor.fetchall()
    connection.close()
    return tasks


def get_all_tasks() -> list[tuple]:
    return _base_tasks_query("WHERE archived = 0", ())


def get_filtered_tasks(
    search_text: str = "",
    category: str = "Все",
    status: str = "Все",
    priority: str = "Все",
) -> list[tuple]:
    conditions = ["archived = 0"]
    params: list[str] = []

    if search_text.strip():
        conditions.append("LOWER(title) LIKE ?")
        params.append(f"%{search_text.strip().lower()}%")

    if category != "Все":
        if category == "Без категории":
            conditions.append("(category IS NULL OR category = '')")
        else:
            conditions.append("category = ?")
            params.append(category)

    if status != "Все":
        conditions.append("status = ?")
        params.append(status)

    if priority != "Все":
        conditions.append("current_priority = ?")
        params.append(priority)

    where_clause = "WHERE " + " AND ".join(conditions)
    return _base_tasks_query(where_clause, tuple(params))


def get_distinct_categories() -> list[str]:
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT DISTINCT category
        FROM tasks
        WHERE archived = 0
        ORDER BY category COLLATE NOCASE
        """
    )

    rows = cursor.fetchall()
    connection.close()

    categories = []
    has_empty = False

    for row in rows:
        value = row[0]
        if value is None or value == "":
            has_empty = True
        else:
            categories.append(value)

    result = ["Все"]
    result.extend(categories)

    if has_empty:
        result.append("Без категории")

    return result


def get_archived_tasks() -> list[tuple]:
    refresh_all_current_priorities()

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            title,
            category,
            tags,
            base_priority,
            current_priority,
            status,
            deadline,
            has_deadline,
            progress,
            is_recurring,
            recurring_type
        FROM tasks
        WHERE archived = 1
        ORDER BY id DESC
        """
    )

    tasks = cursor.fetchall()
    connection.close()
    return tasks


def get_today_tasks() -> list[tuple]:
    refresh_all_current_priorities()
    today = date.today().isoformat()

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            title,
            category,
            tags,
            base_priority,
            current_priority,
            status,
            deadline,
            has_deadline,
            progress,
            is_recurring,
            recurring_type
        FROM tasks
        WHERE archived = 0
          AND (
                (has_deadline = 1 AND deadline = ?)
                OR
                (has_deadline = 1 AND deadline < ? AND status != 'Выполнена')
                OR
                (has_deadline = 0 AND status = 'В процессе')
              )
        ORDER BY
            CASE current_priority
                WHEN 'Критический' THEN 5
                WHEN 'Срочный' THEN 4
                WHEN 'Высокий' THEN 3
                WHEN 'Средний' THEN 2
                WHEN 'Низкий' THEN 1
                ELSE 0
            END DESC,
            id DESC
        """,
        (today, today),
    )

    tasks = cursor.fetchall()
    connection.close()
    return tasks


def get_tasks_by_date(selected_date: str) -> list[tuple]:
    refresh_all_current_priorities()

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            title,
            category,
            tags,
            base_priority,
            current_priority,
            status,
            deadline,
            has_deadline,
            progress,
            is_recurring,
            recurring_type
        FROM tasks
        WHERE archived = 0
          AND has_deadline = 1
          AND deadline = ?
        ORDER BY
            CASE current_priority
                WHEN 'Критический' THEN 5
                WHEN 'Срочный' THEN 4
                WHEN 'Высокий' THEN 3
                WHEN 'Средний' THEN 2
                WHEN 'Низкий' THEN 1
                ELSE 0
            END DESC,
            id DESC
        """,
        (selected_date,),
    )

    tasks = cursor.fetchall()
    connection.close()
    return tasks


def get_reminder_tasks() -> list[tuple]:
    refresh_all_current_priorities()

    today = date.today()
    tomorrow = today + timedelta(days=1)

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            title,
            status,
            deadline,
            has_deadline,
            current_priority
        FROM tasks
        WHERE archived = 0
          AND has_deadline = 1
          AND status != 'Выполнена'
          AND status != 'Заброшена'
          AND (
                deadline < ?
                OR deadline = ?
                OR deadline = ?
              )
        ORDER BY
            CASE current_priority
                WHEN 'Критический' THEN 5
                WHEN 'Срочный' THEN 4
                WHEN 'Высокий' THEN 3
                WHEN 'Средний' THEN 2
                WHEN 'Низкий' THEN 1
                ELSE 0
            END DESC,
            CASE
                WHEN deadline < ? THEN 0
                WHEN deadline = ? THEN 1
                ELSE 2
            END,
            deadline ASC,
            id DESC
        """,
        (
            today.isoformat(),
            today.isoformat(),
            tomorrow.isoformat(),
            today.isoformat(),
            today.isoformat(),
        ),
    )

    reminders = cursor.fetchall()
    connection.close()
    return reminders


def get_statistics() -> dict[str, int | float]:
    refresh_all_current_priorities()
    today = date.today().isoformat()

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            COUNT(*),
            SUM(CASE WHEN status = 'Выполнена' THEN 1 ELSE 0 END),
            SUM(CASE WHEN status = 'Отложена' THEN 1 ELSE 0 END),
            SUM(CASE WHEN status = 'Заброшена' THEN 1 ELSE 0 END),
            SUM(CASE WHEN is_recurring = 1 THEN 1 ELSE 0 END),
            SUM(CASE WHEN has_deadline = 1 AND deadline < ? AND status != 'Выполнена' THEN 1 ELSE 0 END),
            AVG(progress)
        FROM tasks
        WHERE archived = 0
        """,
        (today,),
    )

    row = cursor.fetchone()
    connection.close()

    total_tasks = row[0] or 0
    completed_tasks = row[1] or 0
    postponed_tasks = row[2] or 0
    abandoned_tasks = row[3] or 0
    recurring_tasks = row[4] or 0
    overdue_tasks = row[5] or 0
    average_progress = round(row[6] or 0, 1)

    active_tasks = total_tasks - completed_tasks - abandoned_tasks

    return {
        "total_tasks": total_tasks,
        "active_tasks": active_tasks,
        "completed_tasks": completed_tasks,
        "postponed_tasks": postponed_tasks,
        "abandoned_tasks": abandoned_tasks,
        "recurring_tasks": recurring_tasks,
        "overdue_tasks": overdue_tasks,
        "average_progress": average_progress,
    }


def get_task_by_id(task_id: int) -> tuple | None:
    refresh_all_current_priorities()

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            title,
            description,
            category,
            tags,
            base_priority,
            current_priority,
            status,
            deadline,
            has_deadline,
            progress,
            is_recurring,
            recurring_type,
            archived,
            created_at,
            updated_at
        FROM tasks
        WHERE id = ?
        """,
        (task_id,),
    )

    task = cursor.fetchone()
    connection.close()
    return task


def update_task(
    task_id: int,
    title: str,
    description: str,
    category: str,
    tags: str,
    base_priority: str,
    status: str,
    deadline: str | None,
    has_deadline: int,
    is_recurring: int,
    recurring_type: str | None,
) -> None:
    old_task = get_task_by_id(task_id)
    old_status = old_task[7] if old_task else None

    now = datetime.now().isoformat(timespec="seconds")
    current_priority = calculate_current_priority(
        base_priority=base_priority,
        deadline=deadline,
        has_deadline=has_deadline,
        status=status,
    )

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE tasks
        SET
            title = ?,
            description = ?,
            category = ?,
            tags = ?,
            base_priority = ?,
            current_priority = ?,
            status = ?,
            deadline = ?,
            has_deadline = ?,
            is_recurring = ?,
            recurring_type = ?,
            updated_at = ?
        WHERE id = ?
        """,
        (
            title,
            description,
            category,
            tags,
            base_priority,
            current_priority,
            status,
            deadline,
            has_deadline,
            is_recurring,
            recurring_type,
            now,
            task_id,
        ),
    )

    connection.commit()
    connection.close()

    if old_status != "Выполнена" and status == "Выполнена":
        if is_recurring == 1:
            create_next_recurring_task_from_existing(task_id)
        archive_task(task_id)


def archive_task(task_id: int) -> None:
    task = get_task_by_id(task_id)
    if not task:
        return

    status = task[7]
    if status == "Заброшена":
        return

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE tasks
        SET archived = 1, updated_at = ?
        WHERE id = ?
        """,
        (datetime.now().isoformat(timespec="seconds"), task_id),
    )

    connection.commit()
    connection.close()


def restore_task(task_id: int) -> None:
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE tasks
        SET archived = 0, updated_at = ?
        WHERE id = ?
        """,
        (datetime.now().isoformat(timespec="seconds"), task_id),
    )

    connection.commit()
    connection.close()


def clear_archive() -> None:
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM subtasks
        WHERE task_id IN (SELECT id FROM tasks WHERE archived = 1)
        """
    )
    cursor.execute("DELETE FROM tasks WHERE archived = 1")

    connection.commit()
    connection.close()


def delete_task(task_id: int) -> None:
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("DELETE FROM subtasks WHERE task_id = ?", (task_id,))
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))

    connection.commit()
    connection.close()