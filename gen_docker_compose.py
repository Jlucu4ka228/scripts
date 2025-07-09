#!/usr/bin/env python
import os
import re
from pathlib import Path

import yaml

DOCKER_COMPOSE_PATH = Path("docker-compose.yml")

def get_project_name() -> str:
    # We are ensuring run from project root in main() func, so it is safe to assume that we are in project root
    return Path(os.getcwd()).name

def get_worker_name(path: Path) -> str:
    # Извлекаем имя рабочего файла без расширения, заменяя "_" на "-"
    match = re.search(r"([^/\\]+)(?=\.py$)", str(path))
    return match.group().replace("_", "-") if match else ""


def get_service_name(path: Path) -> str:
    # Получаем имя родительской папки и имя рабочего файла
    parent_name = path.parent.parent.parent.name
    if parent_name.strip() == "":
        parent_name = get_project_name()
    print(parent_name)
    worker_name = get_worker_name(path)
    return f"{parent_name}-{worker_name}"


def generate_service_block(service_name: str, path: Path) -> dict:
    # Пытаемся вычислить относительный путь, если не получается — используем абсолютный путь
    try:
        rel_path = path.relative_to(Path.cwd())

    except ValueError:
        # Если не удаётся вычислить относительный путь, выводим предупреждение и используем абсолютный
        print(f"⚠️ Не удалось вычислить относительный путь для {path}")
        rel_path = (
            path  # Используем абсолютный путь, если относительный не удалось вычислить
        )

    # Заменяем '/' на '\\' в пути для Windows
    rel_path = str(rel_path).replace("\\", "/")

    # Формируем блок настроек для нового сервиса в Docker Compose
    return {
        "image": get_project_name(),  # Имя образа Docker
        "build": {"context": ".", "dockerfile": "Dockerfile"},  # Параметры сборки
        "container_name": service_name,  # Имя контейнера
        "command": f"bash -c 'PYTHONPATH=/application poetry run python -u {rel_path}'",  # Команда для запуска
        "restart": "always",  # Настройка перезапуска контейнера
        "volumes": ["./src:/application/src"],  # Монтируем директорию с исходным кодом
        "env_file": [".env"],  # Файл с переменными окружения
        "logging": {"options": {"max-size": "10m"}},  # Настройки логирования
        "networks": ["net"],  # Сетевые настройки
    }


def get_worker_files() -> list[Path]:
    workers = []
    # Ищем все Python файлы в папке src/workers
    for path in Path("src/workers").rglob("*.py"):
        try:
            text = path.read_text(encoding="utf-8")
            # Если файл содержит конструкцию 'if __name__ == "__main__"', добавляем его в список
            if '__name__ == "__main__"' in text:
                workers.append(path)
        except UnicodeDecodeError:
            # Если не удаётся прочитать файл, продолжаем обработку
            continue
    return workers


def main():
    # Проверяем, что скрипт запускается из корневой директории проекта
    if not Path("pyproject.toml").exists():
        print("Ошибка: Скрипт должен быть запущен из корня проекта!")
        exit(1)

    # Пытаемся загрузить существующий файл docker-compose.yml
    try:
        compose = (
            yaml.safe_load(DOCKER_COMPOSE_PATH.read_text())
            if DOCKER_COMPOSE_PATH.exists()
            else {}
        )
    except yaml.YAMLError:
        # Если файл YAML некорректен, выводим предупреждение и создаём пустой объект
        print("⚠️ Некорректный YAML, перезаписываем...")
        compose = {}

    # Устанавливаем значения по умолчанию для сервисов и сетей, если их нет
    compose.setdefault("services", {})
    compose.setdefault("networks", {"net": {"name": "net", "external": True}})

    # Получаем список всех рабочих файлов
    worker_files = get_worker_files()
    print(f"Найдено {len(worker_files)} рабочих файлов")

    added = 0
    # Для каждого рабочего файла генерируем и добавляем сервис в Docker Compose
    for path in worker_files:
        service_name = get_service_name(path)
        if service_name not in compose["services"]:
            compose["services"][service_name] = generate_service_block(
                service_name, path
            )
            print(f"✅ Добавлен сервис: {service_name}")
            added += 1

    # Записываем обновлённый файл docker-compose.yml
    DOCKER_COMPOSE_PATH.write_text(yaml.dump(compose, sort_keys=False))
    print(
        f"✅ Обновлён файл docker-compose.yml (добавлено {added} новых сервисов, всего: {len(compose['services'])})"
    )


if __name__ == "__main__":
    main()
