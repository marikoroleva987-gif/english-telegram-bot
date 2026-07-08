import random
import asyncio
import datetime

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

import os
TOKEN = os.getenv("TOKEN")
CHAT_ID = 407552647

# Глобальные переменные для учета теста
current_word = None
test_active = False

# Переменные для ограничения сообщений
messages_today = 0
last_reset = datetime.date.today()


def load_words():
    try:
        with open("words.txt", "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return []

def save_words(words):
    with open("words.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(words))

# ----------------------------------------
# Основные команды для работы со словами
# ----------------------------------------

async def add_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.replace("/add", "", 1).strip()

    if "|" not in text:
        await update.message.reply_text(
            "Использование:\n/add слово | перевод | пример"
        )
        return

    words = load_words()

    words.append(text)

    save_words(words)

    await update.message.reply_text(
        "✅ Слово добавлено"
    )

async def list_words(update: Update, context: ContextTypes.DEFAULT_TYPE):
    words = load_words()

    if not words:
        await update.message.reply_text("Список пуст")
        return

    await update.message.reply_text("\n".join(words))

async def delete_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Использование: /delete слово"
        )
        return

    word = " ".join(context.args)
    words = load_words()

    if word in words:
        words.remove(word)
        save_words(words)
        await update.message.reply_text(
            f"Удалено: {word}"
        )
    else:
        await update.message.reply_text(
            "Слово не найдено"
        )

# ----------------------------------------
# Отправка случайного слова
# ----------------------------------------

async def send_random_word(context):
    words = load_words()

    if not words:
        return

    line = random.choice(words)
    parts = [p.strip() for p in line.split("|")]

    if len(parts) < 3:
        return

    english = parts[0]
    russian = parts[1]
    example = parts[2]

    message = (
        f"📖 Слово\n\n"
        f"🇬🇧 {english}\n\n"
        f"🇷🇺 {russian}\n\n"
        f"✍️ {example}"
    )

    await context.bot.send_message(
        chat_id=CHAT_ID,
        text=message
    )

    print("Отправлено:", english)

# ----------------------------------------
# Расписание и лимит сообщений
# ----------------------------------------

async def send_scheduled_word(app):
    global messages_today, last_reset

    today = datetime.date.today()
    # Обнуляем счетчик раз в сутки
    if today != last_reset:
        messages_today = 0
        last_reset = today

    # Ограничение 10 сообщений в день
    if messages_today >= 10:
        return

    await send_random_word(app)
    messages_today += 1

async def start_scheduled_loop(app):
    global messages_today, last_reset
    messages_today = 0
    last_reset = datetime.date.today()

    interval_seconds = 7200  # 2 часа
    while True:
        await send_scheduled_word(app)
        await asyncio.sleep(interval_seconds)

async def on_startup(app):
    # запуск расписания сразу
    asyncio.create_task(start_scheduled_loop(app))

# ----------------------------------------
# Тестовая функция
# ----------------------------------------

async def start_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_word, test_active

    words = load_words()

    if not words:
        await update.message.reply_text("Нет слов для теста.")
        return

    line = random.choice(words)
    parts = [p.strip() for p in line.split("|")]

    if len(parts) < 3:
        await update.message.reply_text("Некорректное слово для теста.")
        return

    current_word = line
    english_word = parts[0]

    test_active = True

    await update.message.reply_text(
        f"Переведите это слово:\n\n🇬🇧 {english_word}"
    )

async def check_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_word, test_active

    if not test_active:
        return  # Нет активного теста, ничего не делать

    user_answer = update.message.text.strip().lower()

    parts = [p.strip() for p in current_word.split("|")]
    if len(parts) < 3:
        return

    correct_answer = parts[1].lower()

    if user_answer == correct_answer:
        await update.message.reply_text("Верно! Молодец! 🎉")
    else:
        await update.message.reply_text(
            f"Неправильно. Правильный ответ: {parts[1]}"
        )

    test_active = False
    current_word = None

# ----------------------------------------
# Основная функция
# ----------------------------------------

def main():
    app = Application.builder().token(TOKEN).build()

    # Команды для слов
    app.add_handler(CommandHandler("add", add_word))
    app.add_handler(CommandHandler("list", list_words))
    app.add_handler(CommandHandler("delete", delete_word))

    # Команда для теста
    app.add_handler(CommandHandler("test", start_test))

    # Обработчик для ответов - любой текст, когда активен тест
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_answer))

    # Запуск расписания при старте
    app.post_init = on_startup

    print("Бот запущен")
    app.run_polling()

if __name__ == "__main__":
    main()