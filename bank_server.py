import random

import telebot

from init import *
from helpers import *
from models import *
from telebot import TeleBot

app = create_app()
bot = telebot.TeleBot(TELEGRAM_TOKEN)

def get_account_by_token(token):
    return Account.query.filter_by(trading_token=token).first()

def get_account(chat_id):
    return Account.query.filter_by(telegram_id=chat_id).first()

def get_transaction(transaction_id):
    return Transaction.query.filter_by( id=transaction_id).first()


@app.route('/')
def index():
    return "Waiting for the thunder"


@app.route('/debug-sentry')
def trigger_error():
    try:
        division_by_zero = 1 / 0
    except Exception as e:
        log(e, True)
        abort(500)

@app.route('/api/ask', methods=['POST'])
def ask_money():
    data = request.json

    if not data.get('token'):
        return jsonify({
            'state': 'error',
            'error': 'No trading token'
        }), 422

    if not data.get('description'):
        return jsonify({
            'state': 'error',
            'error': 'No description'
        }), 422

    if not data.get('account_id') or not isinstance(data.get('account_id'), int):
        return jsonify({
            'state': 'error',
            'error': 'No account id or it is not number'
        }), 422

    if not data.get('amount') or not isinstance(data.get('amount'), (int)) or data.get('amount') < 1:
        return jsonify({
            'state': 'error',
            'error': 'No amount or it is not number or lower than 1'
        }), 422

    receiver_account = get_account_by_token(data.get('token'))

    if not receiver_account:
        return jsonify({
            'state': 'error',
            'error': 'Incorrect trading token'
        }), 403

    if not receiver_account.trading_enabled:
        return jsonify({
            'state': 'error',
            'error': 'Your account is banned'
        }), 403

    sender_account = get_account(data.get('account_id'))

    if not sender_account:
        return jsonify({
            'state': 'error',
            'error': 'Wrong account_id'
        }), 404

    if sender_account.balance() < data.get('amount'):
        return jsonify({
            'state': 'error',
            'error': 'Insufficient funds'
        }), 422

    transaction = Transaction(from_id=sender_account.id,
                              to_id=receiver_account.id,
                              description=data.get('description'),
                              amount=data.get('amount'),
                              status='pending',
                              code=random.randint(1111, 9999),
                              type='trade')
    db.session.add(transaction)
    db.session.commit()

    bot.send_message(sender_account.telegram_id, "Запрос {} gt: {}\n\nКод подтверждения: {}".format(transaction.amount, transaction.description, transaction.code))

    return jsonify({
        'state': 'success',
        'transaction_id': transaction.id
    }), 200

@app.route('/api/verify', methods=['POST'])
def verify_transaction():
    data = request.json

    if not data.get('transaction_id') or not isinstance(data.get('transaction_id'), int):
        return jsonify({
            'state': 'error',
            'error': 'No transaction_id or it is not number'
        }), 422

    if not data.get('code') or not isinstance(data.get('code'), int):
        return jsonify({
            'state': 'error',
            'error': 'No code or it is not number'
        }), 422

    transaction = get_transaction(data.get('transaction_id'))

    if not transaction:
        return jsonify({
            'state': 'error',
            'error': 'Transaction not found'
        }), 404

    if transaction.status == 'done':
        return jsonify({
            'state': 'error',
            'error': 'Transaction is finished'
        }), 403

    if transaction.status == 'banned':
        return jsonify({
            'state': 'error',
            'error': 'Transaction is banned, try to make a new transaction'
        }), 403

    if transaction.status == 'cancelled':
        return jsonify({
            'state': 'error',
            'error': 'Transaction is cancelled, try to make a new transaction'
        }), 403

    if transaction.code != data.get('code'):
        transaction.tries += 1

        if transaction.tries > 2:
            transaction.status = 'banned'

        db.session.commit()

        return jsonify({
            'state': 'error',
            'error': 'Code is incorrect'
        }), 403

    if transaction.sender_account.balance() < transaction.amount:
        transaction.status = 'cancelled'
        db.session.commit()

        return jsonify({
            'state': 'error',
            'error': 'Insufficient funds'
        }), 422

    transaction.status = 'done'
    bot.send_message(transaction.sender_account.telegram_id, "Списание {} gt: {}".format(transaction.amount, transaction.description))
    bot.send_message(transaction.sender_account.telegram_id, "Зачисление {} gt со счета {}: {}".format(transaction.amount, transaction.sender_account.telegram_id, transaction.description))

    db.session.commit()

    return jsonify({
        'state': 'success',
    }), 200


if __name__ == "__main__":
    app.run(HOST, PORT, debug=PRODUCTION)
