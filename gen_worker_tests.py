#!/usr/bin/env python

# TODO: rewrite using MAKO

import os
import re
from pathlib import Path

output_script = "tests/workers/test_workers.py"

root_imports = [
    "import asyncio\n",
    "import pytest\n",
    "from src.helper import redis_client\n",
]


def main():
    if not os.path.exists("pyproject.toml"):
        print("Нужно запускать из корня проекта!")
        exit(-1)

    pathlist = Path("src/workers").rglob("*.py")
    workers_to_test: list[Path] = []
    for path in pathlist:
        with open(path) as worker_file:
            if 'if __name__ == "__main__":' in worker_file.read():
                workers_to_test.append(path)

    # Проверка, существует ли директория, если нет - создаём её
    os.makedirs(os.path.dirname(output_script), exist_ok=True)

    try:
        with open(output_script, "w"):  # Создаём файл, если его нет
            pass
    except OSError as e:
        print(f"Ошибка при создании файла: {e}")
        exit(-1)

    with open(output_script, "r+") as script_file:
        script_content = script_file.read()
        tests: list[str] = []
        for import_ in root_imports:
            if import_ not in script_content:
                if import_ == "from src.helper import redis_client":
                    if not os.path.exists("src/helper.py"):
                        print("Не найден helper(s) файл в директории src, его присутствие необходимо для импорта redis_client. ")
                        print("Пожалуйста, добавьте его и перезапустите скрипт")
                        exit(-1)

                script_file.write(import_)

        for worker_path in workers_to_test:
            worker_name = worker_path.name[:-3]
            if f"def test_{worker_name}" in script_content:
                print(f"Тест для {worker_name} уже существует, пропускаю")
                continue

            with open(worker_path, "r+") as worker_file:
                start_line = ""

                lines = worker_file.readlines()
                for index, line in enumerate(lines):
                    if 'if __name__ == "__main__":' in line:
                        start_line = lines[index + 1].strip()
                        break
                else:
                    print(f"Не нашёл линии запуска у воркера {worker_path}")
                    exit(-1)
                import_path = (
                    str(worker_path)
                    .replace(".py", "")
                    .replace("/", ".")
                    .replace("\\", ".")
                )
                class_name = re.search(pattern=r"\w+(?=\(.*\))", string=start_line)
                if class_name is None:
                    print(
                        "Ошбика при поиске названия класса воркера (скорее всего не сработал регекс"
                    )
                    exit(-1)
                class_name = class_name.group()

                import_line = f"from {import_path} import {class_name}"
                tests.append(
                    f"""{import_line}
@pytest.mark.asyncio
async def test_{worker_name}():
    try:
        async with asyncio.timeout(2):
            {start_line}
            await {start_line.split("=")[0].strip()}.start()
    except asyncio.TimeoutError:
        assert True
    except Exception as e:
        print(f"Тест провален: {{e}}")
        assert False
"""
                )
        for test_ in tests:
            script_file.write(test_ + "\n")


if __name__ == "__main__":
    main()
