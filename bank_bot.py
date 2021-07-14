from bank_server import *
from telebot import TeleBot
import re

bot = TeleBot(TELEGRAM_TOKEN)
temp = {}


def get_account(chat_id):
    return Account.query.filter_by(telegram_id=chat_id).first()

def create_account(chat_id, name, surname):
    new_account = Account(telegram_id=chat_id, name=name, surname=surname)
    db.session.add(new_account)
    db.session.commit()

def send_help(chat_id):
    bot.send_message(chat_id, "- /balance - узнать баланс;\n- /history - история операций;")


@bot.message_handler(content_types=['text'])
def start(message):
    chat_id = message.chat.id
    text = message.text
    account = get_account(chat_id)

    if not account:
        msg = bot.send_message(chat_id, "Добрый день! Похоже, что у вас пока нет счета в нашем банке. Что создать счет, нужно указать имя и фамилию. Для начала, напишите имя на русском языке (например, Алексей)...")
        bot.register_next_step_handler(msg, save_name)
    elif text == '/balance':
        bot.send_message(chat_id, "Баланс вашего счета - {} gt".format(account.balance()))

def save_name(message):
    chat_id = message.chat.id
    name = message.text

    if bool(re.search('~[а-яА-Я ]', name)):
        msg = bot.send_message(chat_id, "Пожалуйста, используй только русские буквы...")
        bot.register_next_step_handler(msg, save_name)

    if len(name.split(' ')) > 1:
        msg = bot.send_message(chat_id, "Пожалуйста, напиши только имя...")
        bot.register_next_step_handler(msg, save_name)

    temp[chat_id] = {
        "name": name
    }

    msg = bot.send_message(chat_id,
                           "Спасибо! Теперь укажи фамилию...")
    bot.register_next_step_handler(msg, save_name)


def save_surname(message):
    chat_id = message.chat.id
    surname = message.text

    if chat_id not in temp:
        msg = bot.send_message(chat_id, "Напиши /start")

    if bool(re.search('~[а-яА-Я ]', surname)):
        msg = bot.send_message(chat_id, "Пожалуйста, используй только русские буквы...")
        bot.register_next_step_handler(msg, save_surname)

    temp[chat_id]['surname'] = surname
    create_account(chat_id, temp[chat_id]['name'], temp[chat_id]['surname'])
    bot.send_message(chat_id, "Все прошло успешно, номер вашего счета - {}".format(chat_id))
    send_help(chat_id)



