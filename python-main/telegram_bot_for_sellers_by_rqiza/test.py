import asyncio

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram import F
import os
from dotenv import load_dotenv
from datetime import date, timedelta, datetime
from telegram_bot_for_sellers_by_rqiza.api.wb_api import get_promotion_statistics
from telegram_bot_for_sellers_by_rqiza.api.wb_api import get_sales_report
from telegram_bot_for_sellers_by_rqiza.api.wb_api import get_orders_report
from telegram_bot_for_sellers_by_rqiza.api.wb_api import get_paid_storage_cost
from telegram_bot_for_sellers_by_rqiza.api.wb_api import get_sales_funnel_report
from telegram_bot_for_sellers_by_rqiza.api.wb_api import check_all_services

# todo исправить ошибки при формирование отчет
# todo добавить возможность возврашщаться (кнопкой) на любом этапе
# todo разделить на модули добавление артикула и выбор даты
# добавить инлайн кнопки, аватарку и описание
# добавить обращение к пользователю по имени и изменить стиль общения
# упростить название кнопок для удобства пользователя
# отредактировать кнопки добавить стикеры гифки ссылки шрифт


# 1 в случае двух ответов по продажам за день (другая страна) программа видит только один из них пример 02.10
# Инициализация бота и диспетчера
rqiza_bot = Bot(token='7537308360:AAHb-6lePBkNleWjEfnVZl3oJmXj-1kWRSc')
dp = Dispatcher()
load_dotenv()

wb_api_token_statistics = os.getenv('wb_api_token_statistics')
wb_api_token_analytics = os.getenv('wb_api_token_analytics')
wb_api_token_promotion = os.getenv('wb_api_token_promotion')

headers_analytics = {'Authorization': wb_api_token_analytics}
headers_statistics = {'Authorization': wb_api_token_statistics}
headers_promotion = {'Authorization': wb_api_token_promotion}

TODAY = date.today()
YESTERDAY = TODAY - timedelta(days=1)
last_bot_message = None
previous_message_data = {}


class Form(StatesGroup):
    waiting_for_date = State()
    waiting_for_token = State()


@dp.callback_query(lambda c: c.data == "to_profile")
async def get_report(callback_query: types.CallbackQuery):
    global last_bot_message
    await callback_query.answer()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="магазин1",callback_data="qwe1")],
        [InlineKeyboardButton(text="магазин2",callback_data="qwe2")],
        [InlineKeyboardButton(text="Получить отчет 🌩",callback_data="get_report")],
        [InlineKeyboardButton(text="Добавить магазин ➕",callback_data="add_store")],
        [InlineKeyboardButton(text="Поддержка ☂️", callback_data="help_user")]
    ])
    text = (
        f"🦹‍♂️🌂  Профиль пользователя {callback_query.from_user.username}\n\n"
        f"ID {callback_query.from_user.id}\n\n"
        f"Доступные магазины:"
    )
    if last_bot_message:
        try:
            await callback_query.bot.edit_message_text(
                text,
                chat_id=callback_query.from_user.id,
                message_id=last_bot_message.message_id,
                reply_markup=keyboard
            )
        except:
            last_bot_message = await callback_query.message.answer(text, reply_markup=keyboard)
    else:
        last_bot_message = await callback_query.message.answer(text, reply_markup=keyboard)


@dp.callback_query(lambda c: c.data == "get_report")
async def get_report(callback_query: types.CallbackQuery):
    global last_bot_message
    await callback_query.answer()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1",callback_data="qwe1")],
        [InlineKeyboardButton(text="2",callback_data="qwe2")],
        [InlineKeyboardButton(text="Добавить магазин ➕",callback_data="add_store")],
        [InlineKeyboardButton(text="Перейти в профиль 📍", callback_data="to_profile")]
    ])
    text = (
        "🛠  Выбери магазин по которому хочешь получить отчет:\n\n"
    )
    if last_bot_message:
        try:
            await callback_query.bot.edit_message_text(
                text,
                chat_id=callback_query.from_user.id,
                message_id=last_bot_message.message_id,
                reply_markup=keyboard
            )
        except:
            last_bot_message = await callback_query.message.answer(text, reply_markup=keyboard)
    else:
        last_bot_message = await callback_query.message.answer(text, reply_markup=keyboard)
