from aiogram import types
from aiogram.client.session import aiohttp
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta
from telegram_bot_for_sellers_by_rqiza.bot.config import user_messages
from telegram_bot_for_sellers_by_rqiza.bot.keyboards.inline import (
    get_profile_keyboard,
    build_report_keyboard,
    get_report_fallback_keyboard,
    get_connect_wb_api_keyboard,
    get_start_keyboard, create_date_keyboard, create_date_user_keyboard, get_add_new_shop,
    get_not_token_profile_keyboard, get_delet_user_token, get_token_keyboard
)
from telegram_bot_for_sellers_by_rqiza.bot.services.report_service import generate_report


async def delet_user_token_callback(callback_query):
    user_id = callback_query.from_user.id
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://localhost:8000/get_user_stores/{user_id}") as resp:
                if resp.status == 200:
                    stores = await resp.json()
                    keyboard = await get_delet_user_token(stores)

                    await callback_query.message.edit_text(
                        "🏪 <b>Выберите магазин который хотели бы удалить</b>",
                        reply_markup=keyboard,
                        parse_mode="HTML"
                    )

    except Exception as e:
        print(f"Ошибка при получении магазинов: {e}")
        await callback_query.answer("Ошибка при загрузке магазинов", show_alert=True)


async def delet_user_token_button_callback(callback: types.CallbackQuery):
    data_parts = callback.data.split('_')
    user_id = callback.from_user.id
    store_id = data_parts[2]
    try:
        async with aiohttp.ClientSession() as session:
            async with session.delete(f"http://localhost:8000/delete_seller_token/{user_id}/{store_id}") as resp:
                if resp.status == 200:
                    await callback.message.edit_text(
                        "🏪 <b>Магазин был удален</b>",
                        reply_markup=get_token_keyboard(),
                        parse_mode="HTML"
                    )

    except Exception as e:
        print(f"Ошибка при получении магазинов: {e}")
        await callback.answer("Ошибка при загрузке магазинов", show_alert=True)


async def handle_store_callback(callback: types.CallbackQuery):
    data_parts = callback.data.split('_')
    if len(data_parts) != 2 or data_parts[0] != 'store':
        await callback.answer("Ошибка обработки запроса")
        return

    store_id = data_parts[1]

    await callback.answer(f"Выбран магазин ID: {store_id}")
    await callback.message.answer(f"Информация о магазине {store_id}...")


