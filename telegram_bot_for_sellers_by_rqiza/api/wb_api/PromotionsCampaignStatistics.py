from telegram_bot_for_sellers_by_rqiza.api.wb_api.Request_Utils import main_requests


async def get_promotion_count(headers: dict):
    """Получение количества рекламных кампаний."""
    url = 'https://advert-api.wildberries.ru/adv/v1/promotion/count'
    return await main_requests(url, headers)


def calculate_company_id(company_id):
    advert_ids = []
    for adverts in company_id['adverts']:
        for advert in adverts['advert_list']:
            advert_ids.append(advert['advertId'])
    return advert_ids


async def post_company_stat(promotion_ids: list, begin_date: str, headers: dict):
    """Получение статистики по рекламным кампаниям."""
    url = 'https://advert-api.wildberries.ru/adv/v2/fullstats'
    params = [{'id': promotion_id, 'dates': [begin_date] } for promotion_id in
              promotion_ids]
    return await main_requests(url, headers, params,methods='POST')


def calculate_company_stat_sum(company_stat: list):
    """Расчет суммы значений по ключам 'sum' и 'views'."""
    keys = ['sum', 'views']
    result = {}
    for key in keys:
        try:
            if company_stat != None:
                values = [c[key] for c in company_stat]
                result[key] = sum(values)
                round(result[key],1)
            else:
                result[key] = 0
        except KeyError:
            result[key] = 0
    return result


async def get_promotion_statistics(headers: dict, begin_date: str):
    """
    Основная функция для получения и расчета статистики по рекламным кампаниям.

    :param headers: Заголовки запроса, включая авторизацию.
    :param begin_date: Начальная дата периода.
    :param end_date: Конечная дата периода.
    :return: Словарь с суммарными значениями по ключам 'sum' и 'views'.
    """
    # Получаем количество рекламных кампаний
    promotion_count_response = await get_promotion_count(headers)
    # Получаем список ID рекламных кампаний
    promotion_ids = calculate_company_id(promotion_count_response)
    # Получаем статистику по рекламным кампаниям
    company_stat_response = await post_company_stat(promotion_ids, begin_date,  headers)
    # Рассчитываем сумму значений по ключам 'sum' и 'views'
    result = calculate_company_stat_sum(company_stat_response)
    return result

