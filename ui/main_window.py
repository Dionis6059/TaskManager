from datetime import date, timedelta

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QHBoxLayout,
    QStackedWidget,
    QLineEdit,
    QComboBox,
    QSizePolicy,
    QSystemTrayIcon,
    QStyle,
    QMenu,
    QApplication,
)
from PySide6.QtGui import (
    QColor,
    QBrush,
    QFont,
    QAction,
)

from ui.add_task_dialog import AddTaskDialog
from ui.edit_task_dialog import EditTaskDialog
from ui.calendar_view import CalendarView
from ui.statistics_view import StatisticsView
from ui.archive_view import ArchiveView
from ui.settings_view import SettingsView

from database.task_repository import (
    get_all_tasks,
    get_today_tasks,
    get_filtered_tasks,
    get_distinct_categories,
    get_reminder_tasks,
)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("Task Manager")
        self.resize(1250, 920)

        self.allow_close = False
        self.tray_hint_shown = False

        self.tray_icon = QSystemTrayIcon(self)

        tray_icon = self.style().standardIcon(
            QStyle.SP_ComputerIcon
        )

        self.tray_icon.setIcon(tray_icon)
        self.setWindowIcon(tray_icon)
        self.tray_icon.setToolTip("Task Manager")

        self.tray_menu = QMenu()

        self.open_action = QAction(
            "Открыть Task Manager",
            self,
        )
        self.open_action.triggered.connect(
            self.show_from_tray
        )

        self.exit_action = QAction(
            "Выход",
            self,
        )
        self.exit_action.triggered.connect(
            self.quit_application
        )

        self.tray_menu.addAction(
            self.open_action
        )
        self.tray_menu.addSeparator()
        self.tray_menu.addAction(
            self.exit_action
        )

        self.tray_icon.setContextMenu(
            self.tray_menu
        )

        self.tray_icon.activated.connect(
            self.on_tray_activated
        )

        self.tray_icon.show()

        central_widget = QWidget()
        self.setCentralWidget(
            central_widget
        )

        self.layout = QVBoxLayout()
        self.layout.setSpacing(12)
        self.layout.setContentsMargins(
            14,
            14,
            14,
            14,
        )

        central_widget.setLayout(
            self.layout
        )

        self.title_label = QLabel(
            "Мой менеджер задач"
        )

        self.title_label.setFont(
            QFont(
                "Segoe UI",
                18,
                QFont.Bold,
            )
        )

        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.setSpacing(8)

        self.all_tasks_button = QPushButton(
            "Все задачи"
        )
        self.all_tasks_button.clicked.connect(
            self.show_all_tasks
        )

        self.today_button = QPushButton(
            "Сегодня"
        )
        self.today_button.clicked.connect(
            self.show_today_tasks
        )

        self.calendar_button = QPushButton(
            "Календарь"
        )
        self.calendar_button.clicked.connect(
            self.show_calendar
        )

        self.statistics_button = QPushButton(
            "Статистика"
        )
        self.statistics_button.clicked.connect(
            self.show_statistics
        )

        self.archive_button = QPushButton(
            "Архив"
        )
        self.archive_button.clicked.connect(
            self.show_archive
        )

        self.settings_button = QPushButton(
            "Настройки"
        )
        self.settings_button.clicked.connect(
            self.show_settings
        )

        self.add_task_button = QPushButton(
            "Добавить задачу"
        )
        self.add_task_button.clicked.connect(
            self.open_add_task_dialog
        )

        self.refresh_reminders_button = QPushButton(
            "Обновить напоминания"
        )
        self.refresh_reminders_button.clicked.connect(
            self.load_reminders
        )

        for button in (
            self.all_tasks_button,
            self.today_button,
            self.calendar_button,
            self.statistics_button,
            self.archive_button,
            self.settings_button,
            self.add_task_button,
            self.refresh_reminders_button,
        ):
            button.setMinimumHeight(34)

        for button in (
            self.all_tasks_button,
            self.today_button,
            self.calendar_button,
            self.statistics_button,
            self.archive_button,
            self.settings_button,
            self.add_task_button,
            self.refresh_reminders_button,
        ):
            self.buttons_layout.addWidget(button)

        self.filters_layout = QHBoxLayout()
        self.filters_layout.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Поиск по названию..."
        )
        self.search_input.setMinimumHeight(32)

        self.category_filter = QComboBox()
        self.status_filter = QComboBox()
        self.priority_filter = QComboBox()

        self.status_filter.addItems(
            [
                "Все",
                "Не начата",
                "В процессе",
                "Выполнена",
                "Не выполнена",
                "Отложена",
                "Заброшена",
            ]
        )

        self.priority_filter.addItems(
            [
                "Все",
                "Низкий",
                "Средний",
                "Высокий",
                "Срочный",
                "Критический",
            ]
        )

        self.apply_filters_button = QPushButton(
            "Применить фильтры"
        )
        self.apply_filters_button.clicked.connect(
            self.apply_filters
        )

        self.reset_filters_button = QPushButton(
            "Сбросить фильтры"
        )
        self.reset_filters_button.clicked.connect(
            self.reset_filters
        )

        for widget in (
            self.category_filter,
            self.status_filter,
            self.priority_filter,
            self.apply_filters_button,
            self.reset_filters_button,
        ):
            widget.setMinimumHeight(32)

        self.filters_layout.addWidget(
            self.search_input,
            2,
        )
        self.filters_layout.addWidget(
            self.category_filter,
            1,
        )
        self.filters_layout.addWidget(
            self.status_filter,
            1,
        )
        self.filters_layout.addWidget(
            self.priority_filter,
            1,
        )
        self.filters_layout.addWidget(
            self.apply_filters_button,
            1,
        )
        self.filters_layout.addWidget(
            self.reset_filters_button,
            1,
        )

        self.reminders_label = QLabel(
            "Напоминания"
        )
        self.reminders_label.setFont(
            QFont(
                "Segoe UI",
                12,
                QFont.Bold,
            )
        )

        self.reminders_list = QListWidget()
        self.reminders_list.itemDoubleClicked.connect(
            self.open_edit_task_dialog_from_item
        )

        self.reminders_list.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed,
        )

        self.reminders_list.setSpacing(4)

        self.tasks_list = QListWidget()
        self.tasks_list.itemDoubleClicked.connect(
            self.open_edit_task_dialog_from_item
        )
        self.tasks_list.setSpacing(6)

        self.calendar_view = CalendarView()
        self.calendar_view.task_double_clicked.connect(
            self.open_edit_task_dialog_by_id
        )

        self.statistics_view = StatisticsView()

        self.archive_view = ArchiveView()
        self.archive_view.task_double_clicked.connect(
            self.open_edit_task_dialog_by_id
        )

        self.settings_view = SettingsView()

        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(
            self.tasks_list
        )
        self.stacked_widget.addWidget(
            self.calendar_view
        )
        self.stacked_widget.addWidget(
            self.statistics_view
        )
        self.stacked_widget.addWidget(
            self.archive_view
        )
        self.stacked_widget.addWidget(
            self.settings_view
        )

        self.layout.addWidget(
            self.title_label
        )
        self.layout.addLayout(
            self.buttons_layout
        )
        self.layout.addLayout(
            self.filters_layout
        )
        self.layout.addWidget(
            self.reminders_label
        )
        self.layout.addWidget(
            self.reminders_list
        )
        self.layout.addWidget(
            self.stacked_widget
        )

        self.apply_styles()

        self.current_view = "all"

        self.refresh_category_filter()
        self.load_tasks()
        self.load_reminders()

        self.stacked_widget.setCurrentWidget(
            self.tasks_list
        )

        self.update_filters_visibility()
        self.update_reminders_visibility()

        self.show_startup_notification()

    def apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #202124;
            }

            QLabel {
                color: #f1f3f4;
            }

            QCheckBox {
                color: #f1f3f4;
                spacing: 8px;
            }

            QPushButton {
                background-color: #303134;
                color: #f1f3f4;
                border: 1px solid #5f6368;
                border-radius: 8px;
                padding: 6px 10px;
            }

            QPushButton:hover {
                background-color: #3c4043;
            }

            QPushButton:pressed {
                background-color: #4a4d51;
            }

            QLineEdit,
            QComboBox {
                background-color: #2b2c30;
                color: #f1f3f4;
                border: 1px solid #5f6368;
                border-radius: 8px;
                padding: 5px 8px;
            }

            QListWidget {
                background-color: #2b2c30;
                border: 1px solid #5f6368;
                border-radius: 10px;
                padding: 6px;
            }

            QListWidget::item:selected {
                border: 2px solid #ffffff;
            }

            QScrollBar:vertical {
                background: #2b2c30;
                width: 12px;
            }

            QScrollBar::handle:vertical {
                background: #5f6368;
                border-radius: 6px;
                min-height: 24px;
            }

            QMenu {
                background-color: #2b2c30;
                color: #f1f3f4;
                border: 1px solid #5f6368;
                padding: 5px;
            }

            QMenu::item {
                padding: 7px 25px;
            }

            QMenu::item:selected {
                background-color: #3c4043;
            }
            """
        )

    def show_from_tray(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def on_tray_activated(
        self,
        reason: QSystemTrayIcon.ActivationReason,
    ) -> None:
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_from_tray()

    def quit_application(self) -> None:
        self.allow_close = True
        self.tray_icon.hide()
        self.close()
        QApplication.quit()

    def closeEvent(self, event) -> None:
        if self.allow_close:
            event.accept()
            return

        event.ignore()
        self.hide()

        if not self.tray_hint_shown:
            self.tray_icon.showMessage(
                "Task Manager",
                "Программа продолжает работать в фоне.\n"
                "Чтобы открыть её снова, дважды нажми по значку в трее.",
                QSystemTrayIcon.Information,
                5000,
            )

            self.tray_hint_shown = True

    def refresh_category_filter(self) -> None:
        current_value = (
            self.category_filter.currentText()
        )

        categories = get_distinct_categories()

        self.category_filter.clear()
        self.category_filter.addItems(
            categories
        )

        index = self.category_filter.findText(
            current_value
        )

        if index >= 0:
            self.category_filter.setCurrentIndex(
                index
            )

    def update_filters_visibility(self) -> None:
        visible = self.current_view in (
            "all",
            "today",
        )

        for widget in (
            self.search_input,
            self.category_filter,
            self.status_filter,
            self.priority_filter,
            self.apply_filters_button,
            self.reset_filters_button,
        ):
            widget.setVisible(visible)

    def update_reminders_visibility(self) -> None:
        visible = self.current_view != "settings"

        self.reminders_label.setVisible(
            visible
        )
        self.reminders_list.setVisible(
            visible
        )

    def get_task_color(
        self,
        current_priority: str,
        status: str,
    ) -> QColor:

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

    def get_item_font(
        self,
        bold: bool = False,
    ) -> QFont:
        font = QFont(
            "Segoe UI",
            10,
        )
        font.setBold(bold)

        return font

    def format_task_item(
        self,
        task: tuple,
    ) -> QListWidgetItem:

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

        deadline_text = (
            deadline
            if has_deadline
            else "Без срока"
        )

        category_text = (
            category
            if category
            else "Без категории"
        )

        tags_text = (
            tags
            if tags
            else "Без меток"
        )

        recurring_text = (
            recurring_type
            if is_recurring and recurring_type
            else "Нет"
        )

        item_text = (
            f"{title}\n"
            f"Категория: {category_text}"
            f"   •   Метки: {tags_text}\n"
            f"Приоритет: {base_priority}"
            f" → {current_priority}"
            f"   •   Статус: {status}"
            f"   •   Прогресс: {progress}%\n"
            f"Срок: {deadline_text}"
            f"   •   Повторение: {recurring_text}"
        )

        item = QListWidgetItem(
            item_text
        )

        item.setData(
            256,
            task_id,
        )

        item.setBackground(
            QBrush(
                self.get_task_color(
                    current_priority,
                    status,
                )
            )
        )

        item.setForeground(
            QBrush(
                QColor(
                    35,
                    35,
                    35,
                )
            )
        )

        item.setFont(
            self.get_item_font()
        )

        return item

    def load_reminders(self) -> None:
        self.reminders_list.clear()

        reminders = get_reminder_tasks()

        row_height = 42
        max_visible_items = 5

        if not reminders:
            item = QListWidgetItem(
                "Срочных напоминаний нет."
            )

            item.setForeground(
                QBrush(
                    QColor(
                        220,
                        220,
                        220,
                    )
                )
            )

            self.reminders_list.addItem(
                item
            )

            self.reminders_list.setFixedHeight(
                row_height + 18
            )

            return

        today = date.today().isoformat()

        tomorrow = (
            date.today()
            + timedelta(days=1)
        ).isoformat()

        for reminder in reminders:
            (
                task_id,
                title,
                status,
                deadline,
                has_deadline,
                current_priority,
            ) = reminder

            if deadline < today:
                prefix = "Просрочено"

            elif deadline == today:
                prefix = "На сегодня"

            elif deadline == tomorrow:
                prefix = "На завтра"

            else:
                prefix = "Скоро"

            item_text = (
                f"{prefix}: {title}"
                f"   •   Срок: {deadline}"
                f"   •   Приоритет: {current_priority}"
            )

            item = QListWidgetItem(
                item_text
            )

            item.setData(
                256,
                task_id,
            )

            item.setBackground(
                QBrush(
                    self.get_task_color(
                        current_priority,
                        status,
                    )
                )
            )

            item.setForeground(
                QBrush(
                    QColor(
                        35,
                        35,
                        35,
                    )
                )
            )

            item.setFont(
                self.get_item_font()
            )

            self.reminders_list.addItem(
                item
            )

        visible_count = min(
            len(reminders),
            max_visible_items,
        )

        new_height = (
            visible_count
            * row_height
            + 18
        )

        self.reminders_list.setFixedHeight(
            new_height
        )

    def show_startup_notification(self) -> None:
        reminders = get_reminder_tasks()

        if not reminders:
            return

        critical_count = 0
        urgent_count = 0
        total_count = len(reminders)

        for reminder in reminders:
            current_priority = reminder[5]

            if current_priority == "Критический":
                critical_count += 1

            elif current_priority == "Срочный":
                urgent_count += 1

        parts = []

        if critical_count > 0:
            parts.append(
                f"критических: {critical_count}"
            )

        if urgent_count > 0:
            parts.append(
                f"срочных: {urgent_count}"
            )

        if not parts:
            parts.append(
                f"напоминаний: {total_count}"
            )

        message = (
            "Есть задачи: "
            + ", ".join(parts)
        )

        self.tray_icon.showMessage(
            "Task Manager",
            message,
            QSystemTrayIcon.Information,
            8000,
        )

    def populate_tasks_list(
        self,
        tasks: list[tuple],
        empty_text: str,
    ) -> None:

        self.tasks_list.clear()

        if not tasks:
            item = QListWidgetItem(
                empty_text
            )

            item.setForeground(
                QBrush(
                    QColor(
                        220,
                        220,
                        220,
                    )
                )
            )

            self.tasks_list.addItem(
                item
            )

            return

        for task in tasks:
            self.tasks_list.addItem(
                self.format_task_item(
                    task
                )
            )

    def load_tasks(self) -> None:
        tasks = get_all_tasks()

        self.populate_tasks_list(
            tasks,
            "Пока нет задач.",
        )

    def load_today_tasks(self) -> None:
        tasks = get_today_tasks()

        self.populate_tasks_list(
            tasks,
            "На сегодня подходящих задач нет.",
        )

    def apply_filters(self) -> None:
        if self.current_view not in (
            "all",
            "today",
        ):
            return

        tasks = get_filtered_tasks(
            search_text=self.search_input.text(),
            category=self.category_filter.currentText(),
            status=self.status_filter.currentText(),
            priority=self.priority_filter.currentText(),
        )

        if self.current_view == "today":
            today_tasks = get_today_tasks()

            today_ids = {
                task[0]
                for task in today_tasks
            }

            tasks = [
                task
                for task in tasks
                if task[0] in today_ids
            ]

            self.populate_tasks_list(
                tasks,
                "По фильтрам в разделе "
                "'Сегодня' ничего не найдено.",
            )

        else:
            self.populate_tasks_list(
                tasks,
                "По фильтрам ничего не найдено.",
            )

    def reset_filters(self) -> None:
        self.search_input.clear()

        self.refresh_category_filter()

        self.category_filter.setCurrentText(
            "Все"
        )

        self.status_filter.setCurrentText(
            "Все"
        )

        self.priority_filter.setCurrentText(
            "Все"
        )

        self.refresh_current_view()

    def show_all_tasks(self) -> None:
        self.current_view = "all"

        self.title_label.setText(
            "Мой менеджер задач — Все задачи"
        )

        self.stacked_widget.setCurrentWidget(
            self.tasks_list
        )

        self.update_filters_visibility()
        self.update_reminders_visibility()

        self.load_tasks()

    def show_today_tasks(self) -> None:
        self.current_view = "today"

        self.title_label.setText(
            "Мой менеджер задач — Сегодня"
        )

        self.stacked_widget.setCurrentWidget(
            self.tasks_list
        )

        self.update_filters_visibility()
        self.update_reminders_visibility()

        self.load_today_tasks()

    def show_calendar(self) -> None:
        self.current_view = "calendar"

        self.title_label.setText(
            "Мой менеджер задач — Календарь"
        )

        self.stacked_widget.setCurrentWidget(
            self.calendar_view
        )

        self.update_filters_visibility()
        self.update_reminders_visibility()

        self.calendar_view.refresh()

    def show_statistics(self) -> None:
        self.current_view = "statistics"

        self.title_label.setText(
            "Мой менеджер задач — Статистика"
        )

        self.stacked_widget.setCurrentWidget(
            self.statistics_view
        )

        self.update_filters_visibility()
        self.update_reminders_visibility()

        self.statistics_view.refresh()

    def show_archive(self) -> None:
        self.current_view = "archive"

        self.title_label.setText(
            "Мой менеджер задач — Архив"
        )

        self.stacked_widget.setCurrentWidget(
            self.archive_view
        )

        self.update_filters_visibility()
        self.update_reminders_visibility()

        self.archive_view.refresh()

    def show_settings(self) -> None:
        self.current_view = "settings"

        self.title_label.setText(
            "Мой менеджер задач — Настройки"
        )

        self.stacked_widget.setCurrentWidget(
            self.settings_view
        )

        self.update_filters_visibility()
        self.update_reminders_visibility()

        self.settings_view.refresh()

    def refresh_current_view(self) -> None:
        self.refresh_category_filter()
        self.load_reminders()

        if self.current_view == "today":
            self.load_today_tasks()

        elif self.current_view == "calendar":
            self.calendar_view.refresh()

        elif self.current_view == "statistics":
            self.statistics_view.refresh()

        elif self.current_view == "archive":
            self.archive_view.refresh()

        elif self.current_view == "settings":
            self.settings_view.refresh()

        else:
            self.load_tasks()

    def refresh_all_views(self) -> None:
        self.refresh_category_filter()
        self.load_tasks()
        self.load_today_tasks()
        self.load_reminders()
        self.calendar_view.refresh()
        self.statistics_view.refresh()
        self.archive_view.refresh()
        self.settings_view.refresh()

    def open_add_task_dialog(self) -> None:
        dialog = AddTaskDialog()

        result = dialog.exec()

        if result:
            self.refresh_all_views()
            self.refresh_current_view()

    def open_edit_task_dialog_from_item(
        self,
        item: QListWidgetItem,
    ) -> None:

        task_id = item.data(256)

        if task_id is None:
            return

        self.open_edit_task_dialog_by_id(
            task_id
        )

    def open_edit_task_dialog_by_id(
        self,
        task_id: int,
    ) -> None:

        dialog = EditTaskDialog(
            task_id
        )

        result = dialog.exec()

        if result:
            self.refresh_all_views()
            self.refresh_current_view()