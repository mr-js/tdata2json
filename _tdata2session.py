import telethon
from telethon import errors
from telethon.sync import types
from telethon.tl import functions
from telethon.errors import PhoneNumberBannedError, FloodWaitError, UserDeactivatedBanError, \
    PhoneCodeInvalidError, SessionPasswordNeededError, PasswordHashInvalidError

from _utils import clear, get_json, generate_connection_params, generate_random_app_version, generate_random_windows_name, generate_random_windows_version, get_current_timestamp, random_from_file, load_api_params_from_json, SESSIONS_DIR, TDATAS_DIR, CONVERT_TDATA, CONVERT_SESSION, CONVERT_SESSIONS

import sys
import os
import shutil
import asyncio
import json
import random
import rich

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

# Универсальная функция для конвертации tdata в session
async def TDataToSession(use_proxy: bool, create_new_session: bool, cloud_password=None, settings=None):
    tdataFolder = CONVERT_TDATA
    proxies = []

    if use_proxy:
        try:
            with open('_proxy.txt', 'r') as f:
                lines = f.readlines()
                for line in lines:
                    if line.strip():
                        proxies.append(line.strip().split(':'))
        except FileNotFoundError:
            print("Файл _proxy.txt не найден, работаем без прокси")

    # Генерация параметров для подключения
    connection_params = generate_connection_params()

    for session_dir in os.listdir(tdataFolder):
        await asyncio.sleep(randint(1, 3))

        try:
            tdesk = TDesktop(os.path.join(tdataFolder, session_dir, "tdata"))
            if tdesk.isLoaded():
                # Инициализируем proxy_args с ключом 'proxy'
                proxy_args = {'proxy': None}
                if use_proxy and proxies:
                    proxy_ip, proxy_port, proxy_user, proxy_pass = choice(proxies)
                    proxy_args['proxy'] = ("http", proxy_ip, int(proxy_port), False, proxy_user, proxy_pass)
                    print(f"Подключено с прокси: {proxy_ip}:{proxy_port}")
                else:
                    print("Работа без прокси")

                session_path = os.path.join("./output", f"{session_dir.strip('/')}.session")
                flag = CreateNewSession if create_new_session else UseCurrentSession

                # Определяем, нужно ли закрывать предыдущую сессию
                if create_new_session:
                    if settings and settings.get('close_session', False):
                        close_old_session = True
                    else:
                        close_old_session = False
                else:
                    # Если не создаём новую сессию, игнорируем параметр close_session
                    close_old_session = False

                # Передаём proxy=proxy_args['proxy'] в ToTelethon
                session = await tdesk.ToTelethon(
                    session=session_path, 
                    flag=flag,  
                    api=connection_params,
                    password=cloud_password if cloud_password else None,
                    proxy=proxy_args['proxy']
                )

                await session.connect()

                if not await session.is_user_authorized():
                    print(f"Аккаунт {session_dir} не авторизован. Переход к следующему.")
                    continue

                data = await session.get_me()
                if data is None:
                    raise ValueError("Не удалось получить данные пользователя.")

                phone = data.phone
                print(f"Телефон: {phone}")

                # Сохраняем данные в JSON-файл
                get_json(
                    session_phone=phone, 
                    connection_params=connection_params, 
                    proxy=proxy_args['proxy'], 
                    password=cloud_password, 
                    save_proxy=settings.get('save_proxy', False) if settings else False
                )

                # Закрываем исходную сессию, если необходимо
                if close_old_session:
                    print("Закрываем исходную сессию...")
                    await tdesk.mainAccount._send(functions.auth.LogOutRequest())
                    print("Исходная сессия закрыта.")

                await session.disconnect()

            else:
                print(f"Не удалось загрузить tdata для папки: {session_dir}")

        except TDesktopUnauthorized:
            print(f"Аккаунт {session_dir} не авторизован. Пропускаем и переходим к следующему аккаунту.")
            continue
        except PasswordIncorrect as e:
            print(f"Неверный пароль для {session_dir}. Пропускаю аккаунт.")
            continue
        except telethon.errors.rpcerrorlist.PasswordHashInvalidError as e:
            print(f"Ошибка: {str(e)} для {session_dir}. Пропуск аккаунта.")
            continue
        except errors.rpcerrorlist.AuthTokenAlreadyAcceptedError as e:
            print(f"Токен авторизации уже был использован для {session_dir}. Пропускаю аккаунт.")
            continue
        except TFileNotFound:
            print(f"Файл key_data не найден для папки: {session_dir}")
            continue
        except NoPasswordProvided:
            print(f"Двухфакторная аутентификация активна для {session_dir}, но пароль не предоставлен. Переход к следующему.")
            continue  # Переход к следующему аккаунту
        except SessionPasswordNeededError:
            print(f"Для {session_dir} требуется двухфакторная аутентификация. Переход к следующему.")
            continue  # Переход к следующему аккаунту
        except ValueError as e:
            print(f"Не удалось получить данные пользователя для папки {session_dir} (бан аккаунта?). Ошибка: {e}")
            continue
        except Exception as e:
            print(f"Ошибка с аккаунтом {session_dir}: {e}")
            continue
