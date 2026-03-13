import asyncio

from aiogram import types
from aiogram.types import Message

from telegram_bot_for_sellers_by_rqiza.api.wb_api.Ping_Seller_Info import get_all_product_photos
from telegram_bot_for_sellers_by_rqiza.bot.keyboards.inline import get_report_webapp_keyboard, get_last_report_keyboard
from telegram_bot_for_sellers_by_rqiza.bot.services.wb_api_service import (
    get_sales_funnel_report,
    get_orders_report,
    get_sales_report,
    get_paid_storage_cost,
    get_promotion_statistics
)


async def generate_report(
        message: types.Message,
        begin_date: str,
        begin_date_str: str,
        end_date: str,
        end_date_str: str,
        store_id: str,
        token: str
):
    """Генерация отчета с фото и текстом в одном сообщении"""
    try:
        headers = {'Authorization': token}
        reports, product_photos = await asyncio.gather(
            main_requests(begin_date, begin_date_str, end_date, end_date_str, headers),
            get_all_product_photos(headers, limit=2)
        )
        report_message = (
            f"Отчет за {begin_date_str}:\n\n"
            f"🛍 <b>Количество заказов: {reports['orders_report']['orders_amount']}</b>\n"
            f"        Сумма заказов: {reports['orders_report']['orders_cost']}р\n\n"
            f"💸 <b>Общая сумма продаж: {reports['sales_report']['total_finished_price']}р</b>\n"
            f"        Возвратов: {reports['sales_report']['sale_count_r']}\n"
            f"        Выкупов: {reports['sales_report']['sale_count_s']}\n"
            f"        Итого продаж за день: {reports['sales_report']['sale_count_diff']}\n\n"
            f"📦 <b>Стоимость платного хранения: {reports['paid_storage_report']}р</b>\n\n"
            f"📈 <b>Статистика рекламных кампаний:</b>\n"
            f"        Сумма затрат на рекламу: {reports['promotion_report']['sum']}р\n"
            f"        Просмотры по рекламной компании: {reports['promotion_report']['views']} 👁\n\n"
            f"🔎<b> Перешли в карточку: {reports['sales_funnel']['total_open_card_count']}</b>\n"
            f"🗑<b> Добавили в корзину: {reports['sales_funnel']['total_add_to_cart_count']}</b>\n\n"
            f"Отчет сформирован ✅"
        )
        report_data = {
            "date": begin_date_str,
            "store_id": store_id,
            "orders_report": reports['orders_report'],
            "sales_report": reports['sales_report'],
            "paid_storage_report": reports['paid_storage_report'],
            "promotion_report": reports['promotion_report'],
            "sales_funnel": reports['sales_funnel']
        }
        if product_photos:
            try:
                await message.delete()
                await message.answer_photo(
                    photo=product_photos[0],
                    caption=report_message,
                    reply_markup=get_last_report_keyboard(report_data),
                    parse_mode="HTML"

                )

            except Exception as e:
                print(f"Ошибка при отправке фото: {e}")
                await message.answer(text=report_message, reply_markup=get_last_report_keyboard())
        else:
            await message.answer(text=report_message, reply_markup=get_last_report_keyboard())

    except Exception as e:
        print(f"Error generating report: {e}")
        await message.answer("⚠️ Ошибка при формировании отчета")


async def generate_report2(message: Message, BEGIN_USER_DATE, BEGIN_USER_DATE2, END_USER_NAME, END_USER_NAME2):
    reports = await main_requests(BEGIN_USER_DATE, BEGIN_USER_DATE2, END_USER_NAME, END_USER_NAME2)

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

    await message.answer(
        "Отчет готов! Нажмите кнопку ниже, чтобы просмотреть:",
        reply_markup=get_report_webapp_keyboard()
    )


async def main_requests(BEGIN_USER_DATE, BEGIN_USER_DATE2, END_USER_NAME, END_USER_NAME2, headers):
    """
    Выполняет все запросы и возвращает результаты.
    """
    sales_funnel, orders_report, sales_report, paid_storage_report, promotion_report = await asyncio.gather(
        get_sales_funnel_report(BEGIN_USER_DATE, END_USER_NAME, headers),
        get_orders_report(BEGIN_USER_DATE, headers),
        get_sales_report(BEGIN_USER_DATE, headers),
        get_paid_storage_cost(BEGIN_USER_DATE, END_USER_NAME, headers),
        get_promotion_statistics(headers, BEGIN_USER_DATE2)
    )

    return {
        'orders_report': orders_report,
        'sales_funnel': sales_funnel,
        'sales_report': sales_report,
        'paid_storage_report': paid_storage_report,
        'promotion_report': promotion_report
    }
