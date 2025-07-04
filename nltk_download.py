import nltk
import os

# Define the custom NLTK data path that Render uses
nltk_data_path = "/opt/render/project/src/nltk_data"
os.makedirs(nltk_data_path, exist_ok=True)

# Download 'punkt' tokenizer to that path
nltk.download("punkt", download_dir=nltk_data_path)
