from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QMessageBox,
    QHBoxLayout,
)
from PySide6.QtGui import QColor, QBrush
from PySide6.QtCore import Signal

from database.task_repository import get_archived_tasks, restore_task, clear_archive


class ArchiveView(QWidget):
    task_double_clicked = Signal(int)

    def __init__(self) -> None:
        super().__init__()

        self.layout = QVBoxLayout(self)

        self.title_label = QLabel("Архив задач")
        self.tasks_list = QListWidget()

        self.buttons_layout = QHBoxLayout()
        self.restore_button = QPushButton("Восстановить выбранную задачу")
        self.clear_archive_button = QPushButton("Очистить архив")

        self.buttons_layout.addWidget(self.restore_button)
        self.buttons_layout.addWidget(self.clear_archive_button)

        self.layout.addWidget(self.title_label)
        self.layout.addWidget(self.tasks_list)
        self.layout.addLayout(self.buttons_layout)

        self.tasks_list.itemDoubleClicked.connect(self.handle_item_double_click)
        self.restore_button.clicked.connect(self.restore_selected_task)
        self.clear_archive_button.clicked.connect(self.clear_all_archive)

        self.refresh()

    def get_task_color(self, current_priority: str, status: str) -> QColor:
        if status == "Выполнена":
            return QColor(200, 255, 200)
        if status == "Отложена":
            return QColor(220, 220, 235)
        if status == "Заброшена":
            return QColor(190, 190, 190)

        if current_priority == "Критический":
            return QColor(255, 170, 170)
        if current_priority == "Срочный":
            return QColor(255, 210, 150)
        if current_priority == "Высокий":
            return QColor(255, 245, 170)
        if current_priority == "Средний":
            return QColor(200, 235, 255)
        if current_priority == "Низкий":
            return QColor(235, 235, 235)

        return QColor(255, 255, 255)

    def refresh(self) -> None:
        self.tasks_list.clear()

        tasks = get_archived_tasks()

        if not tasks:
            self.tasks_list.addItem("Архив пуст.")
            return

        for task in tasks:
            (
                task_id,
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
                recurring_type,
            ) = task

            deadline_text = deadline if has_deadline else "Без срока"
            category_text = category if category else "Без категории"
            tags_text = tags if tags else "Без меток"
            recurring_text = recurring_type if is_recurring and recurring_type else "Нет"

            item_text = (
                f"{title}\n"
                f"Категория: {category_text}\n"
                f"Метки: {tags_text}\n"
                f"Базовый приоритет: {base_priority} | Текущий: {current_priority}\n"
                f"Статус: {status} | Прогресс: {progress}%\n"
                f"Срок: {deadline_text} | Повторение: {recurring_text}"
            )

            item = QListWidgetItem(item_text)
            item.setData(256, task_id)
            item.setBackground(QBrush(self.get_task_color(current_priority, status)))
            item.setForeground(QBrush(QColor(35, 35, 35)))
            self.tasks_list.addItem(item)

    def restore_selected_task(self) -> None:
        item = self.tasks_list.currentItem()

        if not item:
            QMessageBox.warning(self, "Ошибка", "Сначала выбери задачу.")
            return

        task_id = item.data(256)

        if task_id is None:
            return

        restore_task(task_id)
        QMessageBox.information(self, "Успех", "Задача восстановлена из архива.")
        self.refresh()

    def clear_all_archive(self) -> None:
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Ты точно хочешь полностью очистить архив?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            clear_archive()
            QMessageBox.information(self, "Успех", "Архив очищен.")
            self.refresh()

    def handle_item_double_click(self, item: QListWidgetItem) -> None:
        task_id = item.data(256)

        if task_id is None:
            return

        self.task_double_clicked.emit(task_id)