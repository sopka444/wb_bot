import asyncio
import aiohttp
from aiogram import types
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from telegram_bot_for_sellers_by_rqiza.bot.config import rqiza_bot
from telegram_bot_for_sellers_by_rqiza.bot.keyboards.inline import (get_start_keyboard, get_profile_keyboard,
                                                                    get_about_keyboard)
from telegram_bot_for_sellers_by_rqiza.bot.handlers.states import Form
from telegram_bot_for_sellers_by_rqiza.bot.handlers.callbacks import get_or_edit_message

report_message = (
    "       🌨 <b>Мультиаккаунтность</b>:\n"
    "• Подключение неограниченного количества аккаунтов WB\n"
    "• Мгновенное переключение между магазинами\n"
    "• Сводная аналитика по всем подключенных аккаунтах\n"
    "• Единый интерфейс управления\n\n"
    "       🌩 <b>Профессиональная аналитика</b>:\n"
    "• Мгновенные ежедневные отчеты в один клик\n"
    "• Точная фильтрация по артикулам и категориям\n"
    "• Гибкая настройка временных диапазонов\n\n"
    "       🌦 <b>Преимущества для бизнеса:</b>\n"
    "• Все продажи из разных магазинов в едином кабинете\n"
    "• Сравнение эффективности между проектами\n"
    "• Консолидированные отчеты по сети магазинов\n"
    "• Выявление лучших и худших позиций в ассортименте\n\n"
    "🔒 <b>Безопасность:</b>\n"
    "✅ Для работы используется официальный публичный сервер статистики https://openapi.wb.ru.\n"
    "🛠 Пользование ботом абсолютно безопасно."
)


async def about_command(message: Message):
    await rqiza_bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    text = (
        f"Это <b>WB Thunder bOT</b> ⚡️ - мы с тобой знакомы, я помогу быстро получить отчет и "
        f"проанализировать твой профиль на Wildberries.\n"
        f"\n📌 Мои Основные возможности:\n\n\n"
        f"{report_message}"
    )
    await get_or_edit_message(
        message.from_user.id,
        text,
        get_about_keyboard(),
        message=message,
        parse_mode="HTML"
    )


async def start_command(message: Message):
    await rqiza_bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    user_id = message.from_user.id
    user_username = message.from_user.username
    user_first_name = message.from_user.first_name
    user_last_name = message.from_user.last_name
    print(f"ID пользователя: {user_id}")
    print(f"Username: {user_username}")
    print(f"Имя: {user_first_name}")
    print(f"Фамилия: {user_last_name}")

    text = (
        f"Это <b>WB Thunder bOT</b> ⚡️ - я помогу быстро получить отчет и проанализировать твой профиль на Wildberries.\n"
        f"\n📌 Мои Основные возможности:\n\n\n"
        f"{report_message}"
    )

    await rqiza_bot.send_sticker(
        message.from_user.id,
        sticker='CAACAgEAAxkBAAICSGgV8_aoOG4uDb99atWraA11B4IIAAIDCQAC43gEAAGmNc2l6ho94jYE'
    )
    await asyncio.sleep(1.5)

    await get_or_edit_message(
        message.from_user.id,
        text,
        get_start_keyboard(),
        message=message,
        parse_mode="HTML"
    )


async def profile_command(message: types.Message):
    try:
        user_id = message.from_user.id
        username = message.from_user.username or "Без имени"
        await rqiza_bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        # 1. Проверяем статус токена
        token_status = "❌ Токен отсутствует"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://localhost:8000/get_token/{user_id}") as resp:
                    if resp.status == 200:
                        token_status = "✅ Доступ открыт"
        except Exception as e:
            print(f"Ошибка проверки токена: {e}")
            token_status = "⚠️ Ошибка проверки токена"

        # 2. Получаем список магазинов
        stores = []
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://localhost:8000/get_user_stores/{user_id}") as resp:
                    if resp.status == 200:
                        stores = await resp.json()
        except Exception as e:
            print(f"Ошибка загрузки магазинов: {e}")

        # 3. Формируем текст профиля с магазинами
        profile_text = (
            f"🦹‍♂️🌂 Профиль пользователя @{username}\n\n"
            f"🔑 ID: {user_id}\n"
            f"🔐 Статус токена: {token_status}\n\n"
            f"🏪 Доступные магазины:"
        )

        # Добавляем магазины в текст
        if stores:
            for store in stores:
                profile_text += f"\n⚡️- {store.get('name', 'Без названия')}"
        else:
            profile_text += "\nНет доступных магазинов"

        # 4. Получаем клавиатуру
        keyboard = await get_profile_keyboard(user_id, stores)

        # 5. Отправляем сообщение
        await message.answer(
            text=profile_text,
            reply_markup=keyboard  # Если клавиатура не нужна — можно удалить
        )

    except Exception as e:
        print(f"Ошибка в /profile: {e}")
        await message.answer("⚠️ Произошла ошибка при загрузке профиля")


async def token_command(message: Message, state: FSMContext):
    await rqiza_bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    sent_msg = await message.answer("Пожалуйста, введите ваш API токен Wildberries:")
    await state.set_state(Form.waiting_for_token)
    await state.update_data(message_to_delete=sent_msg.message_id)
