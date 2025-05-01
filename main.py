from aiogram import Bot, Dispatcher, F, types
from aiogram.types import Message, WebAppInfo

import logging
import asyncio

from dotenv import load_dotenv  # для загрузки переменных окружения из .env-файла

import os  # для работы с переменными окружения

load_dotenv()

# Создаем бота и диспетчер
bot = Bot(os.getenv("TELEGRAM_BOT_TOKEN"))
dp = Dispatcher()


# Обработчик команды /start
@dp.message(F.text == "/start")
async def start_handler(message: Message):
    markup = types.ReplyKeyboardMarkup(
        keyboard=[
            [
                types.KeyboardButton(
                    text="Открыть веб-страницу",
                    web_app=WebAppInfo(
                        url="https://www.youtube.com/watch?v=y65BZbNB0YA"
                    ),
                )
            ]
        ],
        resize_keyboard=True,
    )
    await message.answer("привет", reply_markup=markup)


async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
