import sys
import os
import telethon
from telethon import errors
from telethon.sync import types
from telethon.tl import functions
from telethon.errors import PhoneNumberBannedError, FloodWaitError, UserDeactivatedBanError, \
    PhoneCodeInvalidError, SessionPasswordNeededError, PasswordHashInvalidError

from _utils import clear, get_json, generate_connection_params, generate_random_app_version, generate_random_windows_name, generate_random_windows_version, get_current_timestamp, random_from_file, load_api_params_from_json, SESSIONS_DIR, TDATAS_DIR, CONVERT_TDATA, CONVERT_SESSION, CONVERT_SESSIONS

from _session2tdata import SessionToTData, TData
from _tdata2session import TDataToSession
from _session2session import SessionToSession, convert_session_session

import asyncio
import json
import random
import rich

import opentele

# Импортируем нужные флаги
from opentele.api import APIData
from opentele.api import UseCurrentSession, CreateNewSession
from opentele.td import TDesktop
from opentele.exception import TFileNotFound, NoPasswordProvided, TDesktopUnauthorized, PasswordIncorrect

from random import choice, randint
import time

# Чтение настроек из файла _settings.txt
def read_settings():
    settings = {
        'create_new_session': False,
        'use_proxy': False,
        'cloud_password': None,
        'save_proxy': False,
        'use_account_proxy': False,
        'connection_attempts': 5, # Новый параметр для попыток подключения
        'close_session':False
    }

    if os.path.exists('_settings.txt'):
        with open('_settings.txt', 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines:
                key, value = map(str.strip, line.split(':'))
                if key == 'Создавать новую сессию':
                    settings['create_new_session'] = value.lower() == 'да'
                elif key == 'Использовать прокси':
                    settings['use_proxy'] = value.lower() == 'да'
                elif key == 'Стандартный облачный пароль':
                    settings['cloud_password'] = None if value.lower() == 'нет' else value
                elif key == 'Записывать прокси в файл json':
                    settings['save_proxy'] = value.lower() == 'да'
                elif key == 'Брать прокси из аккаунта':
                    settings['use_account_proxy'] = value.lower() == 'да'
                elif key == 'Количество попыток подключения':
                    settings['connection_attempts'] = int(value)
                elif key == 'Закрывать предыдущую сессию':
                    settings['close_session'] = value.lower() == 'да'

    return settings

# Меню 
async def main():
    settings = read_settings()  # Чтение настроек
    print(f"Настройки загружены: {settings}") # вывод отладки

    while True:
        rich.print(
            "[bold]Меню[/bold]\n\n"
            "[bright_cyan]| 1 |[/bright_cyan] [bright_red italic]C session в tdata [/bright_red italic]\n"
            "[bright_cyan]| 2 |[/bright_cyan] [bright_red italic]C tdata в session [/bright_red italic]\n"
            "[bright_cyan]| 3 |[/bright_cyan] [bright_red italic]C session в session [/bright_red italic]\n"			
            "[bright_cyan]| 4 |[/bright_cyan] [bright_red italic]Очистить папки [/bright_red italic]\n"
            "[bright_cyan]| 5 |[/bright_cyan] [bright_red italic]Выход [/bright_red italic]\n"
            "[cyan bold]Select: [/cyan bold] ",
            end="",
        )

        choiced = input()

        use_proxy = settings['use_proxy']

        if choiced == "1":
            print("Конвертация из session в tdata...")
            await SessionToTData(settings=settings)
        elif choiced == "2":
            print("Конвертация из tdata в session...")
            await TDataToSession(
                use_proxy=use_proxy, 
                create_new_session=settings['create_new_session'], 
                cloud_password=settings['cloud_password'], 
                settings=settings  # Передаем настройки
            )
        elif choiced == "3":
            print("Конвертация из session в session...")
            await SessionToSession(settings=settings)
        elif choiced == "4":
            clear()
            print("[bold]Очищено[/bold]")
        elif choiced == "5":
            print("Выход.")
            break


if __name__ == "__main__":
    asyncio.run(main())
    print("Успешно.")