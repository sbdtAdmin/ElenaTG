from tools import *


def generate_response(history, content):
    gemini = GeminiAI()
    gemini.chat.history = history
    result = gemini.send_message(content)
    print(result)
    return result