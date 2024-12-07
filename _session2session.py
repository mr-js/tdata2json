import sys
import os
import telethon
from telethon import TelegramClient, errors, events
from telethon.sync import types
from telethon.tl import functions
from telethon.errors import PhoneNumberBannedError, FloodWaitError, UserDeactivatedBanError, \
    PhoneCodeInvalidError, SessionPasswordNeededError, PasswordHashInvalidError, AuthRestartError
from asyncio import IncompleteReadError

from _utils import clear, get_two_fa_password, get_json, generate_connection_params, generate_random_app_version, generate_random_windows_name, generate_random_windows_version, get_current_timestamp, random_from_file, load_api_params_from_json, SESSIONS_DIR, TDATAS_DIR, CONVERT_TDATA, CONVERT_SESSION, CONVERT_SESSIONS

import re
import shutil
import asyncio
import json
import random
import rich
import socks

from random import choice
from time import sleep
from random import randint
import datetime
from faker import Faker
import time


# Функция для загрузки прокси из файла _proxy.txt
def load_proxies_from_file() -> list:
    """Загрузка прокси из файла _proxy.txt."""
    proxies = []
    try:
        with open('_proxy.txt', 'r') as f:
            for line in f:
                if line.strip():
                    proxies.append(line.strip())
    except FileNotFoundError:
        print("Файл _proxy.txt не найден, работаем без прокси")
    return proxies if proxies else None

