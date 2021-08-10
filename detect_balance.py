from bank_server import app
from models import Account

with app.app_context():
    for account in sorted(Account.query.all(), key=lambda x: x.balance()):
        print("{} {} - {}".format(account.name, account.surname, account.balance()))
