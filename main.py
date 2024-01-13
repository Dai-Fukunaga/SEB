from flask import Flask, request, jsonify, render_template, redirect
from models import db, Reservation, Space, User, WaitingQueue
from datetime import datetime
import logging

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reservations.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

#for logging
logging.basicConfig(level=logging.DEBUG)


def update_waiting_ids():
    waitings = WaitingQueue.query.order_by(WaitingQueue.queue_position).all()
    for i, waiting in enumerate(waitings, start=1):
        waiting.queue_position = i
    db.session.commit()

@app.route('/')
def index():
    spaces = Space.query.all()
    error = request.args.get('error')
    return render_template('index.html', spaces=spaces, error=error)

def create_sample_spaces():
    # List of sample spaces
    sample_spaces = [
        {'name': 'ルーム１', 'description': '勉強できそうなばしょ'},
        {'name': '会議室', 'description': '３０人くらい入りそう/プロジェクター有り'},
        {'name': '教室', 'description': 'イベントとか授業が行えそうな場所'},
        # Add more sample spaces as needed
    ]

    # Check if the spaces already exist to avoid duplicates
    existing_space_names = {space.name for space in Space.query.all()}
    for space in sample_spaces:
        if space['name'] not in existing_space_names:
            new_space = Space(name=space['name'], description=space['description'])
            db.session.add(new_space)

    db.session.commit()

@app.route('/reserve', methods=['POST'])
def create_reservation():
    user_id = request.form['user_id']
    space_id = request.form['space_id']
    start_time = datetime.strptime(request.form['start_time'], "%Y-%m-%dT%H:%M")
    end_time = datetime.strptime(request.form['end_time'], "%Y-%m-%dT%H:%M")

    # Check if the end_time is after the start_time
    if end_time <= start_time:
        return redirect('/?error=The end time must be after the start time.')

    # Check if the space is already reserved for the given time
    overlapping_reservations = Reservation.query.filter(
        Reservation.space_id == space_id,
        Reservation.end_time > start_time,
        Reservation.start_time < end_time
    ).all()

    if overlapping_reservations:
        return render_template('join_waiting_list.html', space_id=space_id, user_id=user_id, start_time=start_time, end_time=end_time)

    new_reservation = Reservation(user_id=user_id, space_id=space_id, start_time=start_time, end_time=end_time)
    db.session.add(new_reservation)
    db.session.commit()

    # Render a template for successful reservation
    return render_template('reservation_success.html', reservation_id=new_reservation.id, space_id=space_id)

@app.route('/cancel', methods=['GET', 'POST'])
def cancel_reservation():
    if request.method == 'POST':
        reservation_id = request.form.get('reservation_id')
        waiting_id = request.form.get('waiting_id')

        if reservation_id:
            reservation = Reservation.query.get(reservation_id)
            if reservation:
                space_id = reservation.space_id
                db.session.delete(reservation)
                db.session.commit()

                # Check if there are any waitings for the space of the cancelled reservation
                waiting = WaitingQueue.query.filter_by(space_id=space_id).order_by(WaitingQueue.timestamp).first()
                if waiting:
                    # Create a new reservation for the user who has been waiting the longest
                    new_reservation = Reservation(user_id=waiting.user_id, space_id=space_id, start_time=waiting.start_time, end_time=waiting.end_time)
                    db.session.add(new_reservation)
                    db.session.delete(waiting)
                    db.session.commit()
                    update_waiting_ids()  # Update the queue_position of all remaining waitings

                return """
                <html>
                <head>
                    <meta http-equiv="refresh" content="3; url=/cancel?user_id={}" />
                </head>
                <body>
                    <p>Reservation cancelled successfully. Redirecting in 3 seconds...</p>
                </body>
                </html>
                """.format(reservation.user_id)
            else:
                return "Reservation not found."
        elif waiting_id:
            waiting = WaitingQueue.query.get(waiting_id)
            if waiting:
                db.session.delete(waiting)
                db.session.commit()
                update_waiting_ids()  # Update the queue_position of all remaining waitings
                return """
                <html>
                <head>
                    <meta http-equiv="refresh" content="3; url=/cancel?user_id={}" />
                </head>
                <body>
                    <p>Waiting cancelled successfully. Redirecting in 3 seconds...</p>
                </body>
                </html>
                """.format(waiting.user_id)
            else:
                return "Waiting not found."
    else:
        user_id = request.args.get('user_id')
        reservations = Reservation.query.filter_by(user_id=user_id).all()
        waiting_list = WaitingQueue.query.filter_by(user_id=user_id).all()
        return render_template('cancel.html', reservations=reservations, waiting_list=waiting_list)

@app.route('/cancel_waiting', methods=['POST'])
def cancel_waiting():
    waiting_id = request.form.get('waiting_id')
    waiting = WaitingQueue.query.get(waiting_id)
    if waiting:
        db.session.delete(waiting)
        db.session.commit()
        update_waiting_ids()  # Update the queue_position of all remaining waitings
        return """
        <html>
        <head>
            <meta http-equiv="refresh" content="5; url=/cancel?user_id={}" />
        </head>
        <body>
            <p>Waiting cancelled successfully. Redirecting in 5 seconds...</p>
        </body
        </html>
        """.format(waiting.user_id)
    else:
        return "Waiting not found."

@app.route('/join_waiting_list', methods=['POST'])
def join_waiting_list():
    user_id = request.form['user_id']
    space_id = request.form['space_id']
    start_time = datetime.strptime(request.form['start_time'], "%Y-%m-%d %H:%M:%S")
    end_time = datetime.strptime(request.form['end_time'], "%Y-%m-%d %H:%M:%S")

    max_position = db.session.query(db.func.max(WaitingQueue.queue_position)).scalar() or 0
    waiting_queue = WaitingQueue(user_id=user_id, space_id=space_id, start_time=start_time, end_time=end_time, queue_position=max_position+1)
    db.session.add(waiting_queue)
    db.session.commit()

    return redirect(f'/cancel?user_id={user_id}')
@app.route('/waiting_list/<int:space_id>')
def waiting_list(space_id):
    waiting_queue = WaitingQueue.query.filter_by(space_id=space_id).order_by(WaitingQueue.timestamp).all()
    return render_template('waiting_list.html', waiting_queue=waiting_queue)

@app.route('/spaces', methods=['GET'])
def list_spaces():
    spaces = Space.query.all()
    return jsonify([{'id': space.id, 'name': space.name, 'description': space.description} for space in spaces])


@app.route('/calendar/<int:space_id>')
def calendar(space_id):
    reservations = Reservation.query.filter_by(space_id=space_id).all()
    space = Space.query.get(space_id)
    app.logger.info("reservations: %s", reservations)
    return render_template('calendar.html', reservations=reservations, space=space)

@app.route("/video")
def video():
    return render_template("video.html")

with app.app_context():
    db.drop_all()  # Drops all tables only for dev use
    db.create_all()# Creates the database tables if they don't exist
    create_sample_spaces()# Add sample spaces to the database

if __name__ == '__main__':
    app.run(debug=True)
