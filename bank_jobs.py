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
                                  filter(lambda x: x.created_on.date() == datetime.now().date(), transactions), 0)

            cashback = min(today_amount, DAILY_PRICE) * CASHBACK
            fact_price = max(0, DAILY_PRICE - today_amount)

            if fact_price:
                transaction = Transaction(from_id=account.id,
                                          description="Оплата участия в кластере",
                                          amount=DAILY_PRICE,
                                          status='done',
                                          type='daily')
                db.session.add(transaction)

                bot.send_message(account.telegram_id, "Списание {} gt за участие в акселераторе".format(transaction.amount))

            if cashback:
                transaction = Transaction(to_id=account.id,
                                          description="cashback",
                                          amount=cashback,
                                          status='done',
                                          type='cashback')
                db.session.add(transaction)

                bot.send_message(account.telegram_id,
                                 "Начислено кэшбека {} gt".format(cashback))
        db.session.commit()


if __name__ == "__main__":
    scheduler = BlockingScheduler()
    scheduler.add_job(pay, 'cron', hour=20, minute=55, second=0, args=(app,))
    scheduler.start()
