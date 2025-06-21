import re
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer

stemmer = PorterStemmer()

def remove_patterns(text):
    text = re.sub(r'http[s]?://\S+', '', text)
    text = re.sub(r'\[.*?\]\(.*?\)', '', text)
    text = re.sub(r'@\w+', '', text)
    text = re.sub(r'[^\w\s]', '', text)
    return text.strip()

def preprocess_text(text):
    text = text.lower()
    text = remove_patterns(text)
    tokens = word_tokenize(text)
    stemmed_tokens = [stemmer.stem(token) for token in tokens]
    return ' '.join(stemmed_tokens)

def generate_response(user_message):
    message = user_message.lower()
    if any(word in message for word in ["depressed", "sad", "unhappy", "miserable"]):
        return (
            "Oh dear, I'm truly sorry you're feeling down. It sounds like you're carrying a heavy heart today. "
            "Sometimes sharing what's weighing you down can bring a little relief—I’m here to listen. Remember, you're not alone, and you deserve care. "
            "If it ever feels too much, please consider reaching out to someone you trust or a mental health professional."
        )
    elif any(word in message for word in ["lonely", "alone", "isolated"]):
        return (
            "Feeling lonely is incredibly tough, and I'm sorry you're going through that. "
            "I wish I could give you a warm virtual hug right now! Sometimes talking to someone—be it a friend or even me—can help lighten the load."
        )
    elif any(word in message for word in ["anxious", "nervous", "worried"]):
        return (
            "Anxiety can feel overwhelming, and I completely understand how that might be affecting you. "
            "Have you tried taking a few deep breaths or maybe stepping outside for a moment? I'm here to listen if you’d like to talk it through."
        )
    elif any(word in message for word in ["help", "support", "therapy", "professional"]):
        return (
            "It takes courage to ask for help, and I'm proud of you for considering it. While I'm here as your virtual companion, sometimes speaking with a mental health professional can offer deeper support. "
            "Please remember, seeking help is a sign of strength."
        )
    elif any(phrase in message for phrase in ["how are you", "how's it going", "what's up", "how do you do"]):
        return (
            "I'm Lisa, your virtual confidante, buzzing with readiness to chat with you! How's your day shaping up so far?"
        )
    elif any(phrase in message for phrase in ["onepiece", "onepiece spoiler", "spoiler"]):
        return (
            "Ah, diving into One Piece, are we? I must say, the lore is as deep as the ocean—did you know Shanks has a secret story that few have heard of?"
        )
    elif any(word in message for word in ["hi", "hello", "hey"]):
        return "Hello there! I'm Lisa. How are you feeling today?"
    elif "weather" in message:
        return (
            "Weather can be such an interesting topic! Whether it's bright and sunny or a bit gloomy, our surroundings often mirror our mood. "
            "I'd love to hear what the weather's like where you are!"
        )
    elif any(word in message for word in ["bye", "goodbye", "see you"]):
        return (
            "Goodbye for now. Remember, I'm always here if you need someone to talk to. Take care, and have a wonderful day!"
        )
    else:
        return (
            "I hear you. Sometimes it helps to share more about what's on your mind. "
            "Feel free to tell me more about how you're feeling, or if you'd just like some company, I'm right here."
        )
