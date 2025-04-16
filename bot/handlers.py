import random
import asyncio
from pathlib import Path
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from database import load_data, save_user_stats, QUIZ_FILE, CHARACTER_FILE, EMOJI_FILE, STATS_FILE

dp = Dispatcher()

def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🈯 Квиз 1 из 4 💮", callback_data="select_text_quiz_difficulty")],
        [InlineKeyboardButton(text="🦹🏼‍♂️ Квиз угадай персонажа 🥷🏽", callback_data="start_character_quiz")],
        [InlineKeyboardButton(text="🟠🐉 Угадай персонажа по Emoji 🌸🉐", callback_data="start_emoji_quiz")],
        [InlineKeyboardButton(text="📊 Показать мою статистику 💾", callback_data="show_stats")]
    ])

def difficulty_menu(quiz_type):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌱 Легкий", callback_data=f"difficulty|easy|{quiz_type}")],
        [InlineKeyboardButton(text="🌿 Средний", callback_data=f"difficulty|medium|{quiz_type}")],
        [InlineKeyboardButton(text="🔥 Сложный", callback_data=f"difficulty|hard|{quiz_type}")],
        [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_main")]
    ])

@dp.message(Command("start"))
async def start_quiz(message: Message):
    user_id = str(message.from_user.id)
    stats = load_data(STATS_FILE)

    if user_id not in stats:
        stats[user_id] = {"correct": 0, "wrong": 0}
        save_user_stats(stats)

    await message.answer("🎌 Добро пожаловать в Аниме-Квиз!\n\nВыберите опцию:", reply_markup=main_menu())

@dp.callback_query(lambda c: c.data == "select_text_quiz_difficulty")
async def select_text_quiz_difficulty(callback: CallbackQuery):
    await callback.message.edit_text("Выберите уровень сложности:", reply_markup=difficulty_menu("text"))

@dp.callback_query(lambda c: c.data == "start_character_quiz")
async def start_character_quiz(callback: CallbackQuery):
    await callback.message.edit_text("Выберите уровень сложности:", reply_markup=difficulty_menu("image"))

@dp.callback_query(lambda c: c.data == "start_emoji_quiz")
async def start_emoji_quiz(callback: CallbackQuery):
    await callback.message.edit_text("Выберите уровень сложности:", reply_markup=difficulty_menu("emoji"))

@dp.callback_query(lambda c: c.data == "back_to_main")
async def back_to_main_menu(callback: CallbackQuery):
    try:
        await callback.message.edit_text("Вы вернулись в главное меню.", reply_markup=main_menu())
    except Exception:
        await callback.message.answer("Вы вернулись в главное меню.", reply_markup=main_menu())

@dp.callback_query(lambda c: c.data.startswith("difficulty|"))
async def handle_difficulty_selection(callback: CallbackQuery):
    user_id = str(callback.from_user.id)
    difficulty, quiz_type = callback.data.split("|")[1:]

    user_stats = load_data(STATS_FILE)
    user_stats.setdefault(user_id, {})["difficulty"] = difficulty
    save_user_stats(user_stats)

    chat_id = callback.message.chat.id
    await callback.message.answer(f"🔹 Вы выбрали уровень: *{difficulty.capitalize()}*!\nГотовимся к первому вопросу...", parse_mode="Markdown")

    await asyncio.sleep(1)
    if quiz_type == "text":
        await send_question(user_id, chat_id)
    elif quiz_type == "image":
        await send_character_question(user_id, chat_id)
    else:
        await send_emoji_question(user_id, chat_id)

# === ОТПРАВКА ВОПРОСОВ ===

async def send_question(user_id, chat_id):
    data = load_data(QUIZ_FILE)
    user_stats = load_data(STATS_FILE)
    difficulty = user_stats.get(user_id, {}).get("difficulty", "easy")

    question_list = data.get(difficulty, [])
    if not question_list:
        return

    question = random.choice(question_list)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=option, callback_data=f"answer|{option}|{question['correct']}")] for option in question["options"]
        ]
    )

    bot_msg = f"❓ *{question['question']}*"
    await dp.bot.send_message(chat_id, bot_msg, reply_markup=keyboard, parse_mode="Markdown")

async def send_character_question(user_id, chat_id):
    data = load_data(CHARACTER_FILE)
    user_stats = load_data(STATS_FILE)
    difficulty = user_stats.get(user_id, {}).get("difficulty", "easy")

    question_list = data.get(difficulty, [])
    if not question_list:
        return

    question = random.choice(question_list)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=option, callback_data=f"answer|{option}|{question['correct']}")] for option in question["options"]
        ]
    )

    image_path = Path("achievements") / question["image"]
    photo = FSInputFile(image_path)
    await dp.bot.send_photo(chat_id, photo=photo, caption="Угадай персонажа:", reply_markup=keyboard)

async def send_emoji_question(user_id, chat_id):
    data = load_data(EMOJI_FILE)
    user_stats = load_data(STATS_FILE)
    difficulty = user_stats.get(user_id, {}).get("difficulty", "easy")

    question_list = data.get(difficulty, [])
    if not question_list:
        return

    question = random.choice(question_list)
    emoji_text = " ".join(question["emoji"])
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=option, callback_data=f"answer|{option}|{question['correct']}")] for option in question["options"]
        ]
    )

    await dp.bot.send_message(chat_id, f"Угадай аниме по эмодзи:\n{emoji_text}", reply_markup=keyboard)

# === ОБРАБОТКА ОТВЕТА ===

@dp.callback_query(lambda c: c.data.startswith("answer|"))
async def handle_answer(callback: CallbackQuery):
    user_id = str(callback.from_user.id)
    answer_data = callback.data.split("|")
    selected_answer = answer_data[1]
    correct_answer = answer_data[2]

    stats = load_data(STATS_FILE)
    stats.setdefault(user_id, {"correct": 0, "wrong": 0})

    if selected_answer == correct_answer:
        stats[user_id]["correct"] += 1
        text = "✅ Верно!"
    else:
        stats[user_id]["wrong"] += 1
        text = f"❌ Неверно! Правильный ответ: {correct_answer}"

    save_user_stats(stats)
    await callback.message.answer(text)
    await asyncio.sleep(1)

    difficulty = stats[user_id].get("difficulty", "easy")
    quiz_type = "text"
    if callback.message.photo:
        quiz_type = "image"
    elif "эмодзи" in callback.message.text.lower():
        quiz_type = "emoji"

    if quiz_type == "text":
        await send_question(user_id, callback.message.chat.id)
    elif quiz_type == "image":
        await send_character_question(user_id, callback.message.chat.id)
    else:
        await send_emoji_question(user_id, callback.message.chat.id)

# === СТАТИСТИКА ===

@dp.callback_query(lambda c: c.data == "show_stats")
async def show_stats(callback: CallbackQuery):
    user_id = str(callback.from_user.id)
    stats = load_data(STATS_FILE)
    user_stats = stats.get(user_id, {"correct": 0, "wrong": 0})

    correct = user_stats.get("correct", 0)
    wrong = user_stats.get("wrong", 0)
    total = correct + wrong
    percent = round((correct / total) * 100, 2) if total else 0

    await callback.message.answer(
        f"📊 Ваша статистика:\n\n"
        f"✅ Правильных ответов: {correct}\n"
        f"❌ Неправильных ответов: {wrong}\n"
        f"📈 Точность: {percent}%"
    )
