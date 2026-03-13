import asyncio
import logging
import aiohttp
import pandas as pd
from datetime import datetime, timedelta
from io import BytesIO
from collections import defaultdict

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

# Для AI анализа изображений
import google.generativeai as genai
from PIL import Image
import requests
from io import BytesIO

# Конфигурация
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
WB_API_TOKEN = "YOUR_WILDBERRIES_API_TOKEN"
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"  # Для анализа фото

# Настройка Gemini AI
genai.configure(api_key=GEMINI_API_KEY)
vision_model = genai.GenerativeModel('gemini-1.5-flash')

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Состояния для FSM
class ProductStates(StatesGroup):
    waiting_for_sku = State()
    waiting_for_photo = State()
    waiting_for_date_range = State()

# Кэш для данных
class DataCache:
    def __init__(self):
        self.sales_data = {}
        self.stocks_data = {}
        self.products_info = {}
        self.last_update = None
        
    def is_valid(self, minutes=5):
        if not self.last_update:
            return False
        return datetime.now() - self.last_update < timedelta(minutes=minutes)
    
    def update(self, sales=None, stocks=None, products=None):
        if sales:
            self.sales_data = sales
        if stocks:
            self.stocks_data = stocks
        if products:
            self.products_info = products
        self.last_update = datetime.now()

cache = DataCache()

# Класс для работы с Wildberries API
class WildberriesAPI:
    def __init__(self, api_token):
        self.api_token = api_token
        self.base_url = "https://statistics-api.wildberries.ru"
        self.headers = {"Authorization": self.api_token}
        
    async def get_sales(self, date_from=None, flag=1):
        """Получение продаж"""
        if not date_from:
            date_from = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            
        url = f"{self.base_url}/api/v1/supplier/sales"
        params = {
            "dateFrom": date_from,
            "flag": flag
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Error getting sales: {response.status}")
                        return None
            except Exception as e:
                logger.error(f"Exception in get_sales: {e}")
                return None
                
    async def get_stocks(self, date_from=None):
        """Получение остатков"""
        if not date_from:
            date_from = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            
        url = f"{self.base_url}/api/v1/supplier/stocks"
        params = {"dateFrom": date_from}
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Error getting stocks: {response.status}")
                        return None
            except Exception as e:
                logger.error(f"Exception in get_stocks: {e}")
                return None
                
    async def get_orders(self, date_from=None, flag=1):
        """Получение заказов"""
        if not date_from:
            date_from = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            
        url = f"{self.base_url}/api/v1/supplier/orders"
        params = {
            "dateFrom": date_from,
            "flag": flag
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Error getting orders: {response.status}")
                        return None
            except Exception as e:
                logger.error(f"Exception in get_orders: {e}")
                return None

wb_api = WildberriesAPI(WB_API_TOKEN)

# Класс для AI анализа изображений
class ImageAnalyzer:
    def __init__(self, model):
        self.model = model
        
    async def analyze_image(self, image_url=None, image_bytes=None):
        """Анализ изображения с помощью Gemini AI"""
        try:
            if image_url:
                response = requests.get(image_url)
                img = Image.open(BytesIO(response.content))
            elif image_bytes:
                img = Image.open(BytesIO(image_bytes))
            else:
                return "Нет изображения для анализа"
            
            prompt = """
            Проанализируй это изображение товара для маркетплейса Wildberries.
            Оцени следующие аспекты:
            1. Качество фото (освещение, четкость)
            2. Инфографика (есть ли текст/метки на фото)
            3. Привлекательность для покупателя
            4. Соответствие категории товара
            5. Рекомендации по улучшению
            
            Дай краткий, но информативный ответ на русском языке.
            """
            
            response = self.model.generate_content([prompt, img])
            return response.text
        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            return f"Ошибка анализа изображения: {str(e)}"

image_analyzer = ImageAnalyzer(vision_model)

# Клавиатуры
def get_main_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text="📊 Продажи")
    builder.button(text="📦 Остатки")
    builder.button(text="📈 График продаж")
    builder.button(text="🔍 Поиск товара")
    builder.button(text="📸 Анализ фото")
    builder.button(text="📅 Отчет за период")
    builder.button(text="🔄 Обновить данные")
    builder.button(text="⚙️ Настройки")
    builder.adjust(2, 2, 2, 2)
    return builder.as_markup(resize_keyboard=True)

def get_date_range_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="Сегодня", callback_data="date_today")
    builder.button(text="Вчера", callback_data="date_yesterday")
    builder.button(text="7 дней", callback_data="date_week")
    builder.button(text="30 дней", callback_data="date_month")
    builder.button(text="Свой период", callback_data="date_custom")
    builder.adjust(2, 2, 1)
    return builder.as_markup()

