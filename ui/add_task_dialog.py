from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QPushButton,
    QComboBox,
    QCheckBox,
    QDateEdit,
    QMessageBox,
)
from PySide6.QtCore import QDate

from database.task_repository import create_task, RECURRING_OPTIONS


class AddTaskDialog(QDialog):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("Добавить задачу")
        self.resize(400, 560)

        layout = QVBoxLayout(self)

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Название задачи")

        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Описание задачи")

        self.category_input = QLineEdit()
        self.category_input.setPlaceholderText("Категория")

        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("Метки через запятую")

        self.priority_input = QComboBox()
        self.priority_input.addItems(["Низкий", "Средний", "Высокий"])

        self.status_input = QComboBox()
        self.status_input.addItems(
            ["Не начата", "В процессе", "Выполнена", "Отложена", "Заброшена"]
        )

        self.deadline_checkbox = QCheckBox("Указать срок")
        self.deadline_checkbox.setChecked(False)

        self.deadline_input = QDateEdit()
        self.deadline_input.setCalendarPopup(True)
        self.deadline_input.setDate(QDate.currentDate())
        self.deadline_input.setEnabled(False)

        self.deadline_checkbox.toggled.connect(self.deadline_input.setEnabled)

        self.recurring_input = QComboBox()
        self.recurring_input.addItems(RECURRING_OPTIONS)

        self.save_button = QPushButton("Сохранить задачу")
        self.save_button.clicked.connect(self.save_task)

        layout.addWidget(QLabel("Название"))
        layout.addWidget(self.title_input)

        layout.addWidget(QLabel("Описание"))
        layout.addWidget(self.description_input)

        layout.addWidget(QLabel("Категория"))
        layout.addWidget(self.category_input)

        layout.addWidget(QLabel("Метки"))
        layout.addWidget(self.tags_input)

        layout.addWidget(QLabel("Приоритет"))
        layout.addWidget(self.priority_input)

        layout.addWidget(QLabel("Статус"))
        layout.addWidget(self.status_input)

        layout.addWidget(self.deadline_checkbox)
        layout.addWidget(self.deadline_input)

        layout.addWidget(QLabel("Повторение"))
        layout.addWidget(self.recurring_input)

        layout.addWidget(self.save_button)

    def save_task(self) -> None:
        title = self.title_input.text().strip()
        description = self.description_input.toPlainText().strip()
        category = self.category_input.text().strip()
        tags = self.tags_input.text().strip()
        base_priority = self.priority_input.currentText()
        status = self.status_input.currentText()

        if not title:
            QMessageBox.warning(self, "Ошибка", "Название задачи не может быть пустым.")
            return

        has_deadline = 1 if self.deadline_checkbox.isChecked() else 0
        deadline = (
            self.deadline_input.date().toString("yyyy-MM-dd")
            if has_deadline
            else None
        )

        recurring_type = self.recurring_input.currentText()
        is_recurring = 0 if recurring_type == "Нет" else 1

        create_task(
            title=title,
            description=description,
            category=category,
            tags=tags,
            base_priority=base_priority,
            status=status,
            deadline=deadline,
            has_deadline=has_deadline,
            is_recurring=is_recurring,
            recurring_type=None if recurring_type == "Нет" else recurring_type,
        )

        QMessageBox.information(self, "Успех", "Задача сохранена.")
        self.accept()