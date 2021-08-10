from bank_server import app
from models import Account

with app.app_context():
    for account in Account.query.all():
        print("{} {} - {}".format(account.name, account.surname, account.balance()))
