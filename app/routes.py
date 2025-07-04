
import json
from datetime import datetime
import nltk
import pickle
import numpy as np
from scipy.sparse import hstack
from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from twilio.rest import Client

from app import db, app
from app.models import User, Appointment, Assessment, Task, TaskCompletion, Prediction
from app.utils import preprocess_text, generate_response
import os
nltk.download('punkt')
# Load Twilio configuration from app.config
TWILIO_ACCOUNT_SID = app.config.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = app.config.get('TWILIO_AUTH_TOKEN')
TWILIO_WHATSAPP_NUMBER = app.config.get('TWILIO_WHATSAPP_NUMBER')

clients = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Define the path to the ML models directory
ML_MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'ml_models')

# Load the machine learning models and related assets
with open(os.path.join(ML_MODELS_DIR, 'logistic_regression_model.pkl'), 'rb') as f:
    model = pickle.load(f)
with open(os.path.join(ML_MODELS_DIR, 'tfidf_vectorizer.pkl'), 'rb') as f:
    vectorizer = pickle.load(f)
with open(os.path.join(ML_MODELS_DIR, 'label_encoder.pkl'), 'rb') as f:
    label_encoder = pickle.load(f)

# Create a blueprint for all routes
main = Blueprint('main', __name__)

@main.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "")
    response = generate_response(user_message)
    return jsonify({"response": response})

@main.route('/send-whatsapp', methods=['POST'])
def send_whatsapp():
    if 'user_id' not in session:
        return jsonify({'message': 'Unauthorized'}), 401

    data = request.get_json()
    doctor_number = data.get('doctor_number')
    message_content = data.get('message')
    user = User.query.get(session['user_id'])
    username = user.username if user else "Unknown User"
    message_to_send = f"New appointment booked by {username} for {message_content}."
    try:
        clients.messages.create(
            body=message_to_send,
            from_=TWILIO_WHATSAPP_NUMBER,
            to=f'whatsapp:{doctor_number}'
        )
        return jsonify({'message': 'WhatsApp message sent successfully'}), 200
    except Exception as e:
        return jsonify({'message': f'Failed to send WhatsApp message: {str(e)}'}), 500

@main.route('/predict', methods=['POST'])
def predict():
    data = request.get_json(force=True)
    input_text = data.get('text', '')
    if not input_text:
        return jsonify({'error': 'No text provided'}), 400

    processed_text = preprocess_text(input_text)
    tfidf_features = vectorizer.transform([processed_text])
    num_of_characters = len(input_text)
    num_of_sentences = len(nltk.sent_tokenize(input_text))
    num_features = np.array([[num_of_characters, num_of_sentences]])
    combined_features = hstack([tfidf_features, num_features])
    prediction_encoded = model.predict(combined_features)
    prediction_result = label_encoder.inverse_transform(prediction_encoded)[0]

    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])

    new_prediction = Prediction(
        user_id=user.id if user else None,
        text=input_text,
        prediction=prediction_result
    )
    db.session.add(new_prediction)
    db.session.commit()

    return jsonify({'prediction': prediction_result})

@main.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    age = data.get('age')
    email = data.get('email')
    gender = data.get('gender')

    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'Username already exists'}), 400

    if User.query.filter_by(email=email).first():  # 👈 New check
        return jsonify({'message': 'Email already registered'}), 400

    hashed_password = generate_password_hash(password)
    new_user = User(
        username=username,
        password=hashed_password,
        email=email,
        age=age,
        gender=gender
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User registered successfully'}), 201


@main.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password, password):
        session['user_id'] = user.id
        session['username'] = user.username
        return jsonify({'message': 'Login successful', 'username': user.username}), 200
    else:
        return jsonify({'message': 'Invalid credentials'}), 401

@main.route('/schedule', methods=['POST'])
def schedule_appointment():
    if 'user_id' not in session:
        return jsonify({'message': 'Unauthorized'}), 401
    data = request.get_json()
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'message': 'User not found'}), 404
    try:
        date = datetime.strptime(data.get('date'), '%Y-%m-%d')
        new_appointment = Appointment(user_id=user.id, date=date)
        db.session.add(new_appointment)
        db.session.commit()
        return jsonify({'message': 'Appointment scheduled successfully'}), 201
    except ValueError:
        return jsonify({'message': 'Invalid date format'}), 400

