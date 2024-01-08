# models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Space(db.Model):
    __tablename__ = 'spaces'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(200))
    # Additional fields like location, capacity, etc. can be added here

    def __init__(self, name, description):
        self.name = name
        self.description = description

    def __repr__(self):
        return f"<Space {self.name}>"

class Reservation(db.Model):
    __tablename__ = 'reservations'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    space_id = db.Column(db.Integer, db.ForeignKey('spaces.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)

    def __init__(self, user_id, space_id, start_time, end_time):
        self.user_id = user_id
        self.space_id = space_id
        self.start_time = start_time
        self.end_time = end_time

    def __repr__(self):
        return f"<Reservation for space {self.space_id} by user {self.user_id} from {self.start_time} to {self.end_time}>"

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    # Passwords should be hashed! Consider using Flask-Bcrypt or similar
    password_hash = db.Column(db.String(128))

    def __init__(self, name, email, password_hash):
        self.name = name
        self.email = email
        self.password_hash = password_hash

    def __repr__(self):
        return f"<User {self.name}>"
