import random
import asyncio
from pathlib import Path
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from database import load_data, save_user_stats, QUIZ_FILE, CHARACTER_FILE, EMOJI_FILE, STATS_FILE

dp = Dispatcher()

# Главное меню
def main_menu():
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🈯 Квиз 1 из 4 💮", callback_data="select_text_quiz_difficulty")],
            [InlineKeyboardButton(text="🦹🏼‍♂️ Квиз угадай персонажа 🥷🏽", callback_data="start_character_quiz")],
            [InlineKeyboardButton(text="🟠🐉 Угадай персонажа по Emoji 🌸🉐", callback_data="start_emoji_quiz")],
            [InlineKeyboardButton(text="📊 Показать мою статистику 💾", callback_data="show_stats")]
        ]
    )
    return markup


# Меню выбора сложности
def difficulty_menu(quiz_type):
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🌱 Легкий", callback_data=f"difficulty|easy|{quiz_type}")],
            [InlineKeyboardButton(text="🌿 Средний", callback_data=f"difficulty|medium|{quiz_type}")],
            [InlineKeyboardButton(text="🔥 Сложный", callback_data=f"difficulty|hard|{quiz_type}")],
            [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_main")]
        ]
    )
    return markup


# Функция экранирования для Mark
def escape_markdown_v2(text: str) -> str:
    escape_chars = r'\_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)


# Обработчик команды /start
@dp.message(Command("start"))
async def start_quiz(message: Message):
    user_id = str(message.from_user.id)
    stats = load_data(STATS_FILE)

    if user_id not in stats:
        stats[user_id] = {"correct": 0, "wrong": 0}
        save_user_stats(stats)

    await message.answer("🎌 Добро пожаловать в Аниме-Квиз!\n\nВыберите опцию:", reply_markup=main_menu())


