from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_session import Session
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config.from_object('app.config.Config')

# Enable CORS for the specified origin (adjust as needed)
CORS(app, supports_credentials=True, resources={r"/*": {"origins": "http://localhost:5173"}})
Session(app)

# Initialize the SQLAlchemy database
db = SQLAlchemy(app)

# Create the audio folder if it does not exist
os.makedirs(app.config["AUDIO_FOLDER"], exist_ok=True)

# Import and register blueprints
from app.routes import main as main_blueprint
app.register_blueprint(main_blueprint)

# Import models so that tables are created
from app import models

with app.app_context():
    db.create_all()

    # Import the Task model
    from app.models import Task

    # Seed sample tasks if the Task table is empty
    if not Task.query.first():
        sample_tasks = [
            Task(
                title="Guided Breathing",
                description="Practice mindful breathing for 5 minutes.",
                type="mindfulBreathing",
                badge="Breath Badge"
            ),
            Task(
                title="Gratitude Journaling",
                description="Write down three things you're grateful for.",
                type="gratitudeJournaling",
                badge="Gratitude Badge"
            ),
            Task(
                title="Progressive Muscle Relaxation",
                description="Follow a guided progressive muscle relaxation exercise.",
                type="pmr",
                badge="Relaxation Badge"
            ),
            Task(
                title="Physical Activity",
                description="Take a brisk 10-minute walk.",
                type="text",
                badge="Activity Badge"
            )
        ]
        for task in sample_tasks:
            db.session.add(task)
        db.session.commit()
        print("Sample tasks inserted!")

