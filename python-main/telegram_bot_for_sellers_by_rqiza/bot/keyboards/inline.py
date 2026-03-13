from datetime import datetime, timedelta
from urllib.parse import quote_plus

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder


async def get_delet_user_token(stores: list) -> InlineKeyboardMarkup:
    buttons = []

    # Кнопки магазинов
    for store in stores:
        store_id = store.get('id_seller', '')
        store_name = store.get('trade_mark', f'Магазин {store_id}')
        buttons.append([InlineKeyboardButton(
            text=f"⚡️ {store_name}",
            callback_data=f"delet_store_{store_id}"
        )])

    if not buttons:
        buttons.append([InlineKeyboardButton(
            text="Добавить первый магазин ➕",
            callback_data="add_shop"
        )])
    buttons.extend([
        [InlineKeyboardButton(text="Добавить магазин ➕", callback_data="add_shop"),
         InlineKeyboardButton(text="Перейти в профиль 🦹‍♂️", callback_data="to_profile")],
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_about_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Пример отчета 🔍", callback_data="send_video")],
        [InlineKeyboardButton(text="Перейти в профиль 🦹‍♂️", callback_data="to_profile")],
        [InlineKeyboardButton(text="Поддержка ☂️", url="https://t.me/n6kur0rqlyma")]
    ])


def get_last_report_keyboard(report_data: dict) -> InlineKeyboardMarkup:
    import json
    encoded_data = quote_plus(json.dumps(report_data))
    print(encoded_data)
    web_app_url = f"https://valiullin2024.github.io/?report={encoded_data}"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="📊 Открыть отчет",
            web_app=WebAppInfo(url=web_app_url)
        )],
        [
            InlineKeyboardButton(text="Новый отчет 🌩", callback_data="report_by_date_for_new"),
            InlineKeyboardButton(text="В профиль 🦹‍♂️", callback_data="to_profile")
        ],
        [InlineKeyboardButton(text="Поддержка ☂️", url="https://t.me/n6kur0rqlyma")]
    ])


async def create_date_user_keyboard() -> InlineKeyboardBuilder:
    """Создает клавиатуру для выбора даты"""
    builder = InlineKeyboardBuilder()

    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    today = datetime.now().strftime("%Y-%m-%d")

    builder.button(text=f"◀Вчера", callback_data=f"set_date:{yesterday}")
    builder.button(text=f"📌Сегодня", callback_data=f"set_date:{today}")
    builder.button(text="Перейти в профиль 🦹‍♂️", callback_data="to_profile")
    builder.button(text="Поддержка ☂️️", url="https://t.me/n6kur0rqlyma")

    builder.adjust(1)
    return builder


async def create_date_keyboard() -> InlineKeyboardBuilder:
    """Создает клавиатуру для выбора даты"""
    builder = InlineKeyboardBuilder()

    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    today = datetime.now().strftime("%Y-%m-%d")

    builder.button(text=f"◀ Вчера", callback_data=f"set_date:{yesterday}")
    builder.button(text=f"📌 Сегодня", callback_data=f"set_date:{today}")
    builder.button(text="✏️ Ввести вручную", callback_data="enter_date_manually")
    builder.button(text="Перейти в профиль 🦹‍♂️", callback_data="to_profile")
    builder.button(text="Поддержка ☂️️", url="https://t.me/n6kur0rqlyma")

    builder.adjust(2, 1, 1)
    return builder


async def get_profile_keyboard(user_id: int, stores_data: list) -> InlineKeyboardMarkup:
    """Обновленная версия с новой реализацией"""
    buttons = []
    buttons2 = []
    for store in stores_data:
        store_id = store.get('id_seller', '')
        store_name = store.get('name', f'Магазин {store_id}')
        buttons.append([InlineKeyboardButton(
            text=f" {store_name}",
            callback_data=f"store_{store_id}"
        )])
    buttons2.extend([
        [InlineKeyboardButton(text="Получить последний отчет 🌩", callback_data="report_by_date")],
        [InlineKeyboardButton(text="Добавить магазин ➕", callback_data="add_shop"),
         InlineKeyboardButton(text="Удалить магазин 🛠", callback_data="delet_user_token")],
        [InlineKeyboardButton(text="Сформировать отчет ⛈", callback_data="report_by_date")],
        [InlineKeyboardButton(text="Поддержка ☂️", url="https://t.me/n6kur0rqlyma")]
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons2)


async def get_not_token_profile_keyboard() -> InlineKeyboardMarkup:
    """Обновленная версия с новой реализацией"""
    buttons = []

    buttons.extend([
        [InlineKeyboardButton(text="Добавить магазин ➕", callback_data="add_shop")],
        [InlineKeyboardButton(text="Получить пример отчет 🌩", callback_data="send_video")],
        [InlineKeyboardButton(text="Поддержка ☂️", url="https://t.me/n6kur0rqlyma")]
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def build_report_keyboard(stores: list) -> InlineKeyboardMarkup:
    """Создает клавиатуру с магазинами для отчета"""
    buttons = []
    for store in stores:
        store_id = store.get('id_seller', '')
        store_name = store.get('trade_mark', f'Магазин {store_id}')
        buttons.append([InlineKeyboardButton(
            text=f"⚡️ {store_name}",
            callback_data=f"report_store_{store_id}"  # Префикс report_ для отчетов
        )])
    if not buttons:
        buttons.append([InlineKeyboardButton(
            text="Добавить первый магазин ➕",
            callback_data="add_store"
        )])
    buttons.extend([
        [InlineKeyboardButton(text="Добавить магазин ➕", callback_data="add_shop"),
         InlineKeyboardButton(text="Выбрать дату 🖋", callback_data="report_by_date")],
        [InlineKeyboardButton(text="Перейти в профиль 🦹‍♂️", callback_data="to_profile")]
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_report_fallback_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура на случай ошибки"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Попробовать снова 🔄", callback_data="get_report")],
        [InlineKeyboardButton(text="Добавить магазин ➕", callback_data="add_shop")],
        [InlineKeyboardButton(text="Перейти в профиль 🦹‍♂️", callback_data="to_profile")]
    ])


def get_add_new_shop():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Поддержка ☂️", url="https://t.me/n6kur0rqlyma")],
        [InlineKeyboardButton(text="Перейти в профиль 🦹‍♂️", callback_data="to_profile")]
    ])


def get_connect_wb_api_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Назад ◀️", callback_data="back_one")],
        [InlineKeyboardButton(text="Поддержка ☂️", url="https://t.me/n6kur0rqlyma")],
        [InlineKeyboardButton(text="Перейти в профиль 🦹‍♂️", callback_data="to_profile")]
    ])


def get_token_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Получить отчет 🌩", callback_data="report_by_date"),
         InlineKeyboardButton(text="Перейти в профиль 🦹‍♂️", callback_data="to_profile")],
        [InlineKeyboardButton(text="Поддержка ☂️", url="https://t.me/n6kur0rqlyma")]
    ])


def get_start_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Пример отчета ☂️", callback_data="send_video")],
        [InlineKeyboardButton(text="Подключить магазин Wb 🆓", callback_data="connect_wb_api")]
    ])


def get_report_webapp_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="📊 Открыть отчет",
            web_app=WebAppInfo(url="https://valiullin2024.github.io")
        )
    ]])
