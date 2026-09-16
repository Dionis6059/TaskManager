from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QCalendarWidget,
)
from PySide6.QtGui import QColor, QBrush
from PySide6.QtCore import QDate, Signal

from database.task_repository import get_tasks_by_date


class CalendarView(QWidget):
    task_double_clicked = Signal(int)

    def __init__(self) -> None:
        super().__init__()

        self.layout = QVBoxLayout(self)

        self.title_label = QLabel("Календарь задач")
        self.calendar = QCalendarWidget()
        self.tasks_list = QListWidget()

        self.layout.addWidget(self.title_label)
        self.layout.addWidget(self.calendar)
        self.layout.addWidget(self.tasks_list)

        self.calendar.selectionChanged.connect(self.load_tasks_for_selected_date)
        self.tasks_list.itemDoubleClicked.connect(self.handle_item_double_click)

        self.load_tasks_for_selected_date()

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

    def load_tasks_for_selected_date(self) -> None:
        self.tasks_list.clear()

        selected_date = self.calendar.selectedDate().toString("yyyy-MM-dd")
        self.title_label.setText(f"Календарь задач — {selected_date}")

        tasks = get_tasks_by_date(selected_date)

        if not tasks:
            self.tasks_list.addItem("На выбранную дату задач нет.")
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

            category_text = category if category else "Без категории"
            tags_text = tags if tags else "Без меток"
            recurring_text = recurring_type if is_recurring and recurring_type else "Нет"

            item_text = (
                f"{title}\n"
                f"Категория: {category_text}\n"
                f"Метки: {tags_text}\n"
                f"Базовый: {base_priority} | Текущий: {current_priority}\n"
                f"Статус: {status} | Прогресс: {progress}%\n"
                f"Повторение: {recurring_text}"
            )

            item = QListWidgetItem(item_text)
            item.setData(256, task_id)
            item.setBackground(QBrush(self.get_task_color(current_priority, status)))
            item.setForeground(QBrush(QColor(35, 35, 35)))
            self.tasks_list.addItem(item)

    def handle_item_double_click(self, item: QListWidgetItem) -> None:
        task_id = item.data(256)

        if task_id is None:
            return

        self.task_double_clicked.emit(task_id)

    def refresh(self) -> None:
        self.load_tasks_for_selected_date()