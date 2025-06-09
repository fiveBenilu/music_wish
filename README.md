

# 🎵 MusicRecommendationEngine – DJ Bennet's Music Request System

A modern, Flask-based web tool for handling music requests at events – mobile-friendly for guests, and desktop-optimized for admins.

## 🧠 Features

- 🎤 Guests can submit music requests via a sleek mobile form including name, song title, artist, and an optional comment.
- ✅ Privacy checkbox required before submission.
- 🔒 Admin panel with login protection:
  - View all requests in a responsive table
  - Real-time updates via WebSocket
  - Delete entries after playing them
- 🤖 AI-Powered Analysis:
  - Classifies songs as "suitable" or "unsuitable" based on the event context
  - Justification for classification shown on click
  - If models are rate-limited, "Limit" is shown instead

## 🛠️ Tech Stack

- Python (Flask)
- SQLite
- Bootstrap (responsive design)
- JavaScript + WebSocket (real-time updates)
- OpenRouter LLM API (AI integration)

## ⚙️ Setup

1. Clone the repo:
   ```bash
   git clone https://github.com/yourusername/MusicRecommendationEngine.git
   cd MusicRecommendationEngine

	2.	Set up the virtual environment and install dependencies:

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt


	3.	Add an .env file with your OpenRouter API key:

OPENROUTER_API_KEY=your-key-here


	4.	Run the app:

flask run



🔑 Admin Login

Default credentials:
	•	Username: admin
	•	Password: admin

You can modify them in the main.py or extend the login logic.

📦 Folder Structure

.
├── static/               # Stylesheets, JS, images
├── templates/            # HTML templates
├── main.py               # Flask application
├── ai_utils.py           # LLM logic
├── event_config.txt      # Event description + genres
└── README.md

📄 License

MIT License – free to use and modify.

⸻

Built with ❤️ for DJs and party people by Bennet Griese.

Let me know if you want the German version included as a second section.
