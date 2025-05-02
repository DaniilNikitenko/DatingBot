import asyncio
import logging
import sqlite3

from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode

from dotenv import load_dotenv
import os
from aiogram.client.default import DefaultBotProperties

load_dotenv()

bot = Bot(
    token=os.getenv("TELEGRAM_BOT_TOKEN"),
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
admin_id = os.getenv("ADMIN_ID")  # твой Telegram ID
dp = Dispatcher()

# ======= База данных =======
conn = sqlite3.connect("dating_bot.db")
cursor = conn.cursor()

cursor.execute(
    """
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    age INTEGER NOT NULL,
    city TEXT NOT NULL,
    about TEXT,
    photo_id TEXT NOT NULL
)
"""
)
conn.commit()


# ======= Состояния регистрации =======
class Register(StatesGroup):
    name = State()
    age = State()
    city = State()
    about = State()
    photo = State()


# ======= /start =======
@dp.message(F.text == "/start")
async def start(message: Message, state: FSMContext):
    await message.answer(
        "Привет! Давай зарегистрируемся. Как тебя зовут?",
        reply_markup=types.ReplyKeyboardRemove(),
    )
    await state.set_state(Register.name)


@dp.message(Register.name)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Сколько тебе лет?")
    await state.set_state(Register.age)


@dp.message(Register.age)
async def get_age(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введи число.")
        return
    await state.update_data(age=int(message.text))
    await message.answer("Из какого ты города?")
    await state.set_state(Register.city)


@dp.message(Register.city)
async def get_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    await message.answer(
        "Напиши немного о себе (можно пропустить, отправив прочерк '-')"
    )
    await state.set_state(Register.about)


@dp.message(Register.about)
async def get_about(message: Message, state: FSMContext):
    about = None if message.text.strip() == "-" else message.text
    await state.update_data(about=about)
    await message.answer("Отправь своё фото 📸 (обязательно!)")
    await state.set_state(Register.photo)


@dp.message(Register.photo, F.photo)
async def get_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    photo_id = message.photo[-1].file_id

    # Сохраняем в базу данных
    cursor.execute(
        """
        INSERT OR REPLACE INTO users (user_id, name, age, city, about, photo_id)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            message.from_user.id,
            data["name"],
            data["age"],
            data["city"],
            data.get("about"),
            photo_id,
        ),
    )
    conn.commit()

    # Формируем анкету
    caption = (
        f"<b>Имя:</b> {data['name']}\n"
        f"<b>Возраст:</b> {data['age']}\n"
        f"<b>Город:</b> {data['city']}\n"
    )

    if data.get("about"):
        caption += f"<b>О себе:</b> {data.get('about', '—')}"

    # Клавиатура с действиями
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="🔍 Смотреть анкеты")],
            [types.KeyboardButton(text="✏️ Редактировать анкету")],
        ],
        resize_keyboard=True,
    )

    await message.answer_photo(
        photo=photo_id,
        caption=caption,
        reply_markup=keyboard,
        parse_mode="HTML",
    )

    await state.clear()


class EditProfile(StatesGroup):
    name = State()  # для изменения имени
    age = State()  # для изменения возраста
    city = State()  # для изменения города
    photo = State()  # для изменения фото


# ======= Обработчик команды "✏️ Редактировать анкету" =======
@dp.message(F.text == "✏️ Редактировать анкету")
async def edit_profile_menu(message: Message, state: FSMContext):
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="Изменить имя")],
            [types.KeyboardButton(text="Изменить возраст")],
            [types.KeyboardButton(text="Изменить город")],
            [types.KeyboardButton(text="Изменить фото")],
            [types.KeyboardButton(text="Изменить всю анкету")],
            [types.KeyboardButton(text="Показать анкету")],
        ],
        resize_keyboard=True,
    )
    await message.answer("Выберите, что вы хотите изменить:", reply_markup=keyboard)
    await state.clear()


# ======= Обработчики кнопок редактирования =======
@dp.message(F.text == "Изменить имя")
async def change_name(message: Message, state: FSMContext):
    await message.answer("Напиши новое имя:")
    await state.set_state(EditProfile.name)


@dp.message(EditProfile.name)
async def edit_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    cursor.execute(
        "UPDATE users SET name = ? WHERE user_id = ?",
        (message.text, message.from_user.id),
    )
    conn.commit()
    await message.answer("Имя обновлено!")
    await state.clear()


@dp.message(F.text == "Изменить возраст")
async def change_age(message: Message, state: FSMContext):
    await message.answer("Напиши новый возраст:")
    await state.set_state(EditProfile.age)


@dp.message(EditProfile.age)
async def edit_age(message: Message, state: FSMContext):
    await state.update_data(age=message.text)
    cursor.execute(
        "UPDATE users SET age = ? WHERE user_id = ?",
        (message.text, message.from_user.id),
    )
    conn.commit()
    await message.answer("Возраст успешно обновлён!")
    await state.clear()


@dp.message(F.text == "Изменить город")
async def change_city(message: Message, state: FSMContext):
    await message.answer("Напиши новый город:")
    await state.set_state(EditProfile.city)


@dp.message(EditProfile.city)
async def edit_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    cursor.execute(
        "UPDATE users SET city = ? WHERE user_id = ?",
        (message.text, message.from_user.id),
    )
    conn.commit()
    await message.answer("Город успешно обновлён!")
    await state.clear()


@dp.message(F.text == "Изменить фото")
async def change_photo(message: Message, state: FSMContext):
    await message.answer("Отправь новое фото 📸:")
    await state.set_state(EditProfile.photo)


@dp.message(EditProfile.photo, F.photo)
async def edit_photo(message: Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    await state.update_data(photo_id=photo_id)
    cursor.execute(
        "UPDATE users SET photo_id = ? WHERE user_id = ?",
        (photo_id, message.from_user.id),
    )
    conn.commit()
    await message.answer("Фото успешно обновлено!")
    await state.clear()


# ======= Обновление всей анкеты (начать регистрацию заново) =======
@dp.message(F.text == "Изменить всю анкету")
async def change_full_profile(message: Message, state: FSMContext):
    await message.answer("Давайте обновим вашу анкету заново!")
    await state.set_state(Register.name)
    await message.answer("Как тебя зовут?")


# ======= Показать анкету =======
@dp.message(F.text == "Показать анкету")
async def show_profile(message: Message, state: FSMContext):
    cursor.execute(
        "SELECT name, age, city, about, photo_id FROM users WHERE user_id = ?",
        (message.from_user.id,),
    )
    result = cursor.fetchone()
    if not result:
        await message.answer("Анкета не найдена. Пожалуйста, зарегистрируйтесь.")
        return

    name, age, city, about, photo_id = result

    caption = (
        f"<b>Имя:</b> {name}\n"
        f"<b>Возраст:</b> {age}\n"
        f"<b>Город:</b> {city}\n"
        f"<b>О себе:</b> {about or '—'}"
    )

    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="🔍 Смотреть анкеты")],
            [types.KeyboardButton(text="✏️ Редактировать анкету")],
        ],
        resize_keyboard=True,
    )

    await message.answer_photo(
        photo=photo_id, caption=caption, reply_markup=keyboard, parse_mode="HTML"
    )


@dp.message(F.text == "/show_all_users")
async def show_all_users(message: Message):
    if message.from_user.id != int(admin_id):
        await message.answer("У вас нет доступа к этой команде.")
        return
    cursor.execute("SELECT * FROM users")
    rows = cursor.fetchall()

    if not rows:
        await message.answer("База данных пуста.")
        return

    # Ограничим вывод по длине сообщения (в Telegram максимум 4096 символов)
    response = ""
    for row in rows:
        user_info = f"ID: {row[0]}, Имя: {row[1]}\n, Возраст: {row[2]}\n, Город: {row[3]}\n, О себе: {row[4]}\n, Фото: {row[5]}\n"
        if len(response) + len(user_info) > 4000:
            await message.answer(response)
            response = ""
        response += user_info

    if response:
        await message.answer(response)


# Запуск
async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
