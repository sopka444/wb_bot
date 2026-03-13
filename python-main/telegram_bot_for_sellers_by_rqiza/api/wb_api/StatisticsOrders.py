from typing import Dict, Tuple, Any, Coroutine

from telegram_bot_for_sellers_by_rqiza.api.wb_api.Request_Utils import main_requests


async def get_orders(begin_date: str, headers: dict) -> Coroutine[Any, Any, Any]:
    """Получение данных о заказах."""
    url = 'https://statistics-api.wildberries.ru/api/v1/supplier/orders'
    params = {
        'dateFrom': begin_date,
        'flag': 1
    }
    return await main_requests(url, headers=headers, params=params)


def calculate_orders_amount_cost(orders) -> Tuple[int, float]:
    """Расчет количества заказов и их стоимости."""
    amount = len(orders)
    cost = sum(order['finishedPrice'] for order in orders)
    return amount, cost


async def get_orders_report(begin_date: str, headers: dict) -> Dict[str, int | float]:
    """
    Общая функция для получения отчета о заказах.

    :param begin_date: Начальная дата для запроса заказов.
    :param headers: Заголовки запроса, включая авторизацию.
    :return: Словарь с количеством заказов и их общей стоимостью.
    """
    orders = await get_orders(begin_date, headers)

    amount, cost = calculate_orders_amount_cost(orders)

    return {
        'orders_amount': amount,
        'orders_cost': cost
    }