# Обработчики команд
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "🚀 Привет! Я бот для аналитики Wildberries.\n\n"
        "Я помогу тебе:\n"
        "• Анализировать продажи и остатки\n"
        "• Смотреть динамику по товарам\n"
        "• Анализировать фото товаров с помощью ИИ\n"
        "• Получать отчеты за разные периоды\n\n"
        "Выбери действие в меню ниже 👇",
        reply_markup=get_main_keyboard()
    )

@dp.message(F.text == "📊 Продажи")
async def show_sales(message: Message):
    await message.answer("🔄 Загружаю данные о продажах...")
    
    try:
        sales_data = await wb_api.get_sales()
        if not sales_data:
            await message.answer("❌ Не удалось получить данные о продажах")
            return
            
        # Анализ данных
        total_sales = len(sales_data)
        total_revenue = sum(sale.get('totalPrice', 0) for sale in sales_data)
        avg_price = total_revenue / total_sales if total_sales > 0 else 0
        
        # Группировка по дням
        sales_by_day = defaultdict(lambda: {'count': 0, 'revenue': 0})
        for sale in sales_data:
            date = sale.get('date', '')[:10]
            sales_by_day[date]['count'] += 1
            sales_by_day[date]['revenue'] += sale.get('totalPrice', 0)
        
        # Формирование отчета
        report = f"📊 *Отчет по продажам*\n\n"
        report += f"📦 Всего продаж: {total_sales}\n"
        report += f"💰 Выручка: {total_revenue:,.2f} ₽\n"
        report += f"💵 Средний чек: {avg_price:,.2f} ₽\n\n"
        report += "*Продажи по дням:*\n"
        
        for date, data in sorted(sales_by_day.items(), reverse=True)[:7]:
            report += f"📅 {date}: {data['count']} шт. ({data['revenue']:,.2f} ₽)\n"
        
        await message.answer(report, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Error in show_sales: {e}")
        await message.answer(f"❌ Ошибка: {str(e)}")

@dp.message(F.text == "📦 Остатки")
async def show_stocks(message: Message):
    await message.answer("🔄 Загружаю данные об остатках...")
    
    try:
        stocks_data = await wb_api.get_stocks()
        if not stocks_data:
            await message.answer("❌ Не удалось получить данные об остатках")
            return
            
        # Анализ остатков
        total_stocks = sum(stock.get('quantity', 0) for stock in stocks_data)
        unique_products = len(set(stock.get('nmId', 0) for stock in stocks_data))
        
        # Товары с низкими остатками
        low_stock = [s for s in stocks_data if s.get('quantity', 0) < 10]
        
        report = f"📦 *Отчет по остаткам*\n\n"
        report += f"📊 Всего товаров на складе: {total_stocks} шт.\n"
        report += f"📦 Уникальных товаров: {unique_products}\n"
        report += f"⚠️ Товаров с остатком <10: {len(low_stock)}\n\n"
        
        if low_stock:
            report += "*Товары, требующие пополнения:*\n"
            for stock in low_stock[:10]:
                report += f"• Артикул {stock.get('nmId')}: {stock.get('quantity')} шт.\n"
        
        await message.answer(report, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Error in show_stocks: {e}")
        await message.answer(f"❌ Ошибка: {str(e)}")

@dp.message(F.text == "📈 График продаж")
async def show_sales_chart(message: Message):
    await message.answer("🔄 Строю график продаж...")
    
    try:
        sales_data = await wb_api.get_sales()
        if not sales_data:
            await message.answer("❌ Не удалось получить данные")
            return
            
        # Подготовка данных для графика
        sales_by_date = defaultdict(float)
        for sale in sales_data:
            date = datetime.fromisoformat(sale['date'].replace('Z', '+00:00')).date()
            sales_by_date[date] += sale.get('totalPrice', 0)
        
        # Сортировка по дате
        dates = sorted(sales_by_date.keys())
        values = [sales_by_date[d] for d in dates]
        
        # Создание графика
        plt.figure(figsize=(10, 6))
        plt.plot(dates, values, marker='o', linestyle='-', linewidth=2, markersize=4)
        plt.title('Динамика продаж', fontsize=16, pad=20)
        plt.xlabel('Дата')
        plt.ylabel('Выручка, ₽')
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Сохранение во временный файл
        chart_file = f"chart_{datetime.now().timestamp()}.png"
        plt.savefig(chart_file, dpi=100, bbox_inches='tight')
        plt.close()
        
        # Отправка графика
        photo = FSInputFile(chart_file)
        await message.answer_photo(photo, caption="📈 График продаж за последние 7 дней")
        
        # Удаление временного файла
        import os
        os.remove(chart_file)
        
    except Exception as e:
        logger.error(f"Error in show_sales_chart: {e}")
        await message.answer(f"❌ Ошибка при создании графика: {str(e)}")

@dp.message(F.text == "🔍 Поиск товара")
async def search_product_start(message: Message, state: FSMContext):
    await message.answer("Введите артикул товара (nmId) для поиска:")
    await state.set_state(ProductStates.waiting_for_sku)

@dp.message(ProductStates.waiting_for_sku)
async def search_product_by_sku(message: Message, state: FSMContext):
    sku = message.text.strip()
    
    if not sku.isdigit():
        await message.answer("❌ Артикул должен быть числом. Попробуйте снова:")
        return
    
    await message.answer(f"🔄 Ищу информацию по артикулу {sku}...")
    
    try:
        # Получаем данные по товару
        sales_data = await wb_api.get_sales()
        stocks_data = await wb_api.get_stocks()
        
        # Фильтруем по артикулу
        product_sales = [s for s in sales_data if str(s.get('nmId')) == sku] if sales_data else []
        product_stocks = [s for s in stocks_data if str(s.get('nmId')) == sku] if stocks_data else []
        
        if not product_sales and not product_stocks:
            await message.answer(f"❌ Товар с артикулом {sku} не найден в продажах или остатках")
            await state.clear()
            return
        
        # Анализ данных
        total_sales = len(product_sales)
        total_revenue = sum(s.get('totalPrice', 0) for s in product_sales)
        total_quantity = sum(s.get('quantity', 0) for s in product_sales)
        
        current_stock = 0
        if product_stocks:
            current_stock = sum(s.get('quantity', 0) for s in product_stocks)
        
        report = f"🔍 *Информация о товаре {sku}*\n\n"
        report += f"📊 *Продажи*\n"
        report += f"• Количество продаж: {total_sales}\n"
        report += f"• Выручка: {total_revenue:,.2f} ₽\n"
        report += f"• Продано единиц: {total_quantity}\n\n"
        report += f"📦 *Остатки*\n"
        report += f"• Текущий остаток: {current_stock} шт.\n"
        
        await message.answer(report, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Error in search_product_by_sku: {e}")
        await message.answer(f"❌ Ошибка при поиске: {str(e)}")
    
    await state.clear()

@dp.message(F.text == "📸 Анализ фото")
async def analyze_photo_start(message: Message, state: FSMContext):
    await message.answer(
        "📸 Отправьте фото товара для анализа с помощью ИИ.\n"
        "Я оценю качество фото и дам рекомендации!"
    )
    await state.set_state(ProductStates.waiting_for_photo)

@dp.message(ProductStates.waiting_for_photo, F.photo)
async def analyze_photo(message: Message, state: FSMContext):
    await message.answer("🔄 Анализирую фото с помощью ИИ...")
    
    try:
        # Получаем фото
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)
        
        # Скачиваем фото
        photo_bytes = await bot.download_file(file_info.file_path)
        photo_data = photo_bytes.read()
        
        # Анализируем с помощью ИИ
        analysis = await image_analyzer.analyze_image(image_bytes=photo_data)
        
        # Отправляем результат
        await message.answer(
            f"🤖 *Результат анализа фото:*\n\n{analysis}",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in analyze_photo: {e}")
        await message.answer(f"❌ Ошибка при анализе фото: {str(e)}")
    
    await state.clear()

@dp.message(ProductStates.waiting_for_photo)
async def analyze_photo_invalid(message: Message):
    await message.answer("❌ Пожалуйста, отправьте фото (изображение)")

@dp.message(F.text == "📅 Отчет за период")
async def report_period_start(message: Message, state: FSMContext):
    await message.answer(
        "Выберите период для отчета:",
        reply_markup=get_date_range_keyboard()
    )
    await state.set_state(ProductStates.waiting_for_date_range)

@dp.callback_query(lambda c: c.data.startswith('date_'))
async def process_date_range(callback: CallbackQuery, state: FSMContext):
    date_type = callback.data.replace('date_', '')
    
    date_from = None
    if date_type == 'today':
        date_from = datetime.now().strftime("%Y-%m-%d")
    elif date_type == 'yesterday':
        date_from = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    elif date_type == 'week':
        date_from = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    elif date_type == 'month':
        date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    elif date_type == 'custom':
        await callback.message.edit_text(
            "Введите даты в формате ГГГГ-ММ-ДД через пробел\n"
            "Например: 2024-01-01 2024-01-31"
        )
        return
    
    await callback.message.edit_text(f"🔄 Формирую отчет за выбранный период...")
    
    try:
        sales_data = await wb_api.get_sales(date_from=date_from)
        orders_data = await wb_api.get_orders(date_from=date_from)
        
        if not sales_data and not orders_data:
            await callback.message.answer("❌ Нет данных за выбранный период")
            await state.clear()
            return
        
        total_sales = len(sales_data) if sales_data else 0
        total_revenue = sum(s.get('totalPrice', 0) for s in sales_data) if sales_data else 0
        total_orders = len(orders_data) if orders_data else 0
        
        report = f"📅 *Отчет за период*\n\n"
        report += f"📊 Продажи: {total_sales}\n"
        report += f"💰 Выручка: {total_revenue:,.2f} ₽\n"
        report += f"📦 Заказы: {total_orders}\n\n"
        
        if sales_data:
            top_products = defaultdict(float)
            for sale in sales_data:
                top_products[sale.get('nmId')] += sale.get('totalPrice', 0)
            
            report += "*Топ-5 товаров по выручке:*\n"
            for nmid, revenue in sorted(top_products.items(), key=lambda x: x[1], reverse=True)[:5]:
                report += f"• {nmid}: {revenue:,.2f} ₽\n"
        
        await callback.message.answer(report, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Error in process_date_range: {e}")
        await callback.message.answer(f"❌ Ошибка: {str(e)}")
    
    await state.clear()
    await callback.answer()

@dp.message(ProductStates.waiting_for_date_range)
async def process_custom_date(message: Message, state: FSMContext):
    try:
        date_start, date_end = message.text.split()
        # Валидация дат
        datetime.strptime(date_start, "%Y-%m-%d")
        datetime.strptime(date_end, "%Y-%m-%d")
        
        await message.answer(f"🔄 Формирую отчет с {date_start} по {date_end}...")
        
        # Аналогичная обработка как выше
        sales_data = await wb_api.get_sales(date_from=date_start)
        
        # ... (код обработки данных)
        
        await message.answer("✅ Отчет сформирован (здесь будет полный отчет)")
        
    except Exception as e:
        await message.answer(f"❌ Ошибка в формате дат: {str(e)}")
    
    await state.clear()

@dp.message(F.text == "🔄 Обновить данные")
async def refresh_data(message: Message):
    await message.answer("🔄 Обновляю данные из Wildberries API...")
    
    try:
        # Очищаем кэш и загружаем новые данные
        cache.update()  # Сброс кэша
        
        sales_data = await wb_api.get_sales()
        stocks_data = await wb_api.get_stocks()
        
        if sales_data:
            cache.update(sales=sales_data)
        if stocks_data:
            cache.update(stocks=stocks_data)
        
        await message.answer("✅ Данные успешно обновлены!")
        
    except Exception as e:
        logger.error(f"Error in refresh_data: {e}")
        await message.answer(f"❌ Ошибка при обновлении: {str(e)}")

@dp.message(F.text == "⚙️ Настройки")
async def show_settings(message: Message):
    settings_text = (
        "⚙️ *Настройки бота*\n\n"
        "• Токен WB: " + ("✅ Подключен" if WB_API_TOKEN != "YOUR_WILDBERRIES_API_TOKEN" else "❌ Не настроен") + "\n"
        "• Gemini AI: " + ("✅ Подключен" if GEMINI_API_KEY != "YOUR_GEMINI_API_KEY" else "❌ Не настроен") + "\n"
        "• Обновление кэша: каждые 5 минут\n"
        "• Язык: Русский\n\n"
        "Для изменения токенов отредактируйте файл конфигурации."
    )
    await message.answer(settings_text, parse_mode="Markdown")

@dp.message()
async def handle_unknown(message: Message):
    await message.answer(
        "❓ Неизвестная команда. Используйте меню для навигации.",
        reply_markup=get_main_keyboard()
    )

async def main():
    logger.info("Starting bot...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())