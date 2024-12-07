import sys
import os
import shutil
import random
import datetime
import json

from opentele.api import APIData

# Директории (перенесите их сюда или передавайте как параметры)
SESSIONS_DIR = "./output/"
TDATAS_DIR = "./output/"
CONVERT_TDATA = "./input/"
CONVERT_SESSION = "./input/"
CONVERT_SESSIONS = "./input/"  # сессии для конвертации в сессии

# Очистка папок 
def clear():
    for dir in [TDATAS_DIR, SESSIONS_DIR, CONVERT_SESSION, CONVERT_TDATA]:
        try:
            shutil.rmtree(dir)
        except OSError:
            for file in os.listdir(dir):
                os.remove(file)

    for dir in [TDATAS_DIR, SESSIONS_DIR, CONVERT_SESSION, CONVERT_TDATA]:
        os.mkdir(dir)

def get_two_fa_password(session_path: str) -> str:
    """Возвращает пароль для двухфакторной аутентификации из JSON-файла."""
    json_file = os.path.join(os.path.dirname(session_path), os.path.splitext(session_path)[0] + ".json")
    if os.path.exists(json_file):
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if 'twoFA' in data:
                return data['twoFA']  # Возвращаем пароль 2FA, если он есть в файле
    return None

def get_json(session_phone: str, connection_params, proxy=None, password=None, save_proxy=True):
    # Если не нужно записывать прокси, установим proxy_info в пустой список
    if proxy and save_proxy:
        # Проверяем тип proxy
        if isinstance(proxy, dict) and 'proxy' in proxy:
            # Если proxy — словарь с ключом 'proxy', извлекаем список
            proxy_info = list(proxy['proxy'])
        elif isinstance(proxy, list):
            # Если proxy — список, используем его напрямую
            proxy_info = proxy
        elif isinstance(proxy, tuple):
            # Если proxy — кортеж, преобразуем его в список
            proxy_info = list(proxy)
        else:
            # Если формат proxy неизвестен, устанавливаем пустой список и выводим предупреждение
            proxy_info = []
            print(f"Предупреждение: Некорректный формат proxy: {proxy}")
    else:
        proxy_info = []  # Если прокси не нужно записывать или отсутствует

    jsonic = {
        'session_file': session_phone,
        'phone': session_phone,
        'register_time': get_current_timestamp(),
        'app_id': connection_params.api_id,
        'app_hash': connection_params.api_hash,
        'sdk': connection_params.system_version,
        'app_version': connection_params.app_version,
        'device': connection_params.device_model,
        'last_check_time': get_current_timestamp(),
        'first_name': "VanyaMarket",
        'last_name': None,
        'username': None,
        'sex': 0,
        'lang_pack': connection_params.lang_code,
        'system_lang_pack': connection_params.system_lang_code,
        'ipv6': False,
        'twoFA': password if password else None,
        'proxy': proxy_info
    }

    # Сохраняем JSON в файл
    with open(SESSIONS_DIR + session_phone + ".json", "w+", encoding='utf-8') as f:
        json.dump(jsonic, f, ensure_ascii=False)

    print(f"JSON-файл для сессии {session_phone} успешно создан.")



# Генерация параметров для подключения
def generate_connection_params():
    resources_path = os.path.join(os.getcwd())

    # Генерация случайных параметров
    api_id, api_hash = random_from_file(os.path.join(resources_path, '_app_pairs.txt'))
    api_id = int(api_id)

    app_version = generate_random_app_version()
    device_model = generate_random_windows_name()
    system_version = generate_random_windows_version()
    lang_code = random_from_file(os.path.join(resources_path, '_lang_codes.txt'))[0]
    system_lang_code = random_from_file(os.path.join(resources_path, '_system_lang_codes.txt'))[0]

    # Возвращаем объект APIData с параметрами
    return APIData(
        api_id=api_id,
        api_hash=api_hash,
        device_model=device_model,
        system_version=system_version,
        app_version=app_version,
        lang_code=lang_code,
        system_lang_code=system_lang_code,
        lang_pack="tdesktop"
    )

# Генерация случайных версий и параметров
def generate_random_app_version():
    return f'{random.randint(5, 5)}.{random.randint(1, 5)}.{random.randint(1, 9)} x64'

def generate_random_windows_name(chars_num: int = 7):
    name_chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    code = ''.join(random.choice(name_chars) for _ in range(chars_num))
    return f'DESKTOP-{code}'

def generate_random_windows_version():
    win_list = ['Windows 8.1', 'Windows 10', 'Windows 11']
    return random.choice(win_list)

def get_current_timestamp():
    dt = datetime.datetime.now(datetime.timezone.utc)
    utc_time = dt.replace(tzinfo=datetime.timezone.utc)
    utc_timestamp = utc_time.timestamp()
    return utc_timestamp

# Получаем пару APP_ID и APP_HASH из файла
def random_from_file(filename, delimiter=':'):
    with open(filename, 'r') as file:
        lines = file.readlines()
        line = random.choice(lines).strip()  # выбираем случайную строку
        return line.split(delimiter)

def load_api_params_from_json(session_path: str, base_path: str) -> dict:
    """Загружает параметры API и другие настройки клиента из JSON-файла."""
    json_file = os.path.join(base_path, session_path.split('.')[0] + ".json")
    
    if os.path.exists(json_file):
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            api_id = data.get('app_id')
            api_hash = data.get('app_hash')
            device_model = data.get('device')
            system_version = data.get('sdk')
            app_version = data.get('app_version')
            lang_code = data.get('lang_pack')
            system_lang_code = data.get('system_lang_pack')
            twoFA = data.get('twoFA')
            proxy = data.get('proxy')
            
            if not api_id or not api_hash:
                raise ValueError("API ID или API Hash отсутствуют в JSON файле.")
            
            return {
                'api_id': api_id,
                'api_hash': api_hash,
                'device_model': device_model,
                'system_version': system_version,
                'app_version': app_version,
                'lang_code': lang_code,
                'system_lang_code': system_lang_code,
                'twoFA': twoFA,
                'proxy': proxy
            }
    else:
        raise FileNotFoundError(f"JSON файл {json_file} не найден.")