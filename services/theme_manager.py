import json
import os
import sys
from pathlib import Path


DEFAULT_THEME = "Тёмная"

THEMES = {
    "Тёмная": {
        "window": "#202124",
        "panel": "#2b2c30",
        "panel_alt": "#303134",
        "hover": "#3c4043",
        "pressed": "#4a4d51",
        "text": "#f1f3f4",
        "muted": "#bdc1c6",
        "border": "#5f6368",
        "selection": "#8ab4f8",
        "background_image": None,
        "overlay": (0, 0, 0, 0),
        "translucent": False,
    },
    "Светлая": {
        "window": "#f5f7fb",
        "panel": "#ffffff",
        "panel_alt": "#eef2f7",
        "hover": "#e1e7ef",
        "pressed": "#d5dde8",
        "text": "#1f2937",
        "muted": "#667085",
        "border": "#c8d0dc",
        "selection": "#2563eb",
        "background_image": None,
        "overlay": (255, 255, 255, 0),
        "translucent": False,
    },
    "Синяя": {
        "window": "#0c1729",
        "panel": "#12243d",
        "panel_alt": "#173153",
        "hover": "#20436f",
        "pressed": "#285585",
        "text": "#edf6ff",
        "muted": "#a9c4df",
        "border": "#3f6f9f",
        "selection": "#63b3ff",
        "background_image": None,
        "overlay": (0, 0, 0, 0),
        "translucent": False,
    },
    "Фиолетовая": {
        "window": "#191326",
        "panel": "#271d3a",
        "panel_alt": "#33244d",
        "hover": "#463164",
        "pressed": "#584079",
        "text": "#f5efff",
        "muted": "#cdbce6",
        "border": "#76579d",
        "selection": "#c084fc",
        "background_image": None,
        "overlay": (0, 0, 0, 0),
        "translucent": False,
    },
    "Волшебная вода": {
        "window": "#101827",
        "panel": "rgba(12, 22, 38, 205)",
        "panel_alt": "rgba(19, 32, 52, 215)",
        "hover": "rgba(31, 61, 88, 225)",
        "pressed": "rgba(45, 77, 105, 235)",
        "text": "#f8fbff",
        "muted": "#c9dbea",
        "border": "#5ec6d7",
        "selection": "#70e1f5",
        "background_image": "assets/themes/magic_water.jpg",
        "overlay": (4, 12, 25, 105),
        "translucent": True,
    },
    "Волшебный лес": {
        "window": "#0b1016",
        "panel": "rgba(8, 14, 20, 205)",
        "panel_alt": "rgba(15, 23, 32, 215)",
        "hover": "rgba(35, 46, 58, 225)",
        "pressed": "rgba(47, 61, 76, 235)",
        "text": "#fff9ff",
        "muted": "#d6d5e8",
        "border": "#9e74d8",
        "selection": "#e38cff",
        "background_image": "assets/themes/magic_forest.jpg",
        "overlay": (0, 5, 12, 100),
        "translucent": True,
    },
}


def _app_data_dir() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA")

    if local_app_data:
        path = Path(local_app_data) / "TaskManager"
    else:
        path = Path.home() / "TaskManager"

    path.mkdir(parents=True, exist_ok=True)
    return path


SETTINGS_PATH = _app_data_dir() / "settings.json"


def resource_path(relative_path: str) -> Path:
    if getattr(sys, "frozen", False):
        base_path = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    else:
        base_path = Path(__file__).resolve().parent.parent

    return base_path / relative_path


def load_settings() -> dict:
    if not SETTINGS_PATH.exists():
        return {}

    try:
        with SETTINGS_PATH.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if isinstance(data, dict):
            return data

    except (OSError, json.JSONDecodeError):
        pass

    return {}


def save_settings(data: dict) -> None:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)

    with SETTINGS_PATH.open("w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2,
        )


def get_theme_names() -> list[str]:
    return list(THEMES.keys())


def get_saved_theme() -> str:
    theme = load_settings().get("theme", DEFAULT_THEME)

    if theme not in THEMES:
        return DEFAULT_THEME

    return theme


def save_theme(theme_name: str) -> None:
    if theme_name not in THEMES:
        theme_name = DEFAULT_THEME

    settings = load_settings()
    settings["theme"] = theme_name
    save_settings(settings)


