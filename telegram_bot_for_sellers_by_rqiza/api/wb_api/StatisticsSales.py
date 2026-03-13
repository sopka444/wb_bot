from telegram_bot_for_sellers_by_rqiza.api.wb_api.Request_Utils import main_requests
from typing import Dict, Tuple, List


async def get_sales(begin_date: str, headers: dict) -> List[Dict]:
    """Получение данных о продажах."""
    url_sales = 'https://statistics-api.wildberries.ru/api/v1/supplier/sales'
    params = {
        'dateFrom': begin_date,
        'flag': 1
    }
    return await main_requests(url_sales, headers=headers, params=params)


def calculate_sales_amount(sales: List[Dict]) -> Tuple[int, int, int]:
    """Расчет количества продаж."""
    sale_count_s = sum(1 for c in sales if c['saleID'][0] == "S")
    sale_count_r = sum(1 for c in sales if c['saleID'][0] == "R")
    return sale_count_s, sale_count_r, sale_count_s - sale_count_r


def calculate_sales_cost(sales: List[Dict]) -> Tuple[float, float]:
    """Расчет стоимости продаж."""
    for_pay = sum(c['forPay'] for c in sales)
    finished_price = sum(c['finishedPrice'] for c in sales)
    return for_pay, finished_price


async def get_sales_report(begin_date: str, headers: dict) -> Dict[str, any]:
    """
    Основная функция для получения отчета по продажам.
    """
    sales_data = await get_sales(begin_date, headers)
    sale_count_s, sale_count_r, sale_count_diff = calculate_sales_amount(sales_data)
    for_pay, finished_price = calculate_sales_cost(sales_data)

    report = {
        "sale_count_s": sale_count_s,
        "sale_count_r": sale_count_r,
        "sale_count_diff": sale_count_diff,
        "total_finished_price": finished_price,

    }

    return report
