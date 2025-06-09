

import requests
import os
from dotenv import load_dotenv

load_dotenv()

def genre_vorschlag(title, author):
    api_key = os.getenv("OPENROUTER_API_KEY")
    context_file = "event_config.txt"
    response = None

    if os.path.exists(context_file):
        with open(context_file, "r", encoding="utf-8") as f:
            context = f.read()
    else:
        context = ""

    prompt = f"""Eventbeschreibung & bevorzugte Genres: {context}
Soll der folgende Musikwunsch auf dein Event passen? Gib nur 'geeignet' oder 'ungeeignet' zurück.
Song: '{title}' von '{author}'
"""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    models = [
        "google/gemini-2.0-flash-exp:free",
        "meta-llama/llama-3.3-8b-instruct:free",
        "google/gemma-3n-e4b-it:free",
        "deepseek/deepseek-r1-0528:free",
        "mistralai/devstral-small:free",
        "microsoft/phi-4-reasoning:free"
    ]

    for model in models:
        data = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        try:
            print(f"Versuche Modell: {model}")
            response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
            if response.ok:
                content = response.json()['choices'][0]['message']['content'].strip().lower()
                print("Antwort der KI:", response.json()['choices'][0]['message']['content'].strip())
                print(f"{model} antwortet: {content}")
                if content == "ungeeignet":
                    return "ungeeignet"
                elif content == "geeignet":
                    return "geeignet"
                else:
                    print("Unklare oder fehlerhafte Antwort:", content)
            else:
                print(f"Fehler bei Modell {model}:", response.text)
        except Exception as e:
            print(f"Fehler bei Modell {model}: {e}")
            if response is not None:
                print("Fehlerhafte Antwort:", response.text)
    return "ungeeignet"

# Beispielaufruf
if __name__ == "__main__":
    title = "Bohemian Rhapsody"
    author = "Queen"
    result = genre_vorschlag(title, author)
    print("Klassifikation:", result)