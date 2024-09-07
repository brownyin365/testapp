from flask import Flask, render_template, request, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Replace with your secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'
db = SQLAlchemy(app)

class BonusTask(db.Model):
    __tablename__ = 'bonus_task'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    country = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    bonus = db.Column(db.Float, nullable=False)

    def __init__(self, user_id, country, age, bonus):
        self.user_id = user_id
        self.country = country
        self.age = age
        self.bonus = bonus

# Create database tables
with app.app_context():
    db.create_all()
