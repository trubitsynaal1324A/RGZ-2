from . import db
from flask_login import UserMixin
from sqlalchemy.orm import relationship
from datetime import datetime

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return f'id: {self.id}, username: {self.username}'

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    article = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(30), nullable=False)
    opisanie = db.Column(db.String(256))
    price = db.Column(db.Numeric, nullable=False)
    kolvo = db.Column(db.Integer, nullable=False, default=1)