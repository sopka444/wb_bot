import asyncio
from aiogram import Dispatcher, types
from aiogram.filters import Command
from telegram_bot_for_sellers_by_rqiza.bot.handlers.states import Form
from config import rqiza_bot
from handlers.commands import start_command, token_command, profile_command, about_command
from handlers.callbacks import (
    to_profile_callback,
    get_report_callback,
    connect_wb_api_callback,
    back_one_callback,
    handle_store_callback, get_date_report_callback, handle_date_selection, handle_store_selection, add_new_shop,
    get_date_report_callback_for_new, delet_user_token_callback, delet_user_token_button_callback, send_video_callback
)

from handlers.states import process_token_input, process_date_input

dp = Dispatcher()

#
dp.message.register(start_command, Command("start"))
dp.message.register(token_command, Command("token"))
dp.message.register(profile_command, Command("profile"))
dp.message.register(about_command, Command("about"))
#
dp.callback_query.register(add_new_shop, lambda c: c.data == "add_shop")
dp.callback_query.register(send_video_callback, lambda c: c.data == "send_video")
dp.callback_query.register(to_profile_callback, lambda c: c.data == "to_profile")
dp.callback_query.register(get_report_callback, lambda c: c.data == "get_report")
dp.callback_query.register(connect_wb_api_callback, lambda c: c.data == "connect_wb_api")
dp.callback_query.register(back_one_callback, lambda c: c.data == "back_one")
dp.callback_query.register(delet_user_token_callback, lambda c: c.data == "delet_user_token")
dp.callback_query.register(handle_store_callback, lambda callback: callback.data.startswith('store_'))
dp.callback_query.register(get_date_report_callback, lambda c: c.data == "report_by_date")
dp.callback_query.register(get_date_report_callback_for_new, lambda c: c.data == "report_by_date_for_new")
dp.callback_query.register(handle_date_selection, lambda c: c.data.startswith(('set_date:', 'enter_date_manually')))
dp.callback_query.register(handle_store_selection, lambda c: c.data.startswith('report_store_'))
dp.callback_query.register(delet_user_token_button_callback, lambda c: c.data.startswith('delet_store_'))
#
dp.message.register(process_token_input, Form.waiting_for_token)
dp.message.register(process_date_input, Form.waiting_for_date)


async def main():
    await dp.start_polling(rqiza_bot)


# async def get_small_avatar(message: types.Message):
#     user = message.from_user
#     photos = await rqiza_bot.get_user_profile_photos(user.id, limit=1)
#     if photos.photos:
#         available_sizes = len(photos.photos[0])
#         print(f"Доступно размеров: {available_sizes}")
#         # Получаем все варианты размеров
#         sizes = photos.photos[0]
#
#         # Проверяем параметры каждого размера
#         for i, size in enumerate(sizes):
#             file = await rqiza_bot.get_file(size.file_id)
#             await message.answer(
#                 f"Размер #{i + 1}:\n"
#                 f"• File ID: {size.file_id}\n"
#                 f"• Ширина: {size.width}px\n"
#                 f"• Высота: {size.height}px\n"
#                 f"• Размер файла: {file.file_size // 1024} KB"
#             )
#     if not photos.photos:
#         await message.answer("❌ У вас нет фото профиля.")
#         return
#
#     # Получаем уменьшенную версию (первое фото в массиве - самое маленькое)
#     small_photo = photos.photos[0][2]  # [0][0] — thumbnail (маленькая версия)
#
#     # Отправляем пользователю
#     await message.answer_photo(
#         photo=small_photo.file_id,
#         caption="Вот уменьшенная версия вашего аватара!"
#     )
# # todo когда дойду до готового отчета сделать запись экрана с получением айди видео
# для кнопки  -  пример об отчете

async def handle_video(message: types.Message):
    file_id = message.video.file_id
    print("File ID видео:", file_id)
    await message.reply(f"File ID: {file_id}")


dp.message.register(handle_video, lambda message: message.content_type == "video")
# dp.message.register(get_small_avatar)

if __name__ == "__main__":
    asyncio.run(main())
