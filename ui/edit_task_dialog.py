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
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QInputDialog,
)
from PySide6.QtCore import QDate

from database.task_repository import (
    get_task_by_id,
    update_task,
    delete_task,
    archive_task,
    RECURRING_OPTIONS,
)
from database.subtask_repository import (
    get_subtasks_by_task_id,
    create_subtask,
    update_subtask_status,
    delete_subtask,
    refresh_task_progress,
    SUBTASK_STATUSES,
)


class EditTaskDialog(QDialog):
    def __init__(self, task_id: int) -> None:
        super().__init__()

        self.task_id = task_id
        self.setWindowTitle("Редактировать задачу")
        self.resize(520, 800)

        self.task_data = get_task_by_id(task_id)

        if not self.task_data:
            QMessageBox.critical(self, "Ошибка", "Задача не найдена.")
            self.reject()
            return

        layout = QVBoxLayout(self)

        self.title_input = QLineEdit()
        self.description_input = QTextEdit()
        self.category_input = QLineEdit()
        self.tags_input = QLineEdit()

        self.priority_input = QComboBox()
        self.priority_input.addItems(["Низкий", "Средний", "Высокий"])

        self.status_input = QComboBox()
        self.status_input.addItems(
            ["Не начата", "В процессе", "Выполнена", "Не выполнена", "Отложена", "Заброшена"]
        )

        self.deadline_checkbox = QCheckBox("Указать срок")
        self.deadline_input = QDateEdit()
        self.deadline_input.setCalendarPopup(True)
        self.deadline_input.setEnabled(False)
        self.deadline_checkbox.toggled.connect(self.deadline_input.setEnabled)

        self.recurring_input = QComboBox()
        self.recurring_input.addItems(RECURRING_OPTIONS)

        self.progress_label = QLabel("Прогресс: 0%")

        self.subtasks_list = QListWidget()
        self.subtasks_list.itemDoubleClicked.connect(self.change_subtask_status)

        self.add_subtask_button = QPushButton("Добавить подзадачу")
        self.add_subtask_button.clicked.connect(self.add_subtask)

        self.delete_subtask_button = QPushButton("Удалить выбранную подзадачу")
        self.delete_subtask_button.clicked.connect(self.remove_selected_subtask)

        self.save_button = QPushButton("Сохранить изменения")
        self.save_button.clicked.connect(self.save_task)

        self.archive_button = QPushButton("Отправить в архив")
        self.archive_button.clicked.connect(self.send_to_archive)

        self.delete_button = QPushButton("Удалить задачу")
        self.delete_button.clicked.connect(self.remove_task)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.archive_button)
        buttons_layout.addWidget(self.delete_button)

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

        layout.addWidget(self.progress_label)
        layout.addWidget(QLabel("Подзадачи"))
        layout.addWidget(self.subtasks_list)
        layout.addWidget(self.add_subtask_button)
        layout.addWidget(self.delete_subtask_button)

        layout.addLayout(buttons_layout)

        self.load_task_data()
        self.load_subtasks()

    def load_task_data(self) -> None:
        (
            task_id,
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
        ) = self.task_data

        self.title_input.setText(title or "")
        self.description_input.setPlainText(description or "")
        self.category_input.setText(category or "")
        self.tags_input.setText(tags or "")
        self.priority_input.setCurrentText(base_priority or "Средний")
        self.status_input.setCurrentText(status or "Не начата")
        self.progress_label.setText(f"Прогресс: {progress}%")

        self.setWindowTitle(
            f"Редактировать задачу — базовый: {base_priority}, текущий: {current_priority}"
        )

        self.deadline_checkbox.setChecked(bool(has_deadline))
        self.deadline_input.setEnabled(bool(has_deadline))

        if deadline:
            qdate = QDate.fromString(deadline, "yyyy-MM-dd")
            if qdate.isValid():
                self.deadline_input.setDate(qdate)
            else:
                self.deadline_input.setDate(QDate.currentDate())
        else:
            self.deadline_input.setDate(QDate.currentDate())

        if is_recurring and recurring_type:
            self.recurring_input.setCurrentText(recurring_type)
        else:
            self.recurring_input.setCurrentText("Нет")

    def load_subtasks(self) -> None:
        self.subtasks_list.clear()

        subtasks = get_subtasks_by_task_id(self.task_id)

        if not subtasks:
            self.subtasks_list.addItem("Подзадач пока нет.")
            progress = refresh_task_progress(self.task_id)
            self.progress_label.setText(f"Прогресс: {progress}%")
            return

        for subtask_id, title, status in subtasks:
            item = QListWidgetItem(f"{title} | Статус: {status}")
            item.setData(256, subtask_id)
            self.subtasks_list.addItem(item)

        progress = refresh_task_progress(self.task_id)
        self.progress_label.setText(f"Прогресс: {progress}%")

    def add_subtask(self) -> None:
        title, ok = QInputDialog.getText(self, "Новая подзадача", "Название подзадачи:")

        if ok:
            title = title.strip()
            if not title:
                QMessageBox.warning(self, "Ошибка", "Название подзадачи не может быть пустым.")
                return

            create_subtask(self.task_id, title)
            self.load_subtasks()

    def change_subtask_status(self, item: QListWidgetItem) -> None:
        subtask_id = item.data(256)

        if subtask_id is None:
            return

        status, ok = QInputDialog.getItem(
            self,
            "Изменить статус",
            "Выбери новый статус:",
            SUBTASK_STATUSES,
            0,
            False,
        )

        if ok and status:
            update_subtask_status(subtask_id, status)
            self.load_subtasks()

    def remove_selected_subtask(self) -> None:
        item = self.subtasks_list.currentItem()

        if not item:
            QMessageBox.warning(self, "Ошибка", "Сначала выбери подзадачу.")
            return

        subtask_id = item.data(256)

        if subtask_id is None:
            return

        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Удалить выбранную подзадачу?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            delete_subtask(subtask_id)
            self.load_subtasks()

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

        update_task(
            task_id=self.task_id,
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

        refresh_task_progress(self.task_id)

        QMessageBox.information(self, "Успех", "Изменения сохранены.")
        self.accept()

    def send_to_archive(self) -> None:
        current_status = self.status_input.currentText()

        if current_status == "Заброшена":
            QMessageBox.warning(
                self,
                "Нельзя архивировать",
                "Заброшенные задачи не отправляются в архив.",
            )
            return

        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Отправить задачу в архив?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            archive_task(self.task_id)
            QMessageBox.information(self, "Успех", "Задача отправлена в архив.")
            self.accept()

    def remove_task(self) -> None:
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Ты точно хочешь удалить задачу?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            delete_task(self.task_id)
            QMessageBox.information(self, "Успех", "Задача удалена.")
            self.accept()