import time
from datetime import datetime
from functools import reduce

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import backref, relationship

db = SQLAlchemy()


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    from_id = db.Column(db.Integer, db.ForeignKey('account.id', ondelete="SET NULL"), nullable=True)
    to_id = db.Column(db.Integer, db.ForeignKey('account.id', ondelete="SET NULL"), nullable=True)
    amount = db.Column(db.Float)
    type = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(255), nullable=True)
    code = db.Column(db.Integer, nullable=True)
    description = db.Column(db.Text, nullable=True)
    created_on = db.Column(db.DateTime, server_default=db.func.now())
    tries = db.Column(db.Integer, default=0)


class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=True)
    surname = db.Column(db.String(255), nullable=True)
    telegram_id = db.Column(db.Integer, nullable=True)
    created_on = db.Column(db.DateTime, server_default=db.func.now())
    trading_enabled = db.Column(db.Boolean, default=True)
    trading_token = db.Column(db.String(255), nullable=True)

    incoming_transactions = db.relationship('Transaction', foreign_keys='Transaction.to_id', backref=backref('receiver_account', uselist=False), lazy=True)
    outcoming_transactions = db.relationship('Transaction', foreign_keys='Transaction.from_id', backref=backref('sender_account', uselist=False), lazy=True)

    def done_incoming_transactions(self):
        return Transaction.query.filter_by(to_id=self.id, status="done").all()

    def done_outcoming_transactions(self):
        return Transaction.query.filter_by(from_id=self.id, status="done").all()

    def balance(self):
        transactions = list(map(lambda x:x.amount, self.done_incoming_transactions())) + list(map(lambda x: -1 * x.amount, self.done_outcoming_transactions()))
        return round(reduce(lambda s, t: s + t, transactions, 0), 2)
