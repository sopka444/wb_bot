import os
from dotenv import load_dotenv
from datetime import date, timedelta
from aiogram import Bot
# Загрузка переменных окружения
load_dotenv()

# Текущая дата и вчерашняя дата
TODAY = date.today()
YESTERDAY = TODAY - timedelta(days=1)
rqiza_bot = Bot(token='7679621344:AAE1XmeHCshs9iXge2gZX2zab7hi4oSB_H8')
# Токены API Wildberries
# wb_api_token_statistics = os.getenv('wb_api_token_statistics')
# wb_api_token_analytics = os.getenv('wb_api_token_analytics')
# wb_api_token_promotion = os.getenv('wb_api_token_promotion')
#
# # Заголовки для запросов
# headers_analytics = {'Authorization': wb_api_token_analytics}
# headers_statistics = {'Authorization': wb_api_token_statistics}
# headers_promotion = {'Authorization': wb_api_token_promotion}

# Глобальные переменные для хранения последних сообщений
user_messages = {}
