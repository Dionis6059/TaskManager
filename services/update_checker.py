import hashlib
import json
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path


GITHUB_OWNER = "Dionis6059"
GITHUB_REPOSITORY = "TaskManager"

# Больше не используем GitHub REST API для проверки версии.
# Читаем обычный JSON-файл из репозитория.
UPDATE_MANIFEST_URL = (
    f"https://raw.githubusercontent.com/"
    f"{GITHUB_OWNER}/{GITHUB_REPOSITORY}/main/version.json"
)

UPDATE_DIR = (
    Path(tempfile.gettempdir())
    / "TaskManager"
    / "updates"
)


def normalize_version(version: str) -> tuple[int, ...]:
    version = version.strip()

    if version.lower().startswith("v"):
        version = version[1:]

    parts = version.split(".")
    result = []

    for part in parts:
        number = ""

        for character in part:
            if character.isdigit():
                number += character
            else:
                break

        if number:
            result.append(int(number))
        else:
            result.append(0)

    return tuple(result)


def is_newer_version(
    latest_version: str,
    current_version: str,
) -> bool:
    latest = normalize_version(
        latest_version
    )

    current = normalize_version(
        current_version
    )

    max_length = max(
        len(latest),
        len(current),
    )

    latest += (
        0,
    ) * (
        max_length
        - len(latest)
    )

    current += (
        0,
    ) * (
        max_length
        - len(current)
    )

    return latest > current


def get_update_manifest() -> dict:
    # cache-bust нужен, чтобы после публикации новой версии
    # клиент не получил старый version.json из кэша.
    url = (
        f"{UPDATE_MANIFEST_URL}"
        f"?t={int(time.time())}"
    )

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "TaskManager-UpdateChecker"
            ),
            "Accept": "application/json",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=15,
        ) as response:
            response_text = (
                response.read().decode(
                    "utf-8"
                )
            )

    except urllib.error.HTTPError as error:
        raise RuntimeError(
            "Не удалось получить информацию "
            "об обновлении.\n"
            f"HTTP {error.code}."
        ) from error

    except urllib.error.URLError as error:
        raise RuntimeError(
            "Не удалось подключиться "
            "к серверу обновлений.\n"
            "Проверь подключение к интернету."
        ) from error

    except TimeoutError as error:
        raise RuntimeError(
            "Сервер обновлений "
            "не ответил вовремя."
        ) from error

    try:
        data = json.loads(
            response_text
        )

    except json.JSONDecodeError as error:
        raise RuntimeError(
            "Не удалось прочитать "
            "информацию об обновлении."
        ) from error

    version = str(
        data.get(
            "version",
            "",
        )
    ).strip()

    if not version:
        raise RuntimeError(
            "В файле обновления "
            "не указан номер версии."
        )

    installer_url = str(
        data.get(
            "installer_url",
            "",
        )
    ).strip()

    installer_name = str(
        data.get(
            "installer_name",
            "",
        )
    ).strip()

    release_url = str(
        data.get(
            "release_url",
            "",
        )
    ).strip()

    release_name = str(
        data.get(
            "release_name",
            f"Task Manager v{version}",
        )
    ).strip()

    release_notes = str(
        data.get(
            "release_notes",
            "",
        )
    )

    sha256 = str(
        data.get(
            "sha256",
            "",
        )
    ).strip()

    installer_digest = ""

    if sha256:
        installer_digest = (
            f"sha256:{sha256}"
        )

    return {
        "version": version,
        "release_url": release_url,
        "installer_url": installer_url,
        "installer_name": installer_name,
        "installer_digest": installer_digest,
        "release_name": release_name,
        "release_notes": release_notes,
    }


def check_for_updates(
    current_version: str,
) -> dict:
    manifest = get_update_manifest()

    latest_version = manifest[
        "version"
    ]

    return {
        "update_available": (
            is_newer_version(
                latest_version,
                current_version,
            )
        ),
        "current_version": (
            current_version
        ),
        "latest_version": (
            latest_version
        ),
        "release_url": (
            manifest[
                "release_url"
            ]
        ),
        "installer_url": (
            manifest[
                "installer_url"
            ]
        ),
        "installer_name": (
            manifest[
                "installer_name"
            ]
        ),
        "installer_digest": (
            manifest[
                "installer_digest"
            ]
        ),
        "release_name": (
            manifest[
                "release_name"
            ]
        ),
        "release_notes": (
            manifest[
                "release_notes"
            ]
        ),
    }


def calculate_sha256(
    file_path: Path,
) -> str:
    sha256 = hashlib.sha256()

    with file_path.open(
        "rb"
    ) as file:
        while True:
            chunk = file.read(
                1024 * 1024
            )

            if not chunk:
                break

            sha256.update(
                chunk
            )

    return sha256.hexdigest()


def verify_installer(
    installer_path: Path,
    expected_digest: str,
) -> bool:
    # SHA256 в version.json можно оставить пустым.
    # Тогда проверка просто пропускается.
    if not expected_digest:
        return True

    expected_digest = (
        expected_digest.strip()
    )

    if not expected_digest.startswith(
        "sha256:"
    ):
        return True

    expected_hash = (
        expected_digest
        .split(
            ":",
            1,
        )[1]
        .lower()
    )

    actual_hash = (
        calculate_sha256(
            installer_path
        )
        .lower()
    )

    return (
        actual_hash
        == expected_hash
    )


def download_installer(
    installer_url: str,
    installer_name: str,
    expected_digest: str = "",
) -> Path:
    if not installer_url:
        raise RuntimeError(
            "Для новой версии "
            "не указан установщик."
        )

    if not installer_name:
        installer_name = (
            "TaskManager-Setup.exe"
        )

    UPDATE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    installer_path = (
        UPDATE_DIR
        / installer_name
    )

    request = urllib.request.Request(
        installer_url,
        headers={
            "User-Agent": (
                "TaskManager-Updater"
            ),
        },
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=60,
        ) as response:
            with installer_path.open(
                "wb"
            ) as file:
                while True:
                    chunk = (
                        response.read(
                            1024 * 1024
                        )
                    )

                    if not chunk:
                        break

                    file.write(
                        chunk
                    )

    except urllib.error.HTTPError as error:
        raise RuntimeError(
            "Не удалось скачать "
            "обновление.\n"
            "Ошибка сервера: "
            f"HTTP {error.code}."
        ) from error

    except urllib.error.URLError as error:
        raise RuntimeError(
            "Не удалось скачать "
            "обновление.\n"
            "Проверь интернет."
        ) from error

    except TimeoutError as error:
        raise RuntimeError(
            "Загрузка обновления "
            "заняла слишком много времени."
        ) from error

    if not installer_path.exists():
        raise RuntimeError(
            "Установщик не был скачан."
        )

    if installer_path.stat().st_size == 0:
        raise RuntimeError(
            "Скачанный установщик пуст."
        )

    if not verify_installer(
        installer_path,
        expected_digest,
    ):
        try:
            installer_path.unlink()
        except OSError:
            pass

        raise RuntimeError(
            "Проверка целостности "
            "обновления не пройдена.\n"
            "Установщик удалён."
        )

    return installer_path
