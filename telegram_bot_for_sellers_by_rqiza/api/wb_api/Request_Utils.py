import asyncio
import aiohttp


async def main_requests(url: str, headers: dict, params: dict = None, methods=None, max_retries: int = 3):
    """
    Универсальная функция для выполнения HTTP-запросов с обработкой ошибок.

    :param url: ссылка на запрос
    :param headers: заголовок запроса
    :param params: параметры запроса (используется для GET)
    :param max_retries: максимальное количество попыток при ошибке 429
    """
    global response
    retries = 0
    async with aiohttp.ClientSession() as session:
        while retries < max_retries:
            try:
                if methods is None:
                    request = session.get(url, headers=headers, params=params)
                elif methods == 'POST':
                    request = session.post(url, headers=headers, json=params)
                else:
                    raise ValueError("Неподдерживаемый метод запроса")

                async with request as response:
                    if response.status == 200:
                        return await response.json()

                    elif response.status == 429:  # Too Many Requests
                        print(f'429. Попытка {retries + 1} из {max_retries}', url)
                        await asyncio.sleep(25)
                        retries += 1

                    elif response.status == 401:
                        raise Exception("Ошибка 401: Неверные учетные данные (проверьте токен).")

                    else:
                        raise Exception(f"Ошибка {response.status}: { response.text}", url)

            except aiohttp.ClientError as e:
                print(f"Ошибка при выполнении запроса: {e}", url)
                raise Exception(f"Ошибка при выполнении запроса: {e}", url)

        raise Exception(f"Превышено максимальное количество попыток ({max_retries}) для ошибки 429.", url)
