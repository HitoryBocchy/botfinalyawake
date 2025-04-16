import json

QUIZ_FILE = "quiz_data.json"
CHARACTER_FILE = "character_quiz.json"
EMOJI_FILE = "emoji_quiz.json"
STATS_FILE = "user_stats.json"

def load_data(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read().strip()
            return json.loads(content) if content else {}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_user_stats(stats):
    with open(STATS_FILE, "w", encoding="utf-8") as file:
        json.dump(stats, file, indent=4, ensure_ascii=False)
