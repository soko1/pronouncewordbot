#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import re
import os
import configparser
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile

# --- Конфиг ---
config = configparser.ConfigParser()
config.read("config.ini")

BOT_TOKEN = config['system']['BOT_API']
AUDIO_DIR = config['system']['AUDIO_DIR']
DB_LOG = config['system']['DB_WRITE_COMMANDS']

# --- Проверка на повторный запуск ---
if os.popen(f"ps aux | grep {__file__} | grep -v grep").read().count("python") > 1:
    print("The bot is already running")
    exit(1)

# --- Создание папки для аудио ---
os.makedirs(AUDIO_DIR, exist_ok=True)

# --- Лог-файл ---
log_file = open(DB_LOG, 'a', encoding='utf-8')

# --- Aiogram ---
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- Тексты ---
HELP_TEXT = """
Type the word and get back an audio file with its pronunciation.

If the word is missing or you have ideas — write to @rogork
/thanks — supporters
/donate — support the developer
""".strip()

THANKS_TEXT = "Thanks:\nIt's empty :)".strip()

DONATE_TEXT = """
Support the developer:
https://sakaloucv.github.io/donate

telegram: @rogork
""".strip()

# --- Команды ---
@dp.message(Command("start", "help"))
async def cmd_help(message: Message):
    await message.answer(HELP_TEXT)

@dp.message(Command("thanks"))
async def cmd_thanks(message: Message):
    await message.answer(THANKS_TEXT)

@dp.message(Command("donate"))
async def cmd_donate(message: Message):
    await message.answer(DONATE_TEXT, parse_mode="Markdown")

@dp.message(Command("count"))
async def cmd_count(message: Message):
    try:
        with open(DB_LOG, 'r', encoding='utf-8') as f:
            content = f.read()
        users = len(set(re.findall(r'(\d+):', content)))
        await message.answer(f"Кол-во уникальных пользователей: {users}")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")

# --- Основной обработчик ---
@dp.message()
async def handle_word(message: Message):
    text = message.text.strip()
    chat_id = message.chat.id

    # Фильтр: только буквы, цифры, пробелы
    match = re.search(r'[\w ]+', text)
    if not match:
        await message.answer(HELP_TEXT)
        return

    word = match.group().lower()
    if len(word) < 2 or len(word) > 30:
        await message.answer(HELP_TEXT)
        return

    # Берём только первое слово
    word = word.split()[0]

    # Логируем
    print(f"{chat_id}: {word}", file=log_file, flush=True)

    # Путь к файлу
    audio_path = os.path.join(AUDIO_DIR, f"{word}.mp3")

    # Если файла нет — скачиваем
    if not os.path.exists(audio_path):
        url = f"https://wooordhunt.ru/data/sound/sow/us/{word}.mp3"
        try:
            r = requests.get(url, timeout=10, verify=False)
            if r.status_code == 200 and 'audio/mpeg' in r.headers.get('Content-Type', ''):
                with open(audio_path, 'wb') as f:
                    f.write(r.content)
        except Exception as e:
            print(f"Ошибка скачивания {word}: {e}")

    # Если файл есть — отправляем
    if os.path.exists(audio_path):
        audio = FSInputFile(audio_path)
        await message.answer_voice(audio)
    else:
        await message.answer(
            f"The word *{word}* is not found in the database.\n"
            "Write @rogork if you think it's a mistake.\n"
            "/help — more info",
            parse_mode="Markdown"
        )

# --- Запуск ---
async def main():
    print("PronounceWordBot запущен...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nБот остановлен.")
    finally:
        log_file.close()
