from flask import Flask, render_template
from models import db, Reservation
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reservations.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
migrate = Migrate(app, db)

@app.route('/')
def index():
    return render_template('index.html')

# Include your other routes here (reserve, availability, etc.)

if __name__ == '__main__':
    app.run(debug=True)