@dp.callback_query(lambda c: c.data == "connect_wb_api")
async def connect_wb_api(callback_query: types.CallbackQuery):
    global last_bot_message
    await callback_query.answer()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Назад ◀️", callback_data="back_one")],
        [InlineKeyboardButton(text="Поддержка ☂️", callback_data="help_user")]
    ])
    text = (
        "🛠 ПОДКЛЮЧЕНИЕ\n\n"
        "1️⃣ Зайдите в Личный кабинет WB → Настройки → Доступ к API (https://seller.wildberries.ru/supplier-settings/access-to-api)\n\n"
        "2️⃣ Нажмите кнопку [+ Создать новый токен] и введите любое имя токена\n\n"
        "3️⃣ Нажмите галочку Только на чтение и выберите тип Статистика,Продвижение,Аналитика\n\n"
        "4️⃣ Нажмите [Создать токен], а затем скопируйте его\n\n"
        "👉🏻 Нажмите на команду /token (или напишите в ручную)\n"
        "🛠 Вставьте скопированный токен и отправьте сообщение."
    )

    if last_bot_message:
        try:
            await callback_query.bot.edit_message_text(
                text,
                chat_id=callback_query.from_user.id,
                message_id=last_bot_message.message_id,
                reply_markup=keyboard,
                disable_web_page_preview=True
            )
        except:
            last_bot_message = await callback_query.message.answer(text, reply_markup=keyboard,
                                                                   disable_web_page_preview=True)
    else:
        last_bot_message = await callback_query.message.answer(text, reply_markup=keyboard,
                                                               disable_web_page_preview=True)


