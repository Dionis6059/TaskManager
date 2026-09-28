import hashlib
import json
import tempfile
import urllib.error
import urllib.request
from pathlib import Path


GITHUB_OWNER = "Dionis6059"
GITHUB_REPOSITORY = "TaskManager"

LATEST_RELEASE_API_URL = (
    f"https://api.github.com/repos/"
    f"{GITHUB_OWNER}/{GITHUB_REPOSITORY}/releases/latest"
)

UPDATE_DIR = (
    Path(tempfile.gettempdir())
    / "TaskManager"
    / "updates"
)


def normalize_version(version: str) -> tuple[int, ...]:
    """
    Преобразует:
        v1.0.1
        1.0.1

    в:
        (1, 0, 1)
    """

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


def get_latest_release() -> dict:
    request = urllib.request.Request(
        LATEST_RELEASE_API_URL,
        headers={
            "User-Agent": (
                "TaskManager-UpdateChecker"
            ),
            "Accept": (
                "application/vnd.github+json"
            ),
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
            "GitHub вернул ошибку "
            f"HTTP {error.code}."
        ) from error

    except urllib.error.URLError as error:
        raise RuntimeError(
            "Не удалось подключиться "
            "к GitHub.\n"
            "Проверь подключение "
            "к интернету."
        ) from error

    except TimeoutError as error:
        raise RuntimeError(
            "GitHub не ответил вовремя."
        ) from error

    try:
        data = json.loads(
            response_text
        )

    except json.JSONDecodeError as error:
        raise RuntimeError(
            "Не удалось прочитать "
            "ответ GitHub."
        ) from error

    tag = data.get(
        "tag_name",
        "",
    )

    if not tag:
        raise RuntimeError(
            "GitHub не вернул "
            "номер последней версии."
        )

    version = tag

    if version.lower().startswith("v"):
        version = version[1:]

    installer_url = ""
    installer_name = ""
    installer_digest = ""

    for asset in data.get(
        "assets",
        [],
    ):
        asset_name = asset.get(
            "name",
            "",
        )

        asset_name_lower = (
            asset_name.lower()
        )

        if (
            asset_name_lower.endswith(
                ".exe"
            )
            and "setup"
            in asset_name_lower
        ):
            installer_name = (
                asset_name
            )

            installer_url = (
                asset.get(
                    "browser_download_url",
                    "",
                )
            )

            installer_digest = (
                asset.get(
                    "digest",
                    "",
                )
                or ""
            )

            break

    return {
        "version": version,
        "tag": tag,
        "name": data.get(
            "name",
            tag,
        ),
        "url": data.get(
            "html_url",
            "",
        ),
        "body": data.get(
            "body",
            "",
        ),
        "installer_url": (
            installer_url
        ),
        "installer_name": (
            installer_name
        ),
        "installer_digest": (
            installer_digest
        ),
    }


def check_for_updates(
    current_version: str,
) -> dict:
    release = get_latest_release()

    latest_version = release[
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
            release["url"]
        ),
        "installer_url": (
            release[
                "installer_url"
            ]
        ),
        "installer_name": (
            release[
                "installer_name"
            ]
        ),
        "installer_digest": (
            release[
                "installer_digest"
            ]
        ),
        "release_name": (
            release["name"]
        ),
        "release_notes": (
            release["body"]
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
    """
    Если GitHub вернул SHA256,
    проверяем скачанный файл.

    Если digest отсутствует,
    просто пропускаем проверку.
    """

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
            "В последнем релизе "
            "не найден установщик."
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
            "Ошибка GitHub: "
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