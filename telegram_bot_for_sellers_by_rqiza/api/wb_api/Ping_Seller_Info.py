import asyncio

from telegram_bot_for_sellers_by_rqiza.api.wb_api.Request_Utils import main_requests


async def user_connect(headers):
    url = 'https://common-api.wildberries.ru/api/v1/seller-info'
    request = await main_requests(url, headers=headers)

    if isinstance(request, dict):
        # Нормализуем названия полей
        request['wb_sid'] = request.get('sid')
        request['trade_mark'] = request.get('tradeMark')
    return request


async def ping_statistics(headers):
    url = 'https://statistics-api.wildberries.ru/ping'
    request = await main_requests(url, headers=headers)
    return request


async def ping_promotions(headers):
    url = 'https://advert-api.wildberries.ru/ping'
    request = await main_requests(url, headers=headers)
    return request


async def ping_analytics(headers):
    url = 'https://seller-analytics-api.wildberries.ru/ping'
    request = await main_requests(url, headers=headers)
    return request


async def get_all_product_photos(headers: dict, limit: int = 5):
    """Получает фото товаров с WB (по умолчанию 5 первых фото)"""
    url = "https://content-api.wildberries.ru/content/v2/get/cards/list"

    request_body = {
        "settings": {
            "sort": {"ascending": False},
            "filter": {"withPhoto": 1},
            "cursor": {"limit": limit}
        }
    }

    try:
        response = await main_requests(
            url,
            headers=headers,
            methods="POST",
            params=request_body  # Важно использовать json вместо params!
        )

        if isinstance(response, dict) and response.get("cards"):
            photos = []
            for card in response["cards"]:
                if "photos" in card:
                    # Берем первое фото в максимальном качестве (big или hq)
                    first_photo = card["photos"][0]
                    photo_url = first_photo.get("big") or first_photo.get("hq")
                    if photo_url:
                        photos.append(photo_url)
            return photos

        return []

    except Exception as e:
        print(f"Ошибка при получении фото: {e}")
        return []


async def check_all_services(headers):
    tasks = [
        user_connect(headers),
        ping_statistics(headers),
        ping_promotions(headers),
        ping_analytics(headers),

    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return {
        "user_connect": results[0],
        "statistics": results[1],
        "promotions": results[2],
        "analytics": results[3],

    }
