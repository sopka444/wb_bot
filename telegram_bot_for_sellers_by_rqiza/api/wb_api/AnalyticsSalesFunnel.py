from telegram_bot_for_sellers_by_rqiza.api.wb_api.Request_Utils import main_requests


async def get_sales_funnel_statistics(BEGIN_USER_DATE, END_USER_NAME, headers):
    url = 'https://seller-analytics-api.wildberries.ru/api/v2/nm-report/detail'
    params = {
        "period": {
            "begin": BEGIN_USER_DATE,
            "end": END_USER_NAME
        },
        "page": 1
    }
    return await main_requests(url, headers, params, methods='POST')


def calculate_sales_funnel_statistics(response):
    total_add_to_cart_count = 0
    total_open_card_count = 0

    for card in response['data']['cards']:
        add_to_cart_count = card['statistics']['selectedPeriod']['addToCartCount']
        total_add_to_cart_count += add_to_cart_count

    for card in response['data']['cards']:
        open_card_count = card['statistics']['selectedPeriod']['openCardCount']
        total_open_card_count += open_card_count

    return {
        'total_open_card_count': total_open_card_count,
        'total_add_to_cart_count': total_add_to_cart_count
    }


async def get_sales_funnel_report(BEGIN_USER_DATE, END_USER_NAME, headers_analytics):
    response = await get_sales_funnel_statistics(BEGIN_USER_DATE, END_USER_NAME, headers_analytics)
    return calculate_sales_funnel_statistics(response)