async def handle_store_selection(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик выбора магазина для отчета"""
    try:
        state_data = await state.get_data()
        selected_date = state_data.get('selected_date')

        if not selected_date:
            await callback_query.answer("Дата не выбрана", show_alert=True)
            return

        store_id = callback_query.data.split('_')[-1]
        user_id = callback_query.from_user.id
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://localhost:8000/get_seller_token/{user_id}/{store_id}") as resp:
                    if resp.status == 200:
                        token_data = await resp.json()
                        token = token_data.get('token')

                        if not token:
                            await callback_query.answer("Токен магазина не найден", show_alert=True)
                            return

                        begin_date = f"{selected_date} 00:00:00"
                        end_date = f"{selected_date} 23:59:59"

                        await callback_query.message.edit_text(
                            f"📊 Формирую отчет за {selected_date}",
                            parse_mode="HTML"
                        )

                        await generate_report(
                            callback_query.message,
                            begin_date,
                            selected_date,
                            end_date,
                            selected_date,
                            store_id,
                            token
                        )

                        await state.clear()
                    else:
                        error = await resp.json()
                        await callback_query.answer(
                            f"Ошибка: {error.get('detail', 'Не удалось получить токен магазина или у вас нет доступа')}",
                            show_alert=True
                        )
        except Exception as e:
            print(f"Ошибка при получении токена магазина: {e}")
            await callback_query.answer("Ошибка при формировании отчета", show_alert=True)

    except Exception as e:
        print(f"Error in handle_store_selection: {e}")
        await callback_query.answer("Ошибка при обработке выбора магазина", show_alert=True)


async def get_or_edit_message(user_id: int, text: str, reply_markup, message: types.Message = None,
                              callback_query: types.CallbackQuery = None, **kwargs):
    """Универсальная функция для получения или редактирования сообщения"""
    bot = callback_query.bot if callback_query else message.bot
    chat_id = user_id

    if user_id in user_messages:
        try:
            await bot.edit_message_text(
                text,
                chat_id=chat_id,
                message_id=user_messages[user_id].message_id,
                reply_markup=reply_markup,
                **kwargs
            )
            return user_messages[user_id]
        except Exception as e:
            print(f"Ошибка при редактировании сообщения: {e}")
            new_message = await (callback_query.message.answer if callback_query else message.answer)(
                text, reply_markup=reply_markup, **kwargs
            )
            user_messages[user_id] = new_message
            return new_message
    else:
        new_message = await (callback_query.message.answer if callback_query else message.answer)(
            text, reply_markup=reply_markup, **kwargs
        )
        user_messages[user_id] = new_message
        return new_message


async def send_video_callback(callback: types.CallbackQuery):
    try:
        await callback.bot.send_video(
            chat_id=callback.from_user.id,
            video="BAACAgIAAxkBAAICEGhLHYuN0atR9CFVjAwVUCLxAgABUAACjnwAAq5hWUrc_gNS-pWX4TYE"
        )
        await callback.answer()
    except Exception as e:
        print(f"Ошибка при отправке видео: {e}")
        await callback.answer("Не удалось отправить видео", show_alert=True)


async def handle_video(message: types.Message):
    file_id = message.video.file_id
    print("File ID видео:", file_id)
    await message.reply(f"File ID: {file_id}")


async def to_profile_callback(callback_query: types.CallbackQuery):
    try:
        await callback_query.answer()

        user_id = callback_query.from_user.id
        username = callback_query.from_user.username or "Без имени"
        token_status = "❌ Токен отсутствует"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://localhost:8000/get_token/{user_id}") as resp:
                    if resp.status == 200:
                        token_status = "✅ Доступ открыт"
        except Exception as e:
            print(f"Token check error: {e}")
            token_status = "⚠️ Ошибка проверки токена"
        stores = []
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://localhost:8000/get_user_stores/{user_id}") as resp:
                    if resp.status == 200:
                        stores = await resp.json()
        except Exception as e:
            print(f"Stores fetch error: {e}")
        profile_text = (
            f"🦹‍♂️🌂 Профиль пользователя @{username}\n\n"
            f"🔑 ID: {user_id}\n"
            f"🔐 Статус токена: {token_status}\n\n"
            f"🏪 Доступные магазины:"
        )
        keyboard = await get_not_token_profile_keyboard()
        if stores:
            for store in stores:
                profile_text += f"\n-{store.get('trade_mark', 'Нет названия магазина')} ({store.get('name', 'Без названия')})"
                keyboard = await get_profile_keyboard(user_id, stores)
        else:
            profile_text += "\nНет доступных магазинов"
        try:
            await callback_query.message.edit_text(
                text=profile_text,
                reply_markup=keyboard
            )
        except Exception as e:
            print(f"Edit message error: {e}")
            await callback_query.message.answer(
                text=profile_text,
                reply_markup=keyboard
            )

    except Exception as e:
        print(f"Critical error in to_profile_callback: {e}")
        await callback_query.message.answer("⚠️ Произошла ошибка при загрузке профиля")


async def get_date_report_callback_for_new(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик запроса отчета по дате"""
    try:
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        today = datetime.now().strftime("%Y-%m-%d")
        from telegram_bot_for_sellers_by_rqiza.bot.handlers.states import Form
        await callback_query.answer()
        builder = await create_date_keyboard()
        text = ("📅 Выбор даты отчета\n\n"
                "Выберите дату или введите вручную в формате ГГГГ-ММ-ДД\n\n\n"
                f"Ближайщая возможная дата - {today}")

        await get_or_edit_message(
            callback_query.from_user.id,
            text,
            builder.as_markup(),
            callback_query=callback_query,
            parse_mode="HTML",
            disable_web_page_preview=True
        )

        await state.set_state(Form.waiting_for_date_selection)

    except Exception as e:
        print(f"Error in get_date_report_callback: {e}")
        await callback_query.answer("Ошибка при выборе даты", show_alert=True)


async def get_date_report_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик запроса отчета по дате"""
    try:
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        today = datetime.now().strftime("%Y-%m-%d")
        from telegram_bot_for_sellers_by_rqiza.bot.handlers.states import Form
        await callback_query.answer()
        builder = await create_date_keyboard()
        text = ("📅 <b>Выбор даты отчета</b>\n\n"
                "Выберите дату или введите вручную в формате ГГГГ-ММ-ДД\n\n\n"
                f"Ближайщая возможная дата - {today}")

        await callback_query.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")

        await state.set_state(Form.waiting_for_date_selection)

    except Exception as e:
        print(f"Error in get_date_report_callback: {e}")
        await callback_query.answer("Ошибка при выборе даты", show_alert=True)


async def handle_date_selection(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик выбора даты"""
    try:
        from telegram_bot_for_sellers_by_rqiza.bot.handlers.states import Form
        action = callback_query.data.split(":")[0]
        if action == "set_date":
            selected_date = callback_query.data.split(":")[1]
            await callback_query.answer(f"Выбрана дата: {selected_date}")

            await state.update_data(selected_date=selected_date)

            user_id = callback_query.from_user.id
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"http://localhost:8000/get_user_stores/{user_id}") as resp:
                        if resp.status == 200:
                            stores = await resp.json()
                            keyboard = await build_report_keyboard(stores)

                            await callback_query.message.edit_text(
                                "🏪 <b>Выберите магазин для отчета</b>",
                                reply_markup=keyboard,
                                parse_mode="HTML"
                            )
                            await state.set_state(Form.waiting_for_store_selection)
                            return
            except Exception as e:
                print(f"Ошибка при получении магазинов: {e}")
                await callback_query.answer("Ошибка при загрузке магазинов", show_alert=True)
                return

        elif action == "enter_date_manually":
            builder = await create_date_user_keyboard()
            await callback_query.answer()
            await callback_query.message.edit_text(
                "✏️ Введите дату в формате ГГГГ-ММ-ДД:\n\n"
                "Либо выберите ближайщую*",

                reply_markup=builder.as_markup(),
                parse_mode="HTML"
            )
            await state.set_state(Form.waiting_for_date)

    except Exception as e:
        print(f"Error in handle_date_selection: {e}")
        await callback_query.answer("Ошибка при выборе даты", show_alert=True)


