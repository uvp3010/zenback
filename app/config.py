import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'your_secret_key_here')
    SESSION_TYPE = 'filesystem'
    SESSION_COOKIE_SAMESITE = 'None'
    SESSION_COOKIE_SECURE = True  # Change to True in production when using HTTPS
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    AUDIO_FOLDER = "audio"
    # Twilio configuration
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', 'ACae6111c342c9fa53179d7e909fafa380')
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', '7ce637f990d53f40bb19c279cbeef692')
    TWILIO_WHATSAPP_NUMBER = 'whatsapp:+14155238886'
