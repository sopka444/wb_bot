import asyncio

from telegram_bot_for_sellers_by_rqiza.api.wb_api.Request_Utils import main_requests


# TODO переделать работу функций/
# TODO /добавить основную функцию для вызова дочерних и дальшейнего обращения именно к ней а не вызова по отдельности/


async def get_paid_storage_id(begin_date: str, end_date: str, headers: dict):
    """Получение айди отчета по платному хранению."""
    url = 'https://seller-analytics-api.wildberries.ru/api/v1/paid_storage'
    params = {
        'dateFrom': begin_date,
        'dateTo': end_date
    }
    paid_storage_id = await main_requests(url, headers, params)
    return paid_storage_id['data']['taskId']


async def get_paid_storage_status(paid_storage_id: str, headers: dict):
    """Проверка статуса готовности отчета по платному хранению."""
    status_done = False
    url = f'https://seller-analytics-api.wildberries.ru/api/v1/paid_storage/tasks/{paid_storage_id}/status'
    paid_storage_status = await main_requests(url, headers)

    while not status_done:
        if paid_storage_status['data']['status'] != 'done':
            await asyncio.sleep(5)
            paid_storage_status = await main_requests(url, headers)

        elif paid_storage_status['data']['status'] == 'done':
            status_done = True

    return status_done


async def get_paid_storage_ready_report(paid_storage_id: str, headers: dict):
    """Получение готового отчета по платному хранению."""
    url = f'https://seller-analytics-api.wildberries.ru/api/v1/paid_storage/tasks/{paid_storage_id}/download'
    return await main_requests(url, headers)


def calculate_paid_storage_cost(report: list):
    """Расчет итоговой стоимости платного хранения."""
    total = sum([c['warehousePrice'] for c in report])
    return round(total,1)


async def get_paid_storage_cost(begin_date: str, end_date: str, headers: dict):
    """
    Общая функция для получения стоимости платного хранения.
    :param begin_date: Начальная дата периода.
    :param end_date: Конечная дата периода.
    :param headers: Заголовки запроса.
    :param max_retries: Максимальное количество попыток проверки статуса.
    :return: Итоговая стоимость платного хранения.
    """
    paid_storage_id = await get_paid_storage_id(begin_date, end_date, headers)

    status_done = await get_paid_storage_status(paid_storage_id, headers)

    report = await get_paid_storage_ready_report(paid_storage_id, headers)

    total_cost = calculate_paid_storage_cost(report)
    return total_cost
