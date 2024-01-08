from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from models import db, Reservation, Space, User
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reservations.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

@app.route('/')
def index():
    return "ay yo wassuo"

@app.route('/reserve', methods=['POST'])
def create_reservation():
    data = request.json
    new_reservation = Reservation(
        user_id=data['user_id'],
        space_id=data['space_id'],
        start_time=datetime.strptime(data['start_time'], "%Y-%m-%d %H:%M"),
        end_time=datetime.strptime(data['end_time'], "%Y-%m-%d %H:%M")
    )
    db.session.add(new_reservation)
    db.session.commit()
    return jsonify(new_reservation.id), 201

@app.route('/spaces', methods=['GET'])
def list_spaces():
    spaces = Space.query.all()
    return jsonify([{'id': space.id, 'name': space.name, 'description': space.description} for space in spaces])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Creates the database tables
    app.run(debug=True)
