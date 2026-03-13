from aiogram import types
from aiogram.fsm.context import FSMContext
from datetime import datetime
from telegram_bot_for_sellers_by_rqiza.bot.handlers.callbacks import get_or_edit_message
from telegram_bot_for_sellers_by_rqiza.bot.keyboards.inline import build_report_keyboard, get_connect_wb_api_keyboard, \
    get_report_fallback_keyboard, get_profile_keyboard, get_token_keyboard
from telegram_bot_for_sellers_by_rqiza.bot.services.report_service import generate_report
from telegram_bot_for_sellers_by_rqiza.bot.services.wb_api_service import check_all_services
from aiogram.fsm.state import StatesGroup, State
import aiohttp


class Form(StatesGroup):
    waiting_for_token = State()
    waiting_for_date = State()
    waiting_for_date_selection = State()
    waiting_for_date_input = State()
    waiting_for_store_selection = State()


async def process_date_input(message: types.Message, state: FSMContext):
    """Обработка ручного ввода даты"""
    try:
        user_input = message.text.strip()
        input_date = datetime.strptime(user_input, "%Y-%m-%d").date()
        date_str = str(input_date)

        # Сохраняем дату в состоянии
        await state.update_data(selected_date=date_str)

        # Получаем список магазинов пользователя
        user_id = message.from_user.id
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://localhost:8000/get_user_stores/{user_id}") as resp:
                    if resp.status == 200:
                        stores = await resp.json()
                        keyboard = await build_report_keyboard(stores)

                        await message.answer(
                            "🏪 <b>Выберите магазин для отчета</b>",
                            reply_markup=keyboard,
                            parse_mode="HTML"
                        )
                        await state.set_state(Form.waiting_for_store_selection)
                        return
        except Exception as e:
            print(f"Ошибка при получении магазинов: {e}")
            await message.answer("Ошибка при загрузке магазинов")
            return

    except ValueError:
        await message.answer("❌ Неверный формат даты. Используйте ГГГГ-ММ-ДД")
    except Exception as e:
        print(f"Error in process_date_input: {e}")
        await message.answer("⚠️ Ошибка при обработке даты")


async def process_token_input(message: types.Message, state: FSMContext):
    try:
        await message.bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)

        state_data = await state.get_data()
        if 'message_to_delete' in state_data:
            try:
                await message.bot.delete_message(chat_id=message.chat.id,
                                                 message_id=state_data['message_to_delete'])
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
                f"🏷 Марка: {user_info.get('tradeMark', user_info.get('trade_mark', 'Не указано'))}\n"
            )

            # Сохраняем токен и информацию о продавце
            async with aiohttp.ClientSession() as session:
                token_data = {
                    "user_id": message.from_user.id,
                    "token": user_token,
                    "username": message.from_user.username
                }

                seller_data = {
                    "wb_sid": user_info.get('wb_sid') or user_info.get('sid'),
                    "name": user_info.get('name', ''),
                    "trade_mark": user_info.get('trade_mark') or user_info.get('tradeMark', '')
                }

                api_url = "http://localhost:8000/save_token"
                payload = {
                    "token_data": token_data,
                    "seller_data": seller_data
                }

                async with session.post(api_url, json=payload) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        print(f"Ошибка при сохранении токена: {error_text}")
                    else:
                        result = await resp.json()
                        print(f"Токен успешно сохранён, ID: {result.get('token_id')}")

        if services_status.get('statistics'):
            headers_statistics = headers.copy()
        if services_status.get('analytics'):
            headers_analytics = headers.copy()
        if services_status.get('promotions'):
            headers_promotion = headers.copy()

        if error_services:
            response_parts.insert(0, "⚠ Некоторые сервисы недоступны:\n")
            keyboard = get_connect_wb_api_keyboard()
        else:
            response_parts.insert(0, "✅ Все сервисы доступны\n")
            keyboard = get_token_keyboard()

        response_message = "\n".join(response_parts)

    except Exception as e:
        response_message = f"❌ Ошибка при обработке токена: {str(e)}"
        keyboard = types.ReplyKeyboardRemove()
        await state.clear()

    await get_or_edit_message(
        message.from_user.id,
        response_message,
        keyboard,
        message=message
    )

    await state.clear()
