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
    amount = db.Column(db.Integer)
    type = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(255), nullable=True)
    code = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    created_on = db.Column(db.DateTime, server_default=db.func.now())


class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=True)
    surname = db.Column(db.String(255), nullable=True)
    telegram_id = db.Column(db.Integer, nullable=True)
    created_on = db.Column(db.DateTime, server_default=db.func.now())

    incoming_transactions = db.relationship('Transaction', foreign_keys='Transaction.to_id', backref=backref('to_account', uselist=False), lazy=True)
    outcoming_transactions = db.relationship('Transaction', foreign_keys='Transaction.from_id', backref=backref('from_account', uselist=False), lazy=True)

    def balance(self):
        transactions = map(lambda x:x.amount, self.incoming_transactions) +  map(lambda x: -1 * x.amount, self.outcoming_transactions)
        return reduce(lambda s, t: s + t, transactions, 0)
