import requests
import os
import re
import time
import sys  # Добавьте sys, так как оно используется для поиска в sys.path

def get_latest_telegram_version():
    url = "https://api.github.com/repos/telegramdesktop/tdesktop/releases/latest"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        version = data.get('tag_name')
        if version:
            # Удаляем префикс 'v', если он есть
            version = version.lstrip('v')
            print(f"Получена последняя версия Telegram Desktop: {version}")
            return version
        else:
            print("Не удалось получить тег версии из ответа JSON.")
    else:
        print(f"Ошибка при запросе к GitHub API: {response.status_code}")
    return None

def update_app_version_in_api_file(new_version):
    # Найти путь к пакету opentele в site-packages
    for path in sys.path:
        if 'site-packages' in path and os.path.exists(os.path.join(path, 'opentele')):
            api_file_path = os.path.join(path, 'opentele', 'api.py')
            break
    else:
        raise FileNotFoundError("Не удалось найти библиотеку opentele")

    # Теперь api_file_path указывает на правильный файл
    with open(api_file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # Обновляем версию в контенте файла
    new_content = content.replace("version_placeholder", new_version)

    with open(api_file_path, 'w', encoding='utf-8') as file:
        file.write(new_content)
    print(f"Файл {api_file_path} успешно обновлён. Новая версия: {new_version}")

def main():
    latest_version = get_latest_telegram_version()
    if latest_version:
        update_app_version_in_api_file(latest_version)
        time.sleep(1)
    else:
        print("Не удалось получить последнюю версию Telegram Desktop.")

if __name__ == "__main__":
    main()
