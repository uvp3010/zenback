from app import db
from datetime import datetime


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(80), nullable=False)
    avatar = db.Column(db.String(300), nullable=True, default='/avatars/default.jpg')

    def __repr__(self):
        return f'<User {self.username}>'


class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f'<Appointment {self.date}>'


class Assessment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    responses = db.Column(db.String, nullable=True)  # JSON string containing responses
    result = db.Column(db.String(150), nullable=False)

    def __repr__(self):
        return f'<Assessment {self.id} for user {self.user_id}>'


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(250), nullable=True)
    type = db.Column(db.String(50), nullable=False)  # e.g., "mindfulBreathing", "gratitudeJournaling", etc.
    badge = db.Column(db.String(50), nullable=True)

    def __repr__(self):
        return f'<Task {self.title}>'


class TaskCompletion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    completion_date = db.Column(db.Date, nullable=False, default=lambda: datetime.utcnow().date())
    badge = db.Column(db.String(50), nullable=True)
    __table_args__ = (db.UniqueConstraint('user_id', 'task_id', 'completion_date', name='_user_task_date_uc'),)


class Prediction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    text = db.Column(db.Text, nullable=False)
    prediction = db.Column(db.String(150), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Prediction {self.id} for user {self.user_id}>'


# Only run the following code if this file is executed directly.
if __name__ == "__main__":
    # Import your app instance from your run file or app module.
    from app import app  # Adjust this import if needed

    with app.app_context():
        # Create the tables (if they don't exist already)
        db.create_all()

        # Insert sample tasks if the Task table is empty.
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
                ),
                Task(
                    title="",
                    description="Practice mindful breathing for 5 minutes.",
                    type="mindfulBrea",
                    badge="Breath Badge"
                ),
            ]

            for task in sample_tasks:
                db.session.add(task)
            db.session.commit()
            print("Sample tasks inserted!")

