"""Career AI — AI-Based Career Counselling System.

Application entry point.  Run with:  python run.py
Then open http://127.0.0.1:5000 in your browser.
"""
from app import create_app

app = create_app()

if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5000, debug=True) 