async def get_report_callback(callback_query: types.CallbackQuery):
    try:
        await callback_query.answer("Формируем список магазинов...")

        user_id = callback_query.from_user.id
        text = "🛠 Выбери магазин для получения отчета:\n\n"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://localhost:8000/get_user_stores/{user_id}") as resp:
                    if resp.status == 200:
                        stores = await resp.json()
                        keyboard = await build_report_keyboard(stores)
                    else:
                        keyboard = get_report_fallback_keyboard()
        except Exception as e:
            print(f"Ошибка при получении магазинов: {e}")
            keyboard = get_report_fallback_keyboard()
        try:
            await callback_query.message.edit_text(
                text=text,
                reply_markup=keyboard
            )
        except:
            await callback_query.message.answer(
                text=text,
                reply_markup=keyboard
            )

    except Exception as e:
        print(f"Ошибка в get_report_callback: {e}")
        await callback_query.message.answer("⚠️ Произошла ошибка при загрузке магазинов")


async def add_new_shop(callback_query: types.CallbackQuery):
    await callback_query.answer()
    keyboard = get_add_new_shop()
    text = (
        "🛠 ПОДКЛЮЧЕНИЕ\n\n"
        "1️⃣ Зайдите в Личный кабинет WB → Настройки → Доступ к API (https://seller.wildberries.ru/supplier-settings/access-to-api)\n\n"
        "2️⃣ Нажмите кнопку [+ Создать новый токен] и введите любое имя токена\n\n"
        "3️⃣ Нажмите галочку Только на чтение и выберите тип Статистика,Продвижение,Аналитика\n\n"
        "4️⃣ Нажмите [Создать токен], а затем скопируйте его\n\n"
        "👉🏻 Нажмите на команду /token (или напишите в ручную)\n"
        "🛠 Вставьте скопированный токен и отправьте сообщение."
    )
    await callback_query.message.edit_text(
        text=text,
        reply_markup=keyboard)


async def connect_wb_api_callback(callback_query: types.CallbackQuery):
    await callback_query.answer()
    text = (
        "🛠 ПОДКЛЮЧЕНИЕ\n\n"
        "1️⃣ Зайдите в Личный кабинет WB → Настройки → Доступ к API (https://seller.wildberries.ru/supplier-settings/access-to-api)\n\n"
        "2️⃣ Нажмите кнопку [+ Создать новый токен] и введите любое имя токена\n\n"
        "3️⃣ Нажмите галочку Только на чтение и выберите тип Статистика,Продвижение,Аналитика\n\n"
        "4️⃣ Нажмите [Создать токен], а затем скопируйте его\n\n"
        "👉🏻 Нажмите на команду /token (или напишите в ручную)\n"
        "🛠 Вставьте скопированный токен и отправьте сообщение."
    )
    await get_or_edit_message(
        callback_query.from_user.id,
        text,
        get_connect_wb_api_keyboard(),
        callback_query=callback_query,
        disable_web_page_preview=True
    )


async def back_one_callback(callback_query: types.CallbackQuery):
    await callback_query.answer()
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
    await get_or_edit_message(
        callback_query.from_user.id,
        text,
        get_start_keyboard(),
        callback_query=callback_query,
        parse_mode="HTML",
        disable_web_page_preview=True
    )
