from init import *
from models import *
from datetime import datetime
from apscheduler.schedulers.background import BlockingScheduler
import telebot

app = create_app()
bot = telebot.TeleBot(TELEGRAM_TOKEN)


def pay(app):
    print('daily start')
    with app.app_context():
        for account in Account.query.all():
            transactions = Transaction.query.filter_by(from_id=account.id, type='trade', status='done').all()
            today_amount = reduce(lambda a, b: a + b.amount,
                                  filter(lambda x: x.created_on > datetime.now().date(), transactions), 0)

            cashback = min(today_amount, DAILY_PRICE) * CASHBACK
            transaction = Transaction(from_id=account.id,
                                      to_id=None,
                                      description="Оплата участия в кластере",
                                      amount=DAILY_PRICE,
                                      status='done',
                                      code=None,
                                      type='daily')
            db.session.add(transaction)

            bot.send_message(account.telegram_id,
                             "Списание {} gt за участие в акселераторе".format(transaction.amount))

            if cashback:
                transaction = Transaction(from_id=None,
                                          to_id=account.id,
                                          description="cashback",
                                          amount=cashback,
                                          status='done',
                                          code=None,
                                          type='cashback')
                db.session.add(transaction)

                bot.send_message(account.telegram_id,
                                 "Начислено кэшбека {} gt".format(cashback))
        db.session.commit()


scheduler = BlockingScheduler()
scheduler.add_job(pay, 'cron', hour=22, minute=53, second=0, args=(app,))
scheduler.start()