@main.route('/update-profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return jsonify({'message': 'Unauthorized'}), 401
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'message': 'User not found'}), 404
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    age = data.get('age')
    gender = data.get('gender')
    avatar = data.get('avatar')

    if username:
        user.username = username
    if email:
        user.email = email
    if age:
        user.age = age
    if gender:
        user.gender = gender
    if avatar is not None:
        user.avatar = avatar

    db.session.commit()
    return jsonify({
        'message': 'Profile updated successfully',
        'user': {
            'username': user.username,
            'email': user.email,
            'age': user.age,
            'gender': user.gender,
            'avatar': user.avatar
        }
    }), 200

@main.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return jsonify({'message': 'Logged out successfully'}), 200

@main.route('/dashboard', methods=['GET'])
def dashboard():
    if 'user_id' not in session:
        return jsonify({'message': 'Unauthorized'}), 401
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'message': 'User not found'}), 404

    appointments = Appointment.query.filter(
        Appointment.user_id == user.id,
        Appointment.date >= datetime.utcnow()
    ).all()
    appointments_list = [{'id': appt.id, 'date': appt.date.isoformat()} for appt in appointments]

    today = datetime.utcnow().date()
    tasks = Task.query.filter(Task.type != "achievement").all()
    tasks_list = []
    for task in tasks:
        completion = TaskCompletion.query.filter_by(user_id=user.id, task_id=task.id, completion_date=today).first()
        tasks_list.append({
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'completed': True if completion else False,
            'badge': completion.badge if completion else task.badge
        })

    assessments = Assessment.query.filter_by(user_id=user.id).all()
    assessments_list = [{
        'id': assessment.id,
        'date': assessment.date.isoformat(),
        'score': assessment.score,
        'result': assessment.result,
        'responses': json.loads(assessment.responses)
    } for assessment in assessments]

    predictions = Prediction.query.filter_by(user_id=user.id).order_by(Prediction.created_at.asc()).all()
    predictions_list = [{
        'id': p.id,
        'text': p.text,
        'prediction': p.prediction,
        'date': p.created_at.isoformat()
    } for p in predictions]

    achievement_completions = TaskCompletion.query.filter_by(user_id=user.id, completion_date=today)\
                            .join(Task, Task.id == TaskCompletion.task_id)\
                            .filter(Task.type == "achievement").all()
    achievements_list = [{
        'badge': ac.badge,
        'date': ac.completion_date.isoformat()
    } for ac in achievement_completions]

    latestPrediction = predictions_list[-1]['prediction'] if predictions_list else None

    if assessments:
        latestScore = assessments[-1].score
        avgScore = sum(a.score for a in assessments if a.score is not None) / len(assessments)
        assessmentCount = len(assessments)
    else:
        latestScore = None
        avgScore = None
        assessmentCount = 0

    dashboard_data = {
        'user': {
            'username': user.username,
            'email': user.email,
            'age': user.age,
            'gender': user.gender,
            'avatar': user.avatar
        },
        'appointments': appointments_list,
        'tasks': tasks_list,
        'assessments': assessments_list,
        'predictions': predictions_list,
        'achievements': achievements_list,
        'latestScore': latestScore,
        'avgScore': avgScore,
        'assessmentCount': assessmentCount,
        'latestPrediction': latestPrediction,
        'moodCalendar': []
    }
    return jsonify(dashboard_data), 200

@main.route('/save-assessment', methods=['POST'])
def save_assessment():
    if 'user_id' not in session:
        return jsonify({'message': 'Unauthorized'}), 401
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'message': 'User not found'}), 404
    data = request.get_json()
    score = data.get('score')
    result = data.get('result')
    responses = json.dumps(data.get('responses', {}))
    if isinstance(result, dict):
        result = json.dumps(result)
    new_assessment = Assessment(
        user_id=user.id,
        score=score,
        result=result,
        responses=responses
    )
    db.session.add(new_assessment)
    db.session.commit()
    return jsonify({'message': 'Assessment saved successfully'}), 201

