from init import *
from models import *
from telebot import TeleBot
import re
from uuid import uuid4

bot = TeleBot(TELEGRAM_TOKEN)
temp = {}

app = create_app()


def get_account(chat_id):
    with app.app_context():
        return Account.query.filter_by(telegram_id=chat_id).first()


def create_account(chat_id, name, surname):
    with app.app_context():
        new_account = Account(telegram_id=chat_id, name=name, surname=surname, trading_token=str(uuid4()))
        db.session.add(new_account)
        db.session.commit()


def send_help(chat_id):
    bot.send_message(chat_id,
                     "* /number - узнать номер счета\n* /balance - узнать баланс;\n* /history - история операций;\n* /token - торговый токен;\n* /reset_token - сбросить торговый токен;")


def send_history(account):
    with app.app_context():
        message = "Исходящие транзакции:\n"

        outtransactions = account.done_outcoming_transactions()

        if len(outtransactions) > 20:
            outtransactions = outtransactions[-20:]

        for transaction in outtransactions:
            if not transaction.receiver_account:
                receiver = "акселератора"
            else:
                receiver = transaction.receiver_account.telegram_id

            message += '* -{} gt на счет {} ({}, {})\n'.format(transaction.amount, receiver,
                                                               transaction.description,
                                                               transaction.created_on.strftime('%H:%M %d.%m.%Y'))

        if not outtransactions:
            message += '* еще нет...\n'

        message += "\nВходящие транзакции:\n"

        intransactions = account.done_incoming_transactions()
        if len(intransactions) > 20:
            intransactions = intransactions[-20:]

        for transaction in intransactions:
            if not transaction.sender_account:
                sender = "акселератора"
            else:
                sender = transaction.sender_account.telegram_id

            message += '* +{} gt со счета {} ({}, {})\n'.format(transaction.amount, sender,
                                                                transaction.description,
                                                                transaction.created_on.strftime('%H:%M %d.%m.%Y'))
        if not intransactions:
            message += '* еще нет...\n'

        bot.send_message(account.telegram_id, message)


def send_balance(account):
    with app.app_context():
        if IS_POSVYAT:
            bot.send_message(account.telegram_id, "Баланс вашего счета: 0 gt")
        else:
            bot.send_message(account.telegram_id, "Баланс вашего счета: {} gt".format(account.balance()))


def send_number(account):
    with app.app_context():
        bot.send_message(account.telegram_id, "Номер вашего счета: {}".format(account.telegram_id))


def send_token(account):
    with app.app_context():
        bot.send_message(account.telegram_id, "Ваш торговый токен: {}".format(account.trading_token))


def reset_token(account):
    with app.app_context():
        account.trading_token = str(uuid4())
        db.session.add(account)
        db.session.commit()
        bot.send_message(account.telegram_id, "Ваш новый торговый токен: {}".format(account.trading_token))


@bot.message_handler(content_types=['text'])
def start(message):
    with app.app_context():
        chat_id = message.chat.id
        text = message.text
        account = get_account(chat_id)

        if not account:
            msg = bot.send_message(chat_id,
                                   "Добрый день! Похоже, что у вас пока нет счета в нашем банке. Что создать счет, нужно указать имя и фамилию. Для начала, напишите имя на русском языке (например, Алексей)...")
            bot.register_next_step_handler(msg, save_name)
        elif text == '/balance':
            send_balance(account)
        elif text == '/number':
            send_number(account)
        elif text == '/help':
            send_help(chat_id)
        elif text == '/history':
            send_history(account)
        elif text == '/token':
            send_token(account)
        elif text == '/reset_token':
            reset_token(account)


def save_name(message):
    chat_id = message.chat.id
    name = message.text.strip()

    if bool(re.search(r'[^а-яА-Я\s]', name)):
        msg = bot.send_message(chat_id, "Пожалуйста, используй только русские буквы...")
        bot.register_next_step_handler(msg, save_name)
        return

    if len(name.split(' ')) > 1:
        msg = bot.send_message(chat_id, "Пожалуйста, напиши только имя...")
        bot.register_next_step_handler(msg, save_name)
        return

    temp[chat_id] = {
        "name": name.lower().capitalize()
    }

    msg = bot.send_message(chat_id,
                           "Спасибо! Теперь укажи фамилию...")
    bot.register_next_step_handler(msg, save_surname)


def save_surname(message):
    chat_id = message.chat.id
    surname = message.text.strip()

    if chat_id not in temp:
        msg = bot.send_message(chat_id, "Напиши /start")
        return

    if bool(re.search(r'[^а-яА-Я\s]', surname)):
        msg = bot.send_message(chat_id, "Пожалуйста, используй только русские буквы...")
        bot.register_next_step_handler(msg, save_surname)
        return

    temp[chat_id]['surname'] = surname.lower().capitalize()
    create_account(chat_id, temp[chat_id]['name'], temp[chat_id]['surname'])
    bot.send_message(chat_id, "Все прошло успешно, номер вашего счета - {}".format(chat_id))
    send_help(chat_id)


bot.polling(none_stop=True)