# Функция для загрузки прокси, привязанных к аккаунтам
def load_account_proxies(path: str) -> list:
    """Загрузка прокси, привязанных к аккаунтам."""
    proxies = []
    try:
        for filename in os.listdir(path):
            if filename.endswith(".json"):
                with open(os.path.join(path, filename), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'proxy' in data:
                        proxy = data['proxy']
                        if proxy:
                            proxies.append(proxy)
    except FileNotFoundError:
        print(f"Не найдено JSON файлов в директории {path}")
    return proxies if proxies else None

# Функция для загрузки всех прокси
def load_proxies(settings: dict, path: str) -> list:
    """Загрузка прокси либо из файла, либо из аккаунта."""
    if settings.get('use_account_proxy', False):
        return load_account_proxies(path)  # Загружаем прокси из аккаунтов
    elif settings.get('use_proxy', False):
        return load_proxies_from_file()  # Загружаем прокси из _proxy.txt
    else:
        return None  # Прокси не используется

def get_proxy_args(settings: dict, path: str):
    """Получение параметров прокси для подключения."""
    proxies = load_proxies(settings, path)
    proxy = choice(proxies) if proxies else None
    if proxy:
        try:
            if isinstance(proxy, list):
                # Прокси из аккаунта (JSON-файла)
                protocol = proxy[0].lower()
                proxy_ip = proxy[1]
                proxy_port = int(proxy[2])

                # Проверяем наличие логина и пароля
                proxy_user = proxy[4] if len(proxy) > 4 else None
                proxy_pass = proxy[5] if len(proxy) > 5 else None

                # Определяем тип прокси
                if protocol == 'http':
                    proxy_type = socks.HTTP
                elif protocol == 'socks5':
                    proxy_type = socks.SOCKS5
                elif protocol == 'socks4':
                    proxy_type = socks.SOCKS4
                else:
                    print(f"Неизвестный протокол прокси: {protocol}")
                    return {}

                print(f"Используем прокси из аккаунта: {protocol}://{proxy_ip}:{proxy_port}")

                # Проверяем, требуется ли аутентификация
                if proxy_user and proxy_pass:
                    proxy_tuple = (
                        proxy_type,
                        proxy_ip,
                        proxy_port,
                        True,
                        proxy_user,
                        proxy_pass
                    )
                else:
                    proxy_tuple = (
                        proxy_type,
                        proxy_ip,
                        proxy_port
                    )
                return proxy_tuple

            elif isinstance(proxy, str):
                # Прокси из файла _proxy.txt
                parts = proxy.strip().split(':')
                if len(parts) == 2:
                    proxy_ip, proxy_port = parts
                    proxy_port = int(proxy_port)
                    print(f"Используем прокси из файла: {proxy_ip}:{proxy_port}")

                    proxy_tuple = (
                        socks.HTTP,
                        proxy_ip,
                        proxy_port
                    )
                    return proxy_tuple
                elif len(parts) == 4:
                    proxy_ip, proxy_port, proxy_user, proxy_pass = parts
                    proxy_port = int(proxy_port)
                    print(f"Используем прокси из файла: {proxy_ip}:{proxy_port} с авторизацией")

                    proxy_tuple = (
                        socks.HTTP,
                        proxy_ip,
                        proxy_port,
                        True,
                        proxy_user,
                        proxy_pass
                    )
                    return proxy_tuple
                else:
                    print(f"Ошибка: Некорректный формат прокси: {proxy}")
                    return {}
            else:
                print(f"Ошибка: Неизвестный формат прокси: {proxy}")
                return {}
        except Exception as e:
            print(f"Ошибка при обработке прокси: {e}")
            return {}
    else:
        return {}

# Main function to convert sessions
async def SessionToSession(settings: dict):
    for session_file in os.listdir(CONVERT_SESSIONS):
        if session_file.endswith('.session'):
            session_path = os.path.join(CONVERT_SESSIONS, session_file)
            await convert_session_session(session_path, settings)

async def convert_session_session(session_path: str, settings: dict):
    session_name = os.path.splitext(os.path.basename(session_path))[0]
    base_path = os.path.dirname(session_path)
    new_client = None  # Инициализируем new_client

    print(f"Загружаем параметры API из файла {session_name}.json в папке {base_path}")

    try:
        api_params = load_api_params_from_json(session_name + '.json', base_path)
    except FileNotFoundError as e:
        print(f"JSON-файл для сессии {session_name} не найден. Пропускаем эту сессию.")
        return  # Пропускаем текущую сессию и продолжаем со следующей
    except Exception as e:
        print(f"Ошибка при загрузке параметров API для сессии {session_name}: {e}")
        return  # Пропускаем текущую сессию из-за ошибки

    if not api_params or not api_params.get('api_id') or not api_params.get('api_hash'):
        print(f"Ошибка: Не удалось загрузить api_id и api_hash для сессии {session_name}.")
        return

    api_id = int(api_params['api_id'])
    api_hash = api_params['api_hash']
    device_model = api_params.get('device_model', 'Desktop')
    system_version = api_params.get('system_version', 'Windows 10')
    app_version = api_params.get('app_version', '1.0')
    lang_code = api_params.get('lang_code', 'en')
    system_lang_code = api_params.get('system_lang_code', 'en-US')
    twoFA = api_params.get('twoFA', None)

    # Получаем параметры прокси, если они есть
    proxy_args = get_proxy_args(settings, base_path)

    old_client = TelegramClient(
        session=session_path,
        api_id=api_id,
        api_hash=api_hash,
        device_model=device_model,
        system_version=system_version,
        app_version=app_version,
        lang_code=lang_code,
        system_lang_code=system_lang_code,
        proxy=proxy_args if proxy_args else None
    )

    try:
        # Подключаемся к старому клиенту
        print("Подключаемся к старому клиенту...")
        await old_client.connect()

        if not await old_client.is_user_authorized():
            print(f"Сессия {session_name} не авторизована. Пропускаем.")
            return

        me = await old_client.get_me()
        phone = me.phone
        print(f"Номер телефона: {phone}")

        new_connection_params = generate_connection_params()
        print(f"Генерируем новые параметры подключения: {vars(new_connection_params)}")

        new_session_path = os.path.join('output', session_name + '.session')
        new_client = TelegramClient(
            session=new_session_path,
            api_id=new_connection_params.api_id,
            api_hash=new_connection_params.api_hash,
            device_model=new_connection_params.device_model,
            system_version=new_connection_params.system_version,
            app_version=new_connection_params.app_version,
            lang_code=new_connection_params.lang_code,
            system_lang_code=new_connection_params.system_lang_code,
            proxy=proxy_args if proxy_args else None
        )

        await new_client.connect()
        print(f"Подключаемся к новому клиенту для номера {phone}...")

        for attempt in range(settings.get('connection_attempts', 5)):
            try:
                print("Отправляем запрос на получение кода подтверждения...")
                await new_client.send_code_request(phone)
            except FloodWaitError as e:
                print(f"FloodWaitError: необходимо подождать {e.seconds} секунд. Пропускаем эту сессию.")
                return
            except RpcError as e:
                print(f"Ошибка RPC при отправке запроса кода подтверждения: {e}. Пропускаем эту сессию.")
                return
            except (OSError, IncompleteReadError) as e:
                print(f"Ошибка соединения при отправке запроса кода подтверждения: {e}")
                print("Пропускаем эту сессию.")
                return
            except Exception as e:
                print(f"Неизвестная ошибка при отправке запроса кода подтверждения: {e}")
                print("Пропускаем эту сессию.")
                return

            code_received = asyncio.Event()

            @old_client.on(events.NewMessage(incoming=True))
            async def handler(event):
                if event.message.sender_id == 777000:  # Telegram
                    message_text = event.message.message
                    code_match = re.search(r'(\d{5})', message_text)
                    if code_match:
                        code = code_match.group(1)
                        code_received.code = code
                        code_received.set()

            print("Ожидаем получение кода подтверждения...")

            start_time = time.time()
            timeout = 60  # Таймаут ожидания в секундах

            while not code_received.is_set():
                await asyncio.sleep(0.1)
                if time.time() - start_time > timeout:
                    print("Таймаут ожидания кода подтверждения истек. Пропускаем эту сессию.")
                    old_client.remove_event_handler(handler)
                    return

            print("Удаляем обработчик событий...")
            old_client.remove_event_handler(handler)

            try:
                print(f"Авторизация с кодом: {code_received.code}")
                await new_client.sign_in(phone=phone, code=code_received.code)

                if not await new_client.is_user_authorized():
                    raise SessionPasswordNeededError()

                break  # Успешная авторизация

            except SessionPasswordNeededError:
                if twoFA:
                    print(f"Используем двухфакторную аутентификацию для {phone}")
                    await new_client.sign_in(password=twoFA)
                    if await new_client.is_user_authorized():
                        break  # Успешная авторизация
                    else:
                        print("Не удалось авторизоваться после ввода двухфакторного пароля.")
                        return
                else:
                    print(f"Требуется пароль двухфакторной аутентификации для {phone}, но он не указан. Пропускаем.")
                    return
            except PhoneCodeInvalidError:
                print(f"Неверный код подтверждения для номера {phone}. Пробуем запросить новый код...")
                continue
            except FloodWaitError as e:
                print(f"FloodWaitError: необходимо подождать {e.seconds} секунд. Пропускаем эту сессию.")
                return
            except (OSError, IncompleteReadError) as e:
                print(f"Ошибка соединения при авторизации: {e}")
                print("Пропускаем эту сессию.")
                return
            except Exception as e:
                print(f"Неизвестная ошибка при авторизации: {e}")
                print("Пропускаем эту сессию.")
                return

        else:
            print(f"Не удалось авторизоваться в новой сессии {session_name}.")
            return

        print(f"Авторизация успешна, сохраняем сессию для телефона {phone}")

        proxy_data = api_params.get('proxy', [])
        if isinstance(proxy_data, str):
            proxy_data = proxy_data.split(':')

        # Сохраняем параметры в JSON-файл
        get_json(
            session_phone=phone,
            connection_params=new_connection_params,
            proxy=proxy_data,
            password=twoFA,
            save_proxy=settings.get('save_proxy', False)
        )

        print(f"Новая сессия сохранена: {new_session_path}")

        # Закрываем исходную сессию, если указано в настройках
        if settings.get('close_session'):
            print("Закрываем исходную сессию...")
            await old_client.log_out()
            print("Исходная сессия закрыта.")

    except Exception as e:
        print(f"Ошибка при обработке сессии {session_name}: {e}")
    finally:
        await old_client.disconnect()
        if new_client:
            await new_client.disconnect()