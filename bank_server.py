import random
import telebot
from init import *
from helpers import *
from models import *
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
import markdown2

auth = HTTPBasicAuth()
app = create_app()
bot = telebot.TeleBot(TELEGRAM_TOKEN)
admin = generate_password_hash(ADMIN_PASSWORD)


def get_account_by_token(token):
    return Account.query.filter_by(trading_token=token).first()


def get_account(chat_id):
    return Account.query.filter_by(telegram_id=chat_id).first()


def get_transaction(transaction_id):
    return Transaction.query.filter_by(id=transaction_id).first()


@auth.verify_password
def verify_password(username, password):
    if check_password_hash(admin, password):
        return username


@app.route('/', methods=['GET'])
def index():
    with open('docs.md', 'r') as docs:
        html = markdown2.markdown(docs.read(), extras=["fenced-code-blocks", "break-on-newline", "tables"])
    return render_template('index.html', docs=html)

@app.route('/admin', methods=['POST', 'GET'])
@auth.login_required
def admin_panel():
    done_list = []
    undone_list = []

    task = ""
    description = ""
    if request.method == 'POST':
        description = request.form.get('description')
        task = request.form.get('list')
        data = task.split('\n')
        data = list(map(lambda x: x.split('	'), data))
        is_run = request.form.get('action') == 'Начислить'

        try:
            for line in data:
                surname, name = line[0][:line[0].find(' ')], line[0][line[0].find(' ') + 1:]
                amount = int(line[1])

                receiver_account = Account.query.filter_by(name=name, surname=surname).first()

                if receiver_account:
                    done_list.append(line)

                    if is_run:
                        transaction = Transaction(to_id=receiver_account.id,
                                                  description=description,
                                                  amount=amount,
                                                  status='done',
                                                  type='grant')
                        db.session.add(transaction)
                        bot.send_message(receiver_account.telegram_id,
                                         "Зачисление {} gt: {}".format(transaction.amount, transaction.description))
                else:
                    undone_list.append(line)
        except Exception as e:
            return str(e)

        db.session.commit()

    return render_template('admin.html', done_list=done_list, undone_list=undone_list, task=task, description=description)


@app.route('/debug-sentry')
def trigger_error():
    try:
        division_by_zero = 1 / 0
    except Exception as e:
        log(e, True)
        abort(500)


@app.route('/api/send', methods=['POST'])
def send_money():
    data = request.json

    if not data:
        return jsonify({
            'state': 'error',
            'error': 'No data'
        }), 422

    rules = [
        ['token', str, 'No trading token'],
        ['description', str, 'No description'],
        ['account_id', int, 'No account id or it is not number'],
        ['amount', (int, float), 'No amount or it is not number or lower than 1'],
    ]

    correct, error = validate(data, rules)
    if not correct:
        return jsonify({
            'state': 'error',
            'error': error
        }), 422

    sender_account = get_account_by_token(data.get('token'))

    if not sender_account:
        return jsonify({
            'state': 'error',
            'error': 'Incorrect trading token'
        }), 403

    receiver_account = get_account(data.get('account_id'))

    if not receiver_account:
        return jsonify({
            'state': 'error',
            'error': 'Wrong account_id'
        }), 404

    if sender_account.balance() < data.get('amount') * 1.03:
        return jsonify({
            'state': 'error',
            'error': 'Insufficient funds'
        }), 422

    transaction = Transaction(from_id=sender_account.id,
                              to_id=receiver_account.id,
                              description=data.get('description'),
                              amount=data.get('amount'),
                              status='done',
                              code=None,
                              type='transfer')
    db.session.add(transaction)
    db.session.commit()

    commission = Transaction(from_id=sender_account.id,
                             to_id=None,
                             description="Коммиссия за транзакцию ID {}".format(transaction.id),
                             amount=data.get('amount') * 0.03,
                             status='done',
                             code=None,
                             type='commission')

    db.session.add(commission)
    db.session.commit()

    return jsonify({
        'state': 'success',
    }), 200


@app.route('/api/ask', methods=['POST'])
def ask_money():
    data = request.json

    if not data:
        return jsonify({
            'state': 'error',
            'error': 'No data'
        }), 422

    rules = [
        ['token', str, 'No trading token'],
        ['description', str, 'No description'],
        ['account_id', int, 'No account id or it is not number'],
        ['amount', (int, float), 'No amount or it is not number or lower than 1'],
    ]

    correct, error = validate(data, rules)
    if not correct:
        return jsonify({
            'state': 'error',
            'error': error
        }), 422

    receiver_account = get_account_by_token(data.get('token'))
    sender_account = get_account(data.get('account_id'))

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

    if not sender_account:
        return jsonify({
            'state': 'error',
            'error': 'Wrong account_id'
        }), 404

    if sender_account.balance() < data.get('amount'):
        return jsonify({
            'state': 'error',
            'error': 'Insufficient funds of sender'
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

    bot.send_message(sender_account.telegram_id,
                     "Запрос {} gt: {}\n\nКод подтверждения: {}".format(transaction.amount, transaction.description,
                                                                        transaction.code))

    return jsonify({
        'state': 'success',
        'transaction_id': transaction.id
    }), 200


@app.route('/api/verify', methods=['POST'])
def verify_transaction():
    data = request.json

    if not data:
        return jsonify({
            'state': 'error',
            'error': 'No data'
        }), 422

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
    bot.send_message(transaction.sender_account.telegram_id,
                     "Списание {} gt: {}".format(transaction.amount, transaction.description))
    bot.send_message(transaction.sender_account.telegram_id,
                     "Зачисление {} gt со счета {}: {}".format(transaction.amount,
                                                               transaction.sender_account.telegram_id,
                                                               transaction.description))
    commission = Transaction(from_id=transaction.receiver_account.id,
                             to_id=None,
                             description="Коммиссия за транзакцию ID {}".format(transaction.id),
                             amount=transaction.amount * 0.03,
                             status='done',
                             code=None,
                             type='commission')

    db.session.add(commission)
    db.session.commit()

    return jsonify({
        'state': 'success',
    }), 200


if __name__ == "__main__":
    app.run(HOST, PORT, debug=not PRODUCTION)
