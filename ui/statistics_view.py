from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

from database.task_repository import get_statistics


class StatisticsView(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.layout = QVBoxLayout(self)

        self.title_label = QLabel("Статистика задач")
        self.total_label = QLabel()
        self.active_label = QLabel()
        self.completed_label = QLabel()
        self.overdue_label = QLabel()
        self.postponed_label = QLabel()
        self.abandoned_label = QLabel()
        self.recurring_label = QLabel()
        self.average_progress_label = QLabel()

        self.layout.addWidget(self.title_label)
        self.layout.addWidget(self.total_label)
        self.layout.addWidget(self.active_label)
        self.layout.addWidget(self.completed_label)
        self.layout.addWidget(self.overdue_label)
        self.layout.addWidget(self.postponed_label)
        self.layout.addWidget(self.abandoned_label)
        self.layout.addWidget(self.recurring_label)
        self.layout.addWidget(self.average_progress_label)
        self.layout.addStretch()

        self.refresh()

    def refresh(self) -> None:
        stats = get_statistics()

        self.total_label.setText(f"Всего задач: {stats['total_tasks']}")
        self.active_label.setText(f"Активных задач: {stats['active_tasks']}")
        self.completed_label.setText(f"Выполненных задач: {stats['completed_tasks']}")
        self.overdue_label.setText(f"Просроченных задач: {stats['overdue_tasks']}")
        self.postponed_label.setText(f"Отложенных задач: {stats['postponed_tasks']}")
        self.abandoned_label.setText(f"Заброшенных задач: {stats['abandoned_tasks']}")
        self.recurring_label.setText(f"Повторяющихся задач: {stats['recurring_tasks']}")
        self.average_progress_label.setText(
            f"Средний прогресс по задачам: {stats['average_progress']}%"
        )