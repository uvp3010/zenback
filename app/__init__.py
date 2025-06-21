from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_session import Session
from dotenv import load_dotenv
import os

db = SQLAlchemy()
sess = Session()


def create_app():
    load_dotenv()

    app = Flask(__name__)
    app.config.from_object('app.config.Config')

    # Fix CORS origin — allow both local & Vercel
    CORS(app, supports_credentials=True, resources={r"/*": {
        "origins": [
            "http://localhost:5173",
            "https://zen-llmbxsl83-uvp3010s-projects.vercel.app"
        ]
    }})

    sess.init_app(app)
    db.init_app(app)

    # Ensure audio folder exists
    os.makedirs(app.config["AUDIO_FOLDER"], exist_ok=True)

    # Register routes
    from app.routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    with app.app_context():
        from app import models
        db.create_all()

        # Task seeding (optional: only in dev)
        from app.models import Task
        if not Task.query.first():
            sample_tasks = [
                Task(title="Guided Breathing", description="Practice mindful breathing.", type="mindfulBreathing",
                     badge="Breath Badge"),
                Task(title="Gratitude Journaling", description="Write down three things.", type="gratitudeJournaling",
                     badge="Gratitude Badge"),
                Task(title="PMR", description="Do muscle relaxation.", type="pmr", badge="Relaxation Badge"),
                Task(title="Physical Activity", description="Take a 10-minute walk.", type="text",
                     badge="Activity Badge")
            ]
            db.session.bulk_save_objects(sample_tasks)
            db.session.commit()

    return app
