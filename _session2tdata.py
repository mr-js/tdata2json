import sys
import os
import telethon
from telethon import errors
from telethon.sync import types
from telethon.tl import functions
from telethon.errors import PhoneNumberBannedError, FloodWaitError, UserDeactivatedBanError, \
    PhoneCodeInvalidError, SessionPasswordNeededError, PasswordHashInvalidError

from _utils import clear, get_json, generate_connection_params, generate_random_app_version, generate_random_windows_name, generate_random_windows_version, get_current_timestamp, random_from_file, load_api_params_from_json, SESSIONS_DIR, TDATAS_DIR, CONVERT_TDATA, CONVERT_SESSION, CONVERT_SESSIONS

import shutil
import asyncio
import json
import random
import rich
from asyncio import IncompleteReadError, TimeoutError

# Импортируем нужные флаги
from opentele.api import APIData
from opentele.api import UseCurrentSession, CreateNewSession
from opentele.td import TDesktop
from opentele.tl import TelegramClient
from opentele.exception import TFileNotFound, NoPasswordProvided, TDesktopUnauthorized, PasswordIncorrect

from random import choice
from time import sleep
from random import randint
import datetime
from faker import Faker
import time


class TData:
    def __init__(self, path: str = CONVERT_SESSION, settings: dict = None) -> None:
        self.path = path
        self.settings = settings
        self.proxies = self.load_proxies()

    def load_proxies(self) -> list:
        """Загрузка прокси либо из файла, либо из аккаунта."""
        if self.settings.get('use_account_proxy', False):
            return self.load_account_proxies()  # Загружаем прокси из аккаунтов
        elif self.settings.get('use_proxy', False):
            return self.load_proxies_from_file()  # Загружаем прокси из _proxy.txt
        else:
            return None  # Прокси не используется

    def get_two_fa_password(self, session_path: str) -> str:
        """Получает пароль двухфакторной аутентификации из JSON-файла, если он существует."""
        json_file = os.path.join(self.path, session_path.split('.')[0] + ".json")
        if os.path.exists(json_file):
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                two_fa_password = data.get('twoFA', None)
                return two_fa_password
        else:
            return None

    def load_proxies_from_file(self) -> list:
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

    def load_account_proxies(self) -> list:
        """Загрузка прокси, привязанных к аккаунтам."""
        proxies = []
        try:
            for filename in os.listdir(self.path):
                if filename.endswith(".json"):
                    with open(os.path.join(self.path, filename), 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if 'proxy' in data:
                            proxy = data['proxy']
                            if proxy:
                                proxies.append(proxy)
        except FileNotFoundError:
            print(f"Не найдено JSON файлов в директории {self.path}")
        return proxies if proxies else None

    def get_proxy_args(self):
        """Получение параметров прокси для подключения."""
        proxy = choice(self.proxies) if self.proxies else None
        if proxy:
            try:
                # Проверяем тип данных proxy
                if isinstance(proxy, list):
                    protocol = proxy[0]
                    proxy_ip = proxy[1]
                    proxy_port = proxy[2]

                    # Инициализируем переменные
                    proxy_user = None
                    proxy_pass = None
                    index = 3

                    # Проверяем наличие дополнительного булевого значения
                    if isinstance(proxy[index], bool):
                        index += 1

                    # Проверяем наличие имени пользователя и пароля
                    if len(proxy) > index:
                        proxy_user = proxy[index]
                    if len(proxy) > index + 1:
                        proxy_pass = proxy[index + 1]

                    proxy_port = int(proxy_port)

                    # Логирование
                    # print(f"Используем прокси из аккаунта: {protocol}://{proxy_ip}:{proxy_port}") # для отладки

                    proxy_args = {
                        "proxy": (
                            protocol.lower(),
                            proxy_ip,
                            proxy_port,
                            True if protocol.lower() == 'mtproxy' else False,
                            proxy_user,
                            proxy_pass
                        )
                    }
                    return proxy_args

                elif isinstance(proxy, str):
                    # Прокси из файла _proxy.txt
                    parts = proxy.strip().split(':')
                    if len(parts) == 4:
                        proxy_ip, proxy_port, proxy_user, proxy_pass = parts
                        proxy_port = int(proxy_port)
                        print(f"Используем прокси из файла: {proxy_ip}:{proxy_port}")
                        proxy_args = {
                            "proxy": (
                                'http',
                                proxy_ip,
                                proxy_port,
                                False,
                                proxy_user,
                                proxy_pass
                            )
                        }
                        return proxy_args
                    else:
                        print(f"Ошибка: Некорректный формат прокси: {proxy}")
                        return None
                else:
                    print(f"Ошибка: Неизвестный формат прокси: {proxy}")
                    return None
            except Exception as e:
                print(f"Ошибка при обработке прокси: {e}")
                return None
        else:
            return None

    async def session_to_tdata(self, session_path: str, settings: dict) -> None:
        await self._session_to_tdata(session_path, settings)

    async def _session_to_tdata(self, session_path: str, settings: dict) -> None:
        proxy_args = self.get_proxy_args()

        # Получаем пароль для 2FA из JSON-файла
        cloud_password = self.get_two_fa_password(session_path)

        # Загружаем параметры из JSON-файла
        try:
            api_params = load_api_params_from_json(session_path, self.path)
        except FileNotFoundError as e:
            print(f"JSON-файл для сессии {session_path} не найден. Пропускаем эту сессию.")
            return  # Пропускаем текущую сессию

        # Извлекаем параметры API
        api_id = api_params.get('api_id')
        api_hash = api_params.get('api_hash')
        device_model = api_params.get('device_model')
        system_version = api_params.get('system_version')
        app_version = api_params.get('app_version')
        lang_code = api_params.get('lang_code')
        system_lang_code = api_params.get('system_lang_code')

        # Создаем клиент с дополнительными параметрами
        client = TelegramClient(
            os.path.join(self.path, session_path),
            api_id=api_id,
            api_hash=api_hash,
            device_model=device_model,
            system_version=system_version,
            app_version=app_version,
            lang_code=lang_code,
            system_lang_code=system_lang_code,
            proxy=proxy_args['proxy'] if proxy_args else None
        )

        try:
            print("Попытка подключения к клиенту Telegram...")
            await client.connect()

            if not await client.is_user_authorized():
                print(f"Аккаунт {session_path} не авторизован")
                await self.handle_2fa(client, cloud_password)
            else:
                print(f"Авторизовались с номером {session_path}")

            # Проверка, создается ли новая сессия
            if settings.get('create_new_session'):
                flag = CreateNewSession
                print("Создаётся новая сессия.")
                close_old_session = settings.get('close_session', False)
            else:
                flag = UseCurrentSession
                print("Используется существующая сессия.")
                close_old_session = False

            connection_params = generate_connection_params()

            # Конвертация в TDesktop
            tdesk = await client.ToTDesktop(
                flag=flag,
                api=connection_params,
                password=cloud_password if cloud_password else None,
                proxy=proxy_args['proxy'] if proxy_args else None
            )

            # Создаем директорию для TData
            tdata_directory = os.path.join("output", session_path.split('.')[0])
            os.makedirs(tdata_directory, exist_ok=True)

            # Сохранение TData
            tdesk.SaveTData(f"./{tdata_directory}/tdata")
            print(f"TData сохранена в директорию: {tdata_directory}")

            # Закрываем исходную сессию, если необходимо
            if close_old_session:
                print("Закрываем исходную сессию...")
                await client(functions.auth.LogOutRequest())
                print("Исходная сессия закрыта.")

            await client.disconnect()

        except PasswordHashInvalidError as e:
            print(f"Неверный пароль для 2FA для аккаунта {session_path}. Пропускаем аккаунт. Ошибка: {e}")
            return  # Переходим к следующему аккаунту
        except SessionPasswordNeededError:
            print("Необходим ввод пароля для двухфакторной аутентификации.")
            await self.handle_2fa(client, cloud_password)
        except (OSError, IncompleteReadError) as e:
            print(f"Ошибка соединения при обработке сессии {session_path}: {e}")
            print("Пропускаем эту сессию.")
            return
        except FloodWaitError as e:
            print(f"Получен FloodWaitError на {e.seconds} секунд. Пропускаем эту сессию.")
            return
        except Exception as e:
            print(f"Не удалось подключиться или выполнить конвертацию для аккаунта {session_path}: {e}")
            print("Пропускаем эту сессию.")
        finally:
            await client.disconnect()

    async def handle_2fa(self, client, saved_password=None):
        """Обработка двухфакторной аутентификации."""
        if saved_password:
            try:
                # print(f"Используем пароль для 2FA: {saved_password}") # вывод отладки
                await client.sign_in(password=saved_password)
                print("Двухфакторная аутентификация успешно пройдена.")
            except PasswordHashInvalidError:
                print("Неверный сохранённый пароль. Пожалуйста, введите правильный пароль.")
                await self.handle_2fa(client, None)
        else:
            password = input("Введите пароль для двухфакторной аутентификации: ")
            try:
                await client.sign_in(password=password)
                print("Двухфакторная аутентификация успешно пройдена.")
            except PasswordHashInvalidError:
                print("Неверный пароль, повторите ввод.")
                await self.handle_2fa(client, None)

    def pack_to_zip(self, tdata_path: str) -> None:
        """Упаковка TData в архив."""
        shutil.make_archive(f"{tdata_path}", "zip", tdata_path)
        print(f"Упакованная папка {tdata_path} в zip-архив.")

async def SessionToTData(settings: dict):
    tdata = TData(settings=settings)

    for session in os.listdir(CONVERT_SESSION):
        if "." in session and session.split(".")[1] == "session":
            await tdata.session_to_tdata(session_path=session, settings=settings)

    tdata.pack_to_zip(tdata_path=TDATAS_DIR)
