import sys
import winreg
from pathlib import Path


APP_NAME = "TaskManager"

RUN_REGISTRY_PATH = (
    r"Software\Microsoft\Windows\CurrentVersion\Run"
)


def get_app_command() -> str:
    """
    Возвращает команду для автозапуска.

    В собранной версии запускается TaskManager.exe.

    При разработке через Python запускается main.py
    через pythonw.exe, чтобы не появлялась консоль.
    """

    if getattr(sys, "frozen", False):
        executable = Path(sys.executable).resolve()

        return f'"{executable}"'

    python_exe = Path(sys.executable).resolve()

    # python.exe -> pythonw.exe
    pythonw_exe = python_exe.with_name("pythonw.exe")

    if not pythonw_exe.exists():
        pythonw_exe = python_exe

    main_py = (
        Path(__file__)
        .resolve()
        .parent
        .parent
        / "main.py"
    )

    return f'"{pythonw_exe}" "{main_py}"'


def is_autostart_enabled() -> bool:
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            RUN_REGISTRY_PATH,
            0,
            winreg.KEY_READ,
        )

        try:
            winreg.QueryValueEx(
                key,
                APP_NAME,
            )

            return True

        finally:
            winreg.CloseKey(key)

    except FileNotFoundError:
        return False

    except OSError:
        return False


def enable_autostart() -> None:
    command = get_app_command()

    key = winreg.CreateKeyEx(
        winreg.HKEY_CURRENT_USER,
        RUN_REGISTRY_PATH,
        0,
        winreg.KEY_SET_VALUE,
    )

    try:
        winreg.SetValueEx(
            key,
            APP_NAME,
            0,
            winreg.REG_SZ,
            command,
        )

    finally:
        winreg.CloseKey(key)


def disable_autostart() -> None:
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            RUN_REGISTRY_PATH,
            0,
            winreg.KEY_SET_VALUE,
        )

        try:
            winreg.DeleteValue(
                key,
                APP_NAME,
            )

        finally:
            winreg.CloseKey(key)

    except FileNotFoundError:
        pass

    except OSError:
        pass


def set_autostart(enabled: bool) -> None:
    if enabled:
        enable_autostart()
    else:
        disable_autostart()