#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This is a telegram bot for learning english.
Type the word and get back an audio file with it's pronunciation.

Get this code: https://github.com/soko1/pronouncewordbot

# Bot in action

https://t.me/Pronouncewordbot

# Contacts

@gnupg (telegram)
nullbsd@gmail.com (email)

# Donate

Bitcoin: 1NYYFoJiRPnkmFbcv5kYLqwsweix1cVmBT

(Webmoney)
WMZ: Z156396869707
WMR: R409106892241
WME: E320058433666

"""


from __future__ import unicode_literals
import os
import os.path
import re
import configparser
import asyncio
import requests
import telepot.aio

CONFIG = configparser.ConfigParser()
CONFIG.read("config.ini")

AUDIO_DIR = CONFIG['system']['AUDIO_DIR']
URL_WITH_AUDIO = CONFIG['system']['URL_WITH_AUDIO']


# защита от повторного запуска
CHECKPROC = os.popen("ps aux | grep %s" % __file__).read()
if CHECKPROC.count("python") > 1:
    print("The bot is already running")
    os._exit(1)

async def main(msg):
    """
    blabla
    """

    chat_id = msg['chat']['id']
    command = msg['text']

    help = """
Type the word and get back an audio file with its pronounciation.

If there are some words missing or you have an idea of improving the bot — be sure to contact me (@gnupg) and  you'll appear (if you wish) here on the list of supporters — /thanks

You can also thank me by giving a positive feedback or buy me a cup of coffee here — /donate
"""

    thanks = """
Thanks:

It's empty :)
"""

    donate = """
If you want to give thanks buying me a cup of coffee (which I'm really fond of!) — you're welcome:

Bitcoin: `1NYYFoJiRPnkmFbcv5kYLqwsweix1cVmBT`

(Webmoney)
WMZ: `Z156396869707`
WMR: `R409106892241`
WME: `E320058433666`

Any other way: email me at nullbsd@gmail.com or write back here on Telegram @gnupg

Thanks!
"""

    # вывод справки
    if command.find("/start") != -1:
        await BOT.sendMessage(chat_id, help)
        return
    if command.find("/help") != -1:
        await BOT.sendMessage(chat_id, help)
        return
    # доска почёта
    if command.find("/thanks") != -1:
        await BOT.sendMessage(chat_id, thanks)
        return
    # пожертвования
    if command.find("/donate") != -1:
        await BOT.sendMessage(chat_id, donate, parse_mode='Markdown')
        return
    # кол-во уникальных пользователей (незадокументированная команда)
    if command.find("/count") != -1:
        logfile = open(CONFIG['system']['DB_WRITE_COMMANDS'], 'r')
        logfile_content = logfile.read()
        logfile.close()
        num_of_uniq_users = len(set(re.findall(r'd+:', logfile_content)))
        await BOT.sendMessage(chat_id, 'Кол-во уникальных пользователей: ' + str(num_of_uniq_users))
        return

    # отсеивание мусора из спецсимволов
    search_letters = re.search(r'[\w ]+', command)
    if search_letters:
        command = search_letters.group()
    else:
        await BOT.sendMessage(chat_id, help)
        return

    # отсеивание сообщений менее 2 символов и более 30
    command_len = len(command)
    if command_len < 2 or command_len > 30:
        await BOT.sendMessage(chat_id, help)
        return

    # полученная строка
    string = command.lower()
    # разделяем на пробелы
    string = string.split(" ")
    # берём первое слово
    word = string[0]

    # запись лога с присланными сообщениями
    LOG.write("%s: %s\n" % (chat_id, word))
    LOG.flush()

    # путь к звуковому файлу
    audio_file_path = AUDIO_DIR + '/' + word + '.mp3'

    # если файл отсутствует на ФС
    if os.path.exists(audio_file_path) is False:
        # пытаемся найти слово в базе wooordhunt.ru
        fullurl = URL_WITH_AUDIO + word + '.mp3'

        request = requests.get(fullurl)

        # запрос сработал
        if request.status_code == 200:
            # проверка на аудифайл
            if 'audio/mpeg' in request.headers['Content-Type']:
                file = open(audio_file_path, 'wb')
                # пополняем локальную базу
                file.write(request.content)
                file.close()

    # если файл присутствует на ФС
    if os.path.exists(audio_file_path) is True:
        file = open(audio_file_path, 'rb')
        # отправляем пользователю
        await BOT.sendVoice(chat_id, file)
        file.close()
    else:
        # иначе присылаем
        message_for_send = """
The word *%s* is not found in a database.
If you find it wrong, then be sure to contact me — @gnupg

Get more info — /help""" % word
        await BOT.sendMessage(chat_id, message_for_send, parse_mode='Markdown')
        return

# активация бота
BOT = telepot.aio.Bot(CONFIG['system']['BOT_API'])

# создание списка задач
LOOP = asyncio.get_event_loop()
LOOP.create_task(BOT.message_loop({'chat': main}))

print('Listening ...')


LOG = open(CONFIG['system']['DB_WRITE_COMMANDS'], 'a')
print("read file for write")


try:
    LOOP.run_forever()
except KeyboardInterrupt:
    pass
finally:
    LOOP.stop()
    LOOP.close()