# Выбор сложности текстового квиза
@dp.callback_query(lambda c: c.data == "select_text_quiz_difficulty")
async def select_text_quiz_difficulty(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text("Выберите уровень сложности:", reply_markup=difficulty_menu("text"))


# Выбор сложности квиза по персонажам
@dp.callback_query(lambda c: c.data == "start_character_quiz")
async def start_character_quiz(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text("Выберите уровень сложности:", reply_markup=difficulty_menu("image"))
 
    
# Выбор сложности квиза по Emoji
@dp.callback_query(lambda c: c.data == "start_emoji_quiz")
async def start_emoji_quiz(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text("Выберите уровень сложности:", reply_markup=difficulty_menu("emoji"))


# Обработчик кнопки "Назад в меню"
@dp.callback_query(lambda c: c.data == "back_to_main")
async def back_to_main_menu(callback: CallbackQuery):
    await callback.answer()
    try:
        await callback.message.edit_text("Вы вернулись в главное меню.", reply_markup=main_menu())
    except Exception:
        # Если сообщение не редактируемо (например, это фото), просто отправим новое сообщение
        await callback.message.answer("Вы вернулись в главное меню.", reply_markup=main_menu())





# Обработчик выбора сложности
@dp.callback_query(lambda c: c.data.startswith("difficulty|"))
async def handle_difficulty_selection(callback: CallbackQuery):
    await callback.answer()
    user_id = str(callback.from_user.id)
    difficulty, quiz_type = callback.data.split("|")[1:]

    user_stats = load_data(STATS_FILE)
    user_stats.setdefault(user_id, {})["difficulty"] = difficulty
    save_user_stats(user_stats)

    chat_id = callback.message.chat.id
    await bot.send_message(chat_id, f"🔹 Вы выбрали уровень: *{difficulty.capitalize()}*!\nГотовимся к первому вопросу...")

    await asyncio.sleep(0.7)

    if quiz_type == "text":                                  
        await send_question(user_id, chat_id)
    elif quiz_type == "image":
        await send_character_question(user_id, chat_id)
    else:
        await send_emoji_question(user_id, chat_id)



# Функция отправки вопроса (текстовый квиз)
async def send_question(user_id, chat_id):
    quiz_data = load_data(QUIZ_FILE)
    user_stats = load_data(STATS_FILE)
    difficulty = user_stats[user_id].get("difficulty", "medium")

    filtered_questions = [q for q in quiz_data.get("questions", []) if q["difficulty"] == difficulty]

    if not filtered_questions:
        await bot.send_message(chat_id, "😕 Вопросов для этого уровня пока нет.")
        return

    question = random.choice(filtered_questions)

    # Добавляем кнопку "Назад в меню"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=option, callback_data=f"answer|{option}")]
                         for option in question["options"]]
    )
    keyboard.inline_keyboard.append([InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_main")])

    user_stats[user_id]["current_question"] = {**question,"quiz_type": "text"}
    save_user_stats(user_stats)

    await bot.send_message(chat_id, f"❓ {question['question']}", reply_markup=keyboard)



# Функция отправки вопроса (угадай персонажа)
async def send_character_question(user_id, chat_id):
    character_data = load_data(CHARACTER_FILE)
    user_stats = load_data(STATS_FILE)
    difficulty = user_stats.get(user_id, {}).get("difficulty", "medium")

    filtered_questions = [q for q in character_data.get("questions", []) if q["difficulty"] == difficulty]

    if not filtered_questions:
        await bot.send_message(chat_id, "😕 Вопросов пока нет.")
        return

    question = random.choice(filtered_questions)

    # Добавляем кнопку "Назад в меню"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=option, callback_data=f"answer|{option}")]
                         for option in question["options"]]
    )
    keyboard.inline_keyboard.append([InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_main")])

    user_stats[user_id]["current_question"] = {**question,"quiz_type": "image"}
    save_user_stats(user_stats)

    photo = FSInputFile(question["image_path"])  
    await bot.send_photo(chat_id, photo, caption="🖼 Кто этот персонаж?", reply_markup=keyboard)


# Функция отправки вопроса (emoji квиз)
async def send_emoji_question(user_id, chat_id):
    emoji_quiz = load_data(EMOJI_FILE)
    user_stats = load_data(STATS_FILE)
    difficulty = user_stats[user_id].get("difficulty", "medium")

    filtered_questions = [q for q in emoji_quiz.get("questions", []) if q["difficulty"] == difficulty]

    if not filtered_questions:
        await bot.send_message(chat_id, "😕 Вопросов для этого уровня пока нет.")
        return

    question = random.choice(filtered_questions)

    # Добавляем кнопку "Назад в меню"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=option, callback_data=f"answer|{option}")]
                         for option in question["options"]]
    )
    keyboard.inline_keyboard.append([InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_main")])

    user_stats[user_id]["current_question"] = {**question,"quiz_type": "emoji"}
    save_user_stats(user_stats)

    await bot.send_message(chat_id, f"❓ {question['question']}", reply_markup=keyboard)

# === ОБРАБОТКА ОТВЕТА ===

# Обработчик ответов    
@dp.callback_query(lambda c: c.data.startswith("answer|"))
async def handle_answer(callback: CallbackQuery):
    await callback.answer()
    user_id = str(callback.from_user.id)
    user_stats = load_data(STATS_FILE)

    if user_id not in user_stats or "current_question" not in user_stats[user_id]:
        await callback.answer("🔹 Начните квиз заново!", show_alert=True)
        return

    question = user_stats[user_id]["current_question"]
    selected_answer = callback.data.split("|")[1]
    correct_answer = question["answer"]

    if selected_answer == correct_answer:
        response = f"✅ Верно! {question['explanation']}"
        user_stats[user_id]["correct"] += 1
    else:
        response = f"❌ Неверно. Правильный ответ: {correct_answer}.\n{question['explanation']}"
        user_stats[user_id]["wrong"] += 1

    del user_stats[user_id]["current_question"]
    save_user_stats(user_stats)
    
    # Отправляем ОТДЕЛЬНОЕ сообщение с результатом
    await callback.message.answer(response)

    await asyncio.sleep(0.7)
    quiz_type = question.get("quiz_type", "text")  # fallback на "text
    if quiz_type == "image":
        await send_character_question(user_id, callback.message.chat.id)
    elif quiz_type == "emoji":
        await send_emoji_question(user_id, callback.message.chat.id)
    else:
        await send_question(user_id, callback.message.chat.id)

# === СТАТИСТИКА ===

# Обработчик отображения статистики
@dp.callback_query(lambda c: c.data == "show_stats")
async def show_stats(callback: CallbackQuery):
    user_id = str(callback.from_user.id)
    user_stats = load_data(STATS_FILE)
    stats = user_stats.get(user_id, {})

    correct = stats.get("correct", 0)
    wrong = stats.get("wrong", 0)
    total = correct + wrong
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_main")]]
    )

    if total == 0:
        message_text = "📊 У вас пока нет статистики. Начните квиз, чтобы набрать очки!"
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_main")]]
        )
        await callback.message.edit_text(message_text, reply_markup=keyboard)
        return

    # Вычисляем процент
    percentage = int((correct / total) * 100)

    # Подбираем ачивку по прогрессу
    achievements = {
        10: "achievements/10.png",
        30: "achievements/30.png",
        50: "achievements/50.gif",
        70: "achievements/70.gif",
        90: "achievements/90.png",
        100: "achievements/100.gif"
    }

    ACHIEVEMENT_TEXTS =  {
        10: "У тебя начинает получаться! Начало положено!",
        30: "Хорошая работа! Это уже успех!",
        50: "Половина пути пройдена!",
        70: "Вы близки к вершине !",
        90: "Вау! Ты почти аниме!",
        100: "⁴⁰⁴ТЕБЕ БО⁴⁰⁴ЛЬШЕ НЕ  НУ⁴⁰⁴ЖНО АНИМЕ ЧТОБЫ СМОТ⁴⁰⁴РЕТЬ АНИМ⁴⁰⁴Е",
    }

    caption_text =""
    for percent in sorted(ACHIEVEMENT_TEXTS.keys(), reverse=True):
        if percentage >= percent:
            caption_text = ACHIEVEMENT_TEXTS[percent]
            break
    hidden_text = f" || Процент правильных ответов : {percentage}%||"
    
    # 👇 Экранируем для MarkdownV2
    caption_text = escape_markdown_v2(caption_text)
    hidden_text = escape_markdown_v2(hidden_text)
    caption_full = f"{caption_text}\n\n{hidden_text}"

    selected_image = None
    for percent in sorted(achievements.keys()):
        if percentage >= percent:
            selected_image = achievements[percent]

    if selected_image:
        file = FSInputFile(selected_image)
        ext = Path(selected_image).suffix.lower()

        if ext == ".gif":
            await callback.message.answer_animation(
                animation=file,
                caption=caption_full,
                reply_markup=keyboard,
                parse_mode="MarkdownV2"
            )
        elif ext in [".jpg", ".jpeg", ".png"]:
            await callback.message.answer_photo(
                photo=file,
                caption=caption_full,
                reply_markup=keyboard,
                parse_mode="MarkdownV2"
            )
        else:
            fallback_text = f"{caption_text}\n\n{escape_markdown_v2('Неподдерживаемый формат')}"
            await callback.message.answer(text=fallback_text, reply_markup=keyboard, parse_mode="MarkdownV2")
    else:
        message_text = escape_markdown_v2("📊 У вас пока нет статистики. Начните квиз, чтобы набрать очки!")
        await callback.message.edit_text(message_text, reply_markup=keyboard, parse_mode="MarkdownV2")