@dp.callback_query(lambda c: c.data == "back_one")
async def back_one(callback_query: types.CallbackQuery):
    global last_bot_message
    await callback_query.answer()

    # Основное сообщение бота (как в команде /start)
    text = (
        f"Это <b>WB Thunder bOT</b> ⚡️ - я помогу быстро получить отчет и проанализировать твой профиль на Wildberries.\n"
        f"\n📌 Мои Основные возможности:\n\n\n"
        "       🌨 <b>Мультиаккаунтность</b>:\n"
        "• Подключение неограниченного количества аккаунтов WB\n"
        "• Мгновенное переключение между магазинами\n"
        "• Сводная аналитика по всем подключенным аккаунтам\n"
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

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Пример отчета ☂️", callback_data="print_data")],
        [InlineKeyboardButton(text="Подключить магазин Wb 🆓", callback_data="connect_wb_api")]
    ])

    try:
        await callback_query.bot.edit_message_text(
            text,
            chat_id=callback_query.from_user.id,
            message_id=last_bot_message.message_id,
            reply_markup=keyboard,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
    except Exception as e:
        print(f"Ошибка при редактировании сообщения: {e}")


async def main_requests(BEGIN_USER_DATE, BEGIN_USER_DATE2, END_USER_NAME, END_USER_NAME2):
    """
    Выполняет все запросы и возвращает результаты.
    """
    sales_funnel, orders_report, sales_report, paid_storage_report, promotion_report = await asyncio.gather(
        get_sales_funnel_report(BEGIN_USER_DATE, END_USER_NAME, headers_analytics),
        get_orders_report(BEGIN_USER_DATE, headers_statistics),
        get_sales_report(BEGIN_USER_DATE, headers_statistics),
        get_paid_storage_cost(BEGIN_USER_DATE, END_USER_NAME, headers_analytics),
        get_promotion_statistics(headers_promotion, BEGIN_USER_DATE2)
    )

    return {
        'orders_report': orders_report,
        'sales_funnel': sales_funnel,
        'sales_report': sales_report,
        'paid_storage_report': paid_storage_report,
        'promotion_report': promotion_report
    }


@dp.message(Command("start"))
async def start(message: Message):
    global last_bot_message, previous_message_data
    await rqiza_bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)

    user_id = message.from_user.id
    user_username = message.from_user.username
    user_first_name = message.from_user.first_name
    user_last_name = message.from_user.last_name
    print(f"ID пользователя: {user_id}")
    print(f"Username: {user_username}")
    print(f"Имя: {user_first_name}")
    print(f"Фамилия: {user_last_name}")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Пример отчета ☂️", callback_data="print_data")],
        [InlineKeyboardButton(text="Подключить магазин Wb 🆓", callback_data="connect_wb_api")]
    ])

    report_message = (
        "       🌨 <b>Мультиаккаунтность</b>:\n"
        "• Подключение неограниченного количества аккаунтов WB\n"
        "• Мгновенное переключение между магазинами\n"
        "• Сводная аналитика по всем подключенным аккаунтам\n"
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

    if last_bot_message:
        previous_message_data[message.from_user.id] = {
            'text': last_bot_message.text,
            'reply_markup': last_bot_message.reply_markup
        }
        try:
            await message.bot.edit_message_text(
                text,
                chat_id=message.chat.id,
                message_id=last_bot_message.message_id,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        except:
            last_bot_message = await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        previous_message_data[message.from_user.id] = {
            'text': text,
            'reply_markup': keyboard
        }
        last_bot_message = await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@dp.message(Command("token"))
async def token_connect(message: Message, state: FSMContext):
    # Удаляем сообщение с командой /token
    await rqiza_bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    # Отправляем запрос на ввод токена и удаляем его после ответа
    sent_msg = await message.answer("Пожалуйста, введите ваш API токен Wildberries:")
    await state.set_state(Form.waiting_for_token)
    # Сохраняем ID сообщения для последующего удаления
    await state.update_data(message_to_delete=sent_msg.message_id)


@dp.message(Form.waiting_for_token)
async def process_token_input(message: Message, state: FSMContext):
    global last_bot_message, wb_api_token_statistics, wb_api_token_analytics, wb_api_token_promotion
    global headers_statistics, headers_analytics, headers_promotion
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Получить отчет 🌩", callback_data="get_report")],
        [InlineKeyboardButton(text="Поддержка ☂️", callback_data="help_user")]
    ])
    try:
        # Удаляем сообщение с токеном пользователя
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        except:
            pass

        # Удаляем предыдущее сообщение бота, если есть
        state_data = await state.get_data()
        if 'message_to_delete' in state_data:
            try:
                await message.bot.delete_message(chat_id=message.chat.id, message_id=state_data['message_to_delete'])
            except:
                pass

        user_token = message.text.strip()
        if not user_token:
            raise ValueError("Пустой токен")

        headers = {'Authorization': user_token}
        check_results = await check_all_services(headers)

        services_status = {}
        user_info = {}
        error_services = []

        for service, result in check_results.items():
            if service == 'user_connect':
                if isinstance(result, dict):
                    user_info = result
                continue

            if isinstance(result, dict) and result.get('Status') == 'OK':
                services_status[service] = True
            else:
                services_status[service] = False
                error_services.append(service)

        response_parts = []
        if user_info:
            response_parts.append(
                f"👤 Владелец: {user_info.get('name', 'Не указано')}\n"
                f"🏷 Марка: {user_info.get('tradeMark', 'Не указано')}\n"
            )
        else:
            response_parts.append("⚠ Не удалось получить информацию о пользователе\n")

        response_parts.append("\nСтатус сервисов:")
        for service, status in services_status.items():
            response_parts.append(f"- {service.capitalize()}: {'✅ Доступен' if status else '❌ Недоступен'}")

        if services_status.get('statistics'):
            wb_api_token_statistics = user_token
            headers_statistics = headers.copy()
        if services_status.get('analytics'):
            wb_api_token_analytics = user_token
            headers_analytics = headers.copy()
        if services_status.get('promotions'):
            wb_api_token_promotion = user_token
            headers_promotion = headers.copy()

        if error_services:
            response_parts.insert(0, "⚠ Некоторые сервисы недоступны:\n")
        else:
            response_parts.insert(0, "✅ Все сервисы доступны\n")

        response_message = "\n".join(response_parts)

    except Exception as e:
        response_message = f"❌ Ошибка при обработке токена: {str(e)}"
        await state.clear()

    try:
        if last_bot_message:
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=last_bot_message.message_id,
                text=response_message,
                reply_markup=keyboard
            )
        else:
            last_bot_message = await message.answer(response_message)
    except:
        last_bot_message = await message.answer(response_message)

    await state.clear()


@dp.message(F.text.lower() == "вывести общее количество продаж")
async def show_total_sales(message: types.Message):
    await chouse_date(message)


