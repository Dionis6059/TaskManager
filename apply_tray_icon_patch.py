from pathlib import Path


FILE_PATH = Path("ui/main_window.py")


def main() -> None:
    if not FILE_PATH.exists():
        raise SystemExit(
            "Не найден ui/main_window.py. "
            "Запусти этот файл из корня проекта."
        )

    text = FILE_PATH.read_text(
        encoding="utf-8"
    )

    old = '''        tray_icon = self.style().standardIcon(
            QStyle.SP_ComputerIcon
        )

        self.tray_icon.setIcon(
            tray_icon
        )
        self.setWindowIcon(
            tray_icon
        )
'''

    new = '''        tray_icon = QApplication.windowIcon()

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
'''

    if new in text:
        print(
            "Иконка уже подключена в ui/main_window.py."
        )
        return

    if old not in text:
        raise SystemExit(
            "Не удалось найти ожидаемый блок "
            "иконки в ui/main_window.py. "
            "Файл не изменён."
        )

    text = text.replace(
        old,
        new,
        1,
    )

    FILE_PATH.write_text(
        text,
        encoding="utf-8",
    )

    print(
        "Готово: ui/main_window.py обновлён."
    )


if __name__ == "__main__":
    main()
