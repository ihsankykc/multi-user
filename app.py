from flask import Flask, render_template, request, redirect, session
from flask import url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import calendar
from werkzeug.security import generate_password_hash, check_password_hash

events = {}


app = Flask(__name__)
app.secret_key = 'room_temperature'

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///multiuser_calendar.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    password = db.Column(db.String(120), nullable=False)

# Event model
class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.String(10), nullable=False)  # Format: YYYY-MM-DD
    event_text = db.Column(db.String(255), nullable=False)

# Create the database tables
with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])

        # Check if user already exists
        if User.query.filter_by(username=username).first():
            return "Username already exists!"

        # Add new user
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Authenticate user
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('main_page'))
        else:
            return "Invalid credentials!"
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/hello')
@login_required
def main_page():
    
    return render_template('index.html',
                             )

@app.route('/calendar', methods=['GET', 'POST'])
@login_required
def calendar_page():
    today = datetime.today()
    year = request.args.get('year', today.year, type=int)
    month = request.args.get('month', today.month, type=int)

    # Generate the calendar
    cal = calendar.Calendar()
    month_days = cal.monthdayscalendar(year, month)

    # Get events for the current user and month
    date_prefix = f"{year}-{month:02d}"
    user_events = Event.query.filter(
        Event.user_id == current_user.id,
        Event.date.like(f"{date_prefix}-%")
    ).all()

    # Convert events into a dictionary keyed by day
    events = {}
    for event in user_events:
        day = event.date.split('-')[-1]  # Extract the day part
        if day not in events:
            events[day] = []
        events[day].append(event.event_text)

    return render_template('calendar.html', year=year, month=month, month_days=month_days, events=events)



@app.route('/add_event', methods=['POST'])
@login_required
def add_event():
    year = request.form['year']
    month = request.form['month']
    day = request.form['day']
    event_text = request.form['event']

    # Store the event for the logged-in user
    date = f"{year}-{month}-{day}"
    new_event = Event(user_id=current_user.id, date=date, event_text=event_text)
    db.session.add(new_event)
    db.session.commit()

    return redirect(url_for('calendar_page', year=year, month=month))

app.run(host='0.0.0.0', port=5000, debug=True)
