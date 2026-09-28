from datetime import (
    date,
    datetime,
    timedelta,
)

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
    QMessageBox,
)
from PySide6.QtGui import (
    QColor,
    QBrush,
    QFont,
    QAction,
    QPainter,
    QPixmap,
)
from PySide6.QtCore import (
    QThread,
    QTimer,
    Qt,
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

from services.update_worker import UpdateWorker
from services.theme_manager import (
    build_stylesheet,
    get_saved_theme,
    get_theme,
    get_theme_background,
    get_theme_overlay,
)


CRITICAL_NOTIFICATION_HOURS = {
    9,
    15,
    21,
}

MIN_CRITICAL_NOTIFICATION_INTERVAL = timedelta(
    hours=5
)


class BackgroundWidget(QWidget):
    def __init__(
        self,
        parent=None,
    ) -> None:
        super().__init__(parent)

        self.theme_name = get_saved_theme()
        self.background_pixmap = QPixmap()

        self.reload_theme()

    def set_theme(
        self,
        theme_name: str,
    ) -> None:
        self.theme_name = theme_name
        self.reload_theme()
        self.update()

    def reload_theme(self) -> None:
        image_path = get_theme_background(
            self.theme_name
        )

        if (
            image_path is not None
            and image_path.exists()
        ):
            self.background_pixmap = QPixmap(
                str(image_path)
            )
        else:
            self.background_pixmap = QPixmap()

    def paintEvent(
        self,
        event,
    ) -> None:
        painter = QPainter(self)

        theme = get_theme(
            self.theme_name
        )

        painter.fillRect(
            self.rect(),
            QColor(theme["window"]),
        )

        if not self.background_pixmap.isNull():
            scaled = self.background_pixmap.scaled(
                self.size(),
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation,
            )

            x = (
                scaled.width()
                - self.width()
            ) // 2

            y = (
                scaled.height()
                - self.height()
            ) // 2

            painter.drawPixmap(
                0,
                0,
                scaled,
                x,
                y,
                self.width(),
                self.height(),
            )

            red, green, blue, alpha = (
                get_theme_overlay(
                    self.theme_name
                )
            )

            if alpha > 0:
                painter.fillRect(
                    self.rect(),
                    QColor(
                        red,
                        green,
                        blue,
                        alpha,
                    ),
                )

        super().paintEvent(event)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle(
            "Task Manager"
        )
        self.resize(
            1250,
            920,
        )

        self.allow_close = False

        self.current_theme = (
            get_saved_theme()
        )

        # =====================================================
        # ОБНОВЛЕНИЯ
        # =====================================================

        self.update_thread = None
        self.update_worker = None
        self.pending_update = None
        self.automatic_update_check_started = False

        # Используем, чтобы клик по уведомлению
        # о задаче не открывал окно обновления.
        self.last_tray_message_type = None

        # =====================================================
        # КРИТИЧЕСКИЕ НАПОМИНАНИЯ
        # =====================================================

        self.last_critical_notification_at = None
        self.sent_critical_slots = set()

        self.critical_timer = QTimer(
            self
        )
        self.critical_timer.setInterval(
            60 * 1000
        )
        self.critical_timer.timeout.connect(
            self.check_scheduled_critical_notification
        )

        # =====================================================
        # ТРЕЙ
        # =====================================================

        self.tray_icon = QSystemTrayIcon(
            self
        )

        tray_icon = QApplication.windowIcon()

        if tray_icon.isNull():
            tray_icon = self.style().standardIcon(
                QStyle.SP_ComputerIcon
            )

        self.tray_icon.setIcon(
            tray_icon
        )
        self.setWindowIcon(
            tray_icon
        )
        self.tray_icon.setToolTip(
            "Task Manager"
        )

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

        self.tray_icon.messageClicked.connect(
            self.on_tray_message_clicked
        )

        self.tray_icon.show()

        # =====================================================
        # ОСНОВА ОКНА
        # =====================================================

        self.central_background = (
            BackgroundWidget()
        )

        self.setCentralWidget(
            self.central_background
        )

        self.layout = QVBoxLayout(
            self.central_background
        )
        self.layout.setSpacing(
            12
        )
        self.layout.setContentsMargins(
            14,
            14,
            14,
            14,
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

        # =====================================================
        # ВЕРХНИЕ КНОПКИ
        # =====================================================

        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.setSpacing(
            8
        )

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
            button.setMinimumHeight(
                34
            )
            self.buttons_layout.addWidget(
                button
            )

        # =====================================================
        # ФИЛЬТРЫ
        # =====================================================

        self.filters_layout = QHBoxLayout()
        self.filters_layout.setSpacing(
            8
        )

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Поиск по названию..."
        )
        self.search_input.setMinimumHeight(
            32
        )

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
            widget.setMinimumHeight(
                32
            )

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

        # =====================================================
        # НАПОМИНАНИЯ
        # =====================================================

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
        self.reminders_list.setSpacing(
            4
        )

        # =====================================================
        # ПРЕДСТАВЛЕНИЯ
        # =====================================================

        self.tasks_list = QListWidget()
        self.tasks_list.itemDoubleClicked.connect(
            self.open_edit_task_dialog_from_item
        )
        self.tasks_list.setSpacing(
            6
        )

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
        self.settings_view.theme_changed.connect(
            self.apply_theme
        )

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

        # =====================================================
        # ПЕРВИЧНАЯ ЗАГРУЗКА
        # =====================================================

        self.current_view = "all"

        self.apply_theme(
            self.current_theme
        )

        self.refresh_category_filter()
        self.load_tasks()
        self.load_reminders()

        self.stacked_widget.setCurrentWidget(
            self.tasks_list
        )

        self.update_filters_visibility()
        self.update_reminders_visibility()

        # Критические задачи показываем при запуске.
        QTimer.singleShot(
            1200,
            self.show_startup_critical_notification,
        )

        self.critical_timer.start()

        # Автопроверка обновлений.
        QTimer.singleShot(
            4000,
            self.start_automatic_update_check,
        )

    # =========================================================
    # ТЕМЫ
    # =========================================================

    def apply_theme(
        self,
        theme_name: str,
    ) -> None:
        self.current_theme = theme_name

        application = QApplication.instance()

        if application is not None:
            application.setStyleSheet(
                build_stylesheet(
                    theme_name
                )
            )

        self.central_background.set_theme(
            theme_name
        )

        # Перерисовываем списки, чтобы пустые строки
        # и карточки выглядели корректно.
        if hasattr(
            self,
            "reminders_list",
        ):
            self.refresh_current_view()

    # =========================================================
    # ТРЕЙ
    # =========================================================

    def show_from_tray(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def on_tray_activated(
        self,
        reason: QSystemTrayIcon.ActivationReason,
    ) -> None:
        if (
            reason
            == QSystemTrayIcon.DoubleClick
        ):
            self.show_from_tray()

    def on_tray_message_clicked(
        self,
    ) -> None:
        if (
            self.last_tray_message_type
            == "update"
            and self.pending_update
        ):
            self.show_from_tray()
            self.show_settings()

            result = self.pending_update

            answer = QMessageBox.question(
                self,
                "Доступно обновление",
                (
                    "Доступна новая версия "
                    "Task Manager.\n\n"
                    f"Текущая версия: "
                    f"{result['current_version']}\n"
                    f"Новая версия: "
                    f"{result['latest_version']}\n\n"
                    "Скачать и установить "
                    "обновление?"
                ),
                QMessageBox.Yes
                | QMessageBox.No,
                QMessageBox.Yes,
            )

            if answer == QMessageBox.Yes:
                if result.get(
                    "installer_url"
                ):
                    self.settings_view.download_and_install_update(
                        result
                    )
                else:
                    self.settings_view.show_manual_update_dialog(
                        result
                    )

            return

        # Клик по уведомлению о задаче просто
        # открывает программу.
        self.show_from_tray()

    def quit_application(
        self,
    ) -> None:
        self.allow_close = True

        self.tray_icon.hide()
        self.close()
        QApplication.quit()

    def closeEvent(
        self,
        event,
    ) -> None:
        if self.allow_close:
            event.accept()
            return

        # Просто прячем в трей.
        # Никакого уведомления "работает в фоне".
        event.ignore()
        self.hide()

    # =========================================================
    # КРИТИЧЕСКИЕ УВЕДОМЛЕНИЯ
    # =========================================================

    def get_critical_reminders(
        self,
    ) -> list[tuple]:
        return [
            reminder
            for reminder in get_reminder_tasks()
            if reminder[5] == "Критический"
        ]

    def show_critical_notification(
        self,
    ) -> bool:
        critical = self.get_critical_reminders()

        if not critical:
            return False

        count = len(critical)

        if count == 1:
            message = (
                "Есть критическая задача:\n"
                f"{critical[0][1]}"
            )
        else:
            titles = [
                reminder[1]
                for reminder in critical[:2]
            ]

            message = (
                f"Критических задач: {count}.\n"
                + " • ".join(titles)
            )

            if count > 2:
                message += (
                    f"\nИ ещё: {count - 2}"
                )

        self.last_tray_message_type = (
            "critical"
        )

        self.tray_icon.showMessage(
            "Критические задачи",
            message,
            QSystemTrayIcon.Warning,
            10000,
        )

        self.last_critical_notification_at = (
            datetime.now()
        )

        return True

    def show_startup_critical_notification(
        self,
    ) -> None:
        self.show_critical_notification()

    def check_scheduled_critical_notification(
        self,
    ) -> None:
        now = datetime.now()

        if now.hour not in CRITICAL_NOTIFICATION_HOURS:
            return

        # Таймер проверяет раз в минуту.
        # Срабатываем только в первые две минуты часа,
        # чтобы не пропустить слот из-за небольшого дрейфа.
        if now.minute > 1:
            return

        slot = (
            now.date().isoformat(),
            now.hour,
        )

        if slot in self.sent_critical_slots:
            return

        self.sent_critical_slots.add(
            slot
        )

        if (
            self.last_critical_notification_at
            is not None
            and (
                now
                - self.last_critical_notification_at
            )
            < MIN_CRITICAL_NOTIFICATION_INTERVAL
        ):
            return

        self.show_critical_notification()

        # Чистим старые ключи, чтобы множество не росло.
        today_text = now.date().isoformat()

        self.sent_critical_slots = {
            saved_slot
            for saved_slot
            in self.sent_critical_slots
            if saved_slot[0] == today_text
        }

    # =========================================================
    # АВТООБНОВЛЕНИЕ
    # =========================================================

    def start_automatic_update_check(
        self,
    ) -> None:
        if self.automatic_update_check_started:
            return

        self.automatic_update_check_started = True

        self.update_thread = QThread()
        self.update_worker = UpdateWorker()

        self.update_worker.moveToThread(
            self.update_thread
        )

        self.update_thread.started.connect(
            self.update_worker.run
        )

        self.update_worker.update_found.connect(
            self.on_automatic_update_found
        )

        self.update_worker.no_update.connect(
            self.on_automatic_no_update
        )

        self.update_worker.error.connect(
            self.on_automatic_update_error
        )

        self.update_worker.finished.connect(
            self.update_thread.quit
        )

        self.update_worker.finished.connect(
            self.update_worker.deleteLater
        )

        self.update_thread.finished.connect(
            self.on_update_thread_finished
        )

        self.update_thread.finished.connect(
            self.update_thread.deleteLater
        )

        self.update_thread.start()

    def on_automatic_update_found(
        self,
        result: dict,
    ) -> None:
        self.pending_update = result

        self.last_tray_message_type = (
            "update"
        )

        self.tray_icon.showMessage(
            "Доступно обновление",
            (
                "Доступна новая версия "
                f"Task Manager "
                f"{result['latest_version']}.\n"
                "Нажми на уведомление, "
                "чтобы установить её."
            ),
            QSystemTrayIcon.Information,
            10000,
        )

    def on_automatic_no_update(
        self,
    ) -> None:
        self.pending_update = None

    def on_automatic_update_error(
        self,
        error_text: str,
    ) -> None:
        # Автоматическая проверка тихая.
        # Ошибка сети не должна мешать работе.
        pass

    def on_update_thread_finished(
        self,
    ) -> None:
        self.update_worker = None
        self.update_thread = None

    # =========================================================
    # ФИЛЬТРЫ
    # =========================================================

    def refresh_category_filter(
        self,
    ) -> None:
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

    def update_filters_visibility(
        self,
    ) -> None:
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
            widget.setVisible(
                visible
            )

    def update_reminders_visibility(
        self,
    ) -> None:
        visible = (
            self.current_view
            != "settings"
        )

        self.reminders_label.setVisible(
            visible
        )
        self.reminders_list.setVisible(
            visible
        )

    # =========================================================
    # КАРТОЧКИ ЗАДАЧ
    # =========================================================

    def get_task_color(
        self,
        current_priority: str,
        status: str,
    ) -> QColor:
        if status == "Выполнена":
            return QColor(
                200,
                255,
                200,
            )

        if status == "Отложена":
            return QColor(
                220,
                220,
                235,
            )

        if status == "Заброшена":
            return QColor(
                190,
                190,
                190,
            )

        if current_priority == "Критический":
            return QColor(
                255,
                170,
                170,
            )

        if current_priority == "Срочный":
            return QColor(
                255,
                210,
                150,
            )

        if current_priority == "Высокий":
            return QColor(
                255,
                245,
                170,
            )

        if current_priority == "Средний":
            return QColor(
                200,
                235,
                255,
            )

        if current_priority == "Низкий":
            return QColor(
                235,
                235,
                235,
            )

        return QColor(
            255,
            255,
            255,
        )

    def get_item_font(
        self,
        bold: bool = False,
    ) -> QFont:
        font = QFont(
            "Segoe UI",
            10,
        )
        font.setBold(
            bold
        )
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
            if is_recurring
            and recurring_type
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

    # =========================================================
    # НАПОМИНАНИЯ В ОКНЕ
    # =========================================================

    def load_reminders(
        self,
    ) -> None:
        self.reminders_list.clear()

        reminders = get_reminder_tasks()

        row_height = 42
        max_visible_items = 5

        if not reminders:
            item = QListWidgetItem(
                "Срочных напоминаний нет."
            )

            theme = get_theme(
                self.current_theme
            )

            item.setForeground(
                QBrush(
                    QColor(
                        theme["muted"]
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
            + timedelta(
                days=1
            )
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
                f"   •   Приоритет: "
                f"{current_priority}"
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

        self.reminders_list.setFixedHeight(
            visible_count
            * row_height
            + 18
        )

    # =========================================================
    # СПИСКИ ЗАДАЧ
    # =========================================================

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

            theme = get_theme(
                self.current_theme
            )

            item.setForeground(
                QBrush(
                    QColor(
                        theme["muted"]
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

    def load_tasks(
        self,
    ) -> None:
        self.populate_tasks_list(
            get_all_tasks(),
            "Пока нет задач.",
        )

    def load_today_tasks(
        self,
    ) -> None:
        self.populate_tasks_list(
            get_today_tasks(),
            (
                "На сегодня подходящих "
                "задач нет."
            ),
        )

    # =========================================================
    # ФИЛЬТРЫ
    # =========================================================

    def apply_filters(
        self,
    ) -> None:
        if self.current_view not in (
            "all",
            "today",
        ):
            return

        tasks = get_filtered_tasks(
            search_text=(
                self.search_input.text()
            ),
            category=(
                self.category_filter.currentText()
            ),
            status=(
                self.status_filter.currentText()
            ),
            priority=(
                self.priority_filter.currentText()
            ),
        )

        if self.current_view == "today":
            today_ids = {
                task[0]
                for task
                in get_today_tasks()
            }

            tasks = [
                task
                for task
                in tasks
                if task[0]
                in today_ids
            ]

            self.populate_tasks_list(
                tasks,
                (
                    "По фильтрам в разделе "
                    "'Сегодня' ничего "
                    "не найдено."
                ),
            )
        else:
            self.populate_tasks_list(
                tasks,
                (
                    "По фильтрам ничего "
                    "не найдено."
                ),
            )

    def reset_filters(
        self,
    ) -> None:
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

    # =========================================================
    # НАВИГАЦИЯ
    # =========================================================

    def show_all_tasks(
        self,
    ) -> None:
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

    def show_today_tasks(
        self,
    ) -> None:
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

    def show_calendar(
        self,
    ) -> None:
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

    def show_statistics(
        self,
    ) -> None:
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

    def show_archive(
        self,
    ) -> None:
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

    def show_settings(
        self,
    ) -> None:
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

    # =========================================================
    # REFRESH
    # =========================================================

    def refresh_current_view(
        self,
    ) -> None:
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

    def refresh_all_views(
        self,
    ) -> None:
        self.refresh_category_filter()
        self.load_tasks()
        self.load_today_tasks()
        self.load_reminders()
        self.calendar_view.refresh()
        self.statistics_view.refresh()
        self.archive_view.refresh()
        self.settings_view.refresh()

    # =========================================================
    # ДОБАВЛЕНИЕ / РЕДАКТИРОВАНИЕ
    # =========================================================

    def open_add_task_dialog(
        self,
    ) -> None:
        dialog = AddTaskDialog()

        result = dialog.exec()

        if result:
            self.refresh_all_views()
            self.refresh_current_view()

    def open_edit_task_dialog_from_item(
        self,
        item: QListWidgetItem,
    ) -> None:
        task_id = item.data(
            256
        )

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