def get_theme(theme_name: str) -> dict:
    return THEMES.get(theme_name, THEMES[DEFAULT_THEME])


def get_theme_background(theme_name: str) -> Path | None:
    relative_path = get_theme(theme_name).get("background_image")

    if not relative_path:
        return None

    return resource_path(relative_path)


def get_theme_overlay(theme_name: str) -> tuple[int, int, int, int]:
    return tuple(get_theme(theme_name).get("overlay", (0, 0, 0, 0)))


def build_stylesheet(theme_name: str) -> str:
    theme = get_theme(theme_name)

    window = theme["window"]
    panel = theme["panel"]
    panel_alt = theme["panel_alt"]
    hover = theme["hover"]
    pressed = theme["pressed"]
    text = theme["text"]
    muted = theme["muted"]
    border = theme["border"]
    selection = theme["selection"]

    return f"""
    QMainWindow, QDialog {{
        background-color: {window};
        color: {text};
    }}

    QWidget {{
        color: {text};
        font-family: "Segoe UI";
    }}

    QLabel {{
        color: {text};
        background: transparent;
    }}

    QCheckBox, QRadioButton {{
        color: {text};
        background: transparent;
        spacing: 8px;
    }}

    QGroupBox {{
        color: {text};
        background-color: {panel};
        border: 1px solid {border};
        border-radius: 10px;
        margin-top: 12px;
        padding-top: 8px;
    }}

    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 5px;
        color: {text};
    }}

    QPushButton {{
        background-color: {panel_alt};
        color: {text};
        border: 1px solid {border};
        border-radius: 8px;
        padding: 6px 10px;
    }}

    QPushButton:hover {{
        background-color: {hover};
    }}

    QPushButton:pressed {{
        background-color: {pressed};
    }}

    QPushButton:disabled {{
        color: {muted};
    }}

    QLineEdit,
    QComboBox,
    QDateEdit,
    QDateTimeEdit,
    QSpinBox,
    QDoubleSpinBox,
    QTextEdit,
    QPlainTextEdit {{
        background-color: {panel};
        color: {text};
        border: 1px solid {border};
        border-radius: 8px;
        padding: 5px 8px;
        selection-background-color: {selection};
    }}

    QComboBox QAbstractItemView {{
        background-color: {panel};
        color: {text};
        border: 1px solid {border};
        selection-background-color: {hover};
        selection-color: {text};
    }}

    QListWidget,
    QTreeWidget,
    QTableWidget,
    QTableView {{
        background-color: {panel};
        color: {text};
        border: 1px solid {border};
        border-radius: 10px;
        padding: 6px;
        selection-background-color: {selection};
    }}

    QListWidget::item:selected,
    QTreeWidget::item:selected,
    QTableWidget::item:selected {{
        border: 2px solid {selection};
    }}

    QHeaderView::section {{
        background-color: {panel_alt};
        color: {text};
        border: 1px solid {border};
        padding: 6px;
    }}

    QCalendarWidget QWidget {{
        color: {text};
    }}

    QCalendarWidget QAbstractItemView:enabled {{
        background-color: {panel};
        color: {text};
        selection-background-color: {selection};
        selection-color: #ffffff;
    }}

    QMenu {{
        background-color: {panel};
        color: {text};
        border: 1px solid {border};
        padding: 5px;
    }}

    QMenu::item {{
        padding: 7px 25px;
    }}

    QMenu::item:selected {{
        background-color: {hover};
    }}

    QToolTip {{
        background-color: {panel_alt};
        color: {text};
        border: 1px solid {border};
    }}

    QScrollBar:vertical {{
        background: {panel};
        width: 12px;
    }}

    QScrollBar::handle:vertical {{
        background: {border};
        border-radius: 6px;
        min-height: 24px;
    }}

    QScrollBar:horizontal {{
        background: {panel};
        height: 12px;
    }}

    QScrollBar::handle:horizontal {{
        background: {border};
        border-radius: 6px;
        min-width: 24px;
    }}

    QStackedWidget {{
        background: transparent;
        border: none;
    }}
    """


def get_empty_text_color(theme_name: str) -> str:
    return get_theme(theme_name)["muted"]