@main.route('/get-assessments', methods=['GET'])
def get_assessments():
    if 'user_id' not in session:
        return jsonify({'message': 'Unauthorized'}), 401
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'message': 'User not found'}), 404
    assessments = Assessment.query.filter_by(user_id=user.id).all()
    assessments_list = [{
        'id': assessment.id,
        'date': assessment.date.isoformat(),
        'score': assessment.score,
        'result': assessment.result,
        'responses': json.loads(assessment.responses)
    } for assessment in assessments]
    return jsonify(assessments_list), 200

@main.route('/progress-tracking', methods=['GET'])
def progress_tracking():
    if 'user_id' not in session:
        return jsonify({'message': 'Unauthorized'}), 401
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'message': 'User not found'}), 404

    assessments = Assessment.query.filter_by(user_id=user.id).order_by(Assessment.date.asc()).all()
    total = len(assessments)
    if total > 0:
        avg_score = sum(a.score for a in assessments) / total
        worst = max(a.score for a in assessments)
        best = min(a.score for a in assessments)
        timeline = [{'date': a.date.isoformat(), 'score': a.score} for a in assessments]
    else:
        avg_score = worst = best = 0
        timeline = []

    completions = TaskCompletion.query.filter_by(user_id=user.id).all()
    badges = list({completion.badge for completion in completions if completion.badge})
    achievement_badges = [ac.badge for ac in completions if ac.badge == "Wellness Achiever Badge"]

    return jsonify({
        'totalAssessments': total,
        'averageScore': avg_score,
        'bestScore': best,
        'worstScore': worst,
        'timeline': timeline,
        'badges': badges,
        'achievements': achievement_badges
    }), 200

@main.route('/tasks', methods=['GET'])
def get_tasks():
    if 'user_id' not in session:
        return jsonify({'message': 'Unauthorized'}), 401
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'message': 'User not found'}), 404
    today = datetime.utcnow().date()
    tasks = Task.query.filter(Task.type != "achievement").all()
    tasks_list = []
    for task in tasks:
        completion = TaskCompletion.query.filter_by(user_id=user.id, task_id=task.id, completion_date=today).first()
        tasks_list.append({
            'id': task.id,
            'title': task.title,
            'type': task.type,
            'description': task.description,
            'completed': True if completion else False,
            'badge': completion.badge if completion else task.badge
        })
    return jsonify({'tasks': tasks_list}), 200

@main.route('/complete-task', methods=['POST'])
def complete_task():
    if 'user_id' not in session:
        return jsonify({'message': 'Unauthorized'}), 401
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'message': 'User not found'}), 404
    data = request.get_json()
    taskId = data.get('taskId')
    if not taskId:
        return jsonify({'message': 'Task ID not provided'}), 400
    task = Task.query.filter_by(id=taskId).first()
    if not task:
        return jsonify({'message': 'Task not found'}), 404
    today = datetime.utcnow().date()
    existing_completion = TaskCompletion.query.filter_by(user_id=user.id, task_id=task.id, completion_date=today).first()
    if existing_completion:
        return jsonify({'message': 'Task already completed today'}), 400
    new_completion = TaskCompletion(
        user_id=user.id,
        task_id=task.id,
        completion_date=today,
        badge=task.badge
    )
    db.session.add(new_completion)
    db.session.commit()

    regular_tasks_count = Task.query.filter(Task.type != "achievement").count()
    completed_regular = TaskCompletion.query.join(Task, Task.id == TaskCompletion.task_id)\
                           .filter(TaskCompletion.user_id==user.id,
                                   TaskCompletion.completion_date==today,
                                   Task.type != "achievement").count()
    if completed_regular == regular_tasks_count:
        achievement_task = Task.query.filter_by(type="achievement", title="Wellness Achiever").first()
        if achievement_task:
            existing_achiever = TaskCompletion.query.filter_by(user_id=user.id, task_id=achievement_task.id, completion_date=today).first()
            if not existing_achiever:
                achiever_completion = TaskCompletion(
                    user_id=user.id,
                    task_id=achievement_task.id,
                    completion_date=today,
                    badge="Wellness Achiever Badge"
                )
                db.session.add(achiever_completion)
                db.session.commit()

    return jsonify({'message': 'Task marked as completed'}), 200