async def chouse_date(message: types.Message):
    kb = [
        [types.KeyboardButton(text=f"Выбрать ближайщую дату - {YESTERDAY}")],
        [types.KeyboardButton(text="Выбрать другую дату")]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer("Выберите дату для получения отчета🗓", reply_markup=keyboard)


@dp.message(F.text.lower() == f"выбрать ближайщую дату - {YESTERDAY}")
# todo кароче если наступает след день например с 3 мая на  4 мая то есть 04052025 0000 то прогу будет крашить так как второй
# пириод 04052025 23:59 который еще не наступил
# надо добавитьь обработку с проверкой и чтобы ставилось максимально возможное время
async def choose_yesterday(message: types.Message):
    await message.answer(f"📊Начало формирования отчета...")
    YESTERDAY_STR = str(YESTERDAY)
    BEGIN_USER_DATE = f'{YESTERDAY_STR} 00:00:00'
    BEGIN_USER_DATE2 = YESTERDAY_STR
    END_USER_NAME = f'{YESTERDAY_STR} 23:59:59'
    END_USER_NAME2 = YESTERDAY_STR

    await otchet_message(message, BEGIN_USER_DATE, BEGIN_USER_DATE2, END_USER_NAME, END_USER_NAME2)


@dp.message(F.text.lower() == "выбрать другую дату")
async def choose_another_date(message: types.Message, state: FSMContext):
    await message.answer("Введите дату в формате ГГГГ-ММ-ДД:")
    await state.set_state(Form.waiting_for_date)  # Устанавливаем состояние ожидания даты


@dp.message(Form.waiting_for_date)
async def process_date_input(message: types.Message, state: FSMContext):
    user_input = message.text.strip()
    try:
        # Пытаемся преобразовать введенный текст в объект date
        input_date = datetime.strptime(user_input, "%Y-%m-%d").date()
        await message.answer(f"📊Начало формирования отчета...")
        input_date_srt = str(input_date)
        await state.clear()  # Сбрасываем состояние после успешного ввода
        BEGIN_USER_DATE = f'{input_date_srt} 00:00:00'
        BEGIN_USER_DATE2 = input_date_srt
        END_USER_NAME = f'{input_date_srt} 23:59:59'
        END_USER_NAME2 = input_date_srt

        await otchet_message(message, BEGIN_USER_DATE, BEGIN_USER_DATE2, END_USER_NAME, END_USER_NAME2)
    except ValueError:
        await message.answer("Неверный формат даты. Пожалуйста, введите дату в формате ГГГГ-ММ-ДД.")


@dp.message(Command("otchet"))
async def otchet_message(message: Message, BEGIN_USER_DATE, BEGIN_USER_DATE2, END_USER_NAME, END_USER_NAME2):
    print("Начало формирования отчета...")
    reports = await main_requests(BEGIN_USER_DATE, BEGIN_USER_DATE2, END_USER_NAME, END_USER_NAME2)
    print("Отчет сформирован.")

    report_message = (
        f"Отчет за {BEGIN_USER_DATE2}:\n\n"
        f"🛍 Количество заказов: {reports['orders_report']['orders_amount']}\n"
        f"        Сумма заказов: {reports['orders_report']['orders_cost']}\n\n"
        f"💸 Общая сумма продаж: {reports['sales_report']['total_finished_price']}\n"
        f"        Возвратов: {reports['sales_report']['sale_count_r']}\n"
        f"        Выкупов: {reports['sales_report']['sale_count_s']}\n\n"
        f"        Итого продаж за день: {reports['sales_report']['sale_count_diff']}\n"
        f"📦 Стоимость платного хранения: {reports['paid_storage_report']}\n\n"
        f"📈 Статистика рекламных кампаний:\n"
        f"        Сумма затрат на рекламу: {reports['promotion_report']['sum']}\n"
        f"        Просмотры по рекламной компании: {reports['promotion_report']['views']} 👁\n\n"
        f"🔎 Перешли в карточку: {reports['sales_funnel']['total_open_card_count']}\n"
        f"🗑 Добавили в корзину: {reports['sales_funnel']['total_add_to_cart_count']}\n\n"
        f"Отчет сформирован ✅"
    )
    await message.answer(report_message)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="📊 Открыть отчет",
            web_app=WebAppInfo(url="https://valiullin2024.github.io")
        )
    ]])

    await message.answer(
        "Отчет готов! Нажмите кнопку ниже, чтобы просмотреть:",
        reply_markup=keyboard
    )


if __name__ == "__main__":
    dp.run_polling(rqiza_bot)
