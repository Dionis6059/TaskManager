from PySide6.QtCore import QObject, Signal, Slot

from services.update_checker import check_for_updates
from version import APP_VERSION


class UpdateWorker(QObject):
    update_found = Signal(dict)
    no_update = Signal()
    error = Signal(str)
    finished = Signal()

    @Slot()
    def run(self) -> None:
        try:
            result = check_for_updates(
                APP_VERSION
            )

            if result["update_available"]:
                self.update_found.emit(
                    result
                )
            else:
                self.no_update.emit()

        except Exception as error:
            # При автоматической проверке
            # не раздражаем пользователя
            # сообщением об ошибке сети.
            self.error.emit(
                str(error)
            )

        finally:
            self.finished.emit()