"""
Application configuration.

All tunable settings live here so the rest of the codebase can stay clean.
Values can be overridden with environment variables for production use.
"""
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
MODEL_DIR = os.path.join(BASE_DIR, "models")

# Make sure the folders we write to exist.
os.makedirs(INSTANCE_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)


class Config:
    """Base configuration shared by every environment."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-secret-key-in-production-9f3a2c")

    # SQLite database stored inside /instance so it is easy to find and back up.
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///" + os.path.join(INSTANCE_DIR, "career_counselling.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Where the trained ML model is saved / loaded from.
    MODEL_PATH = os.path.join(MODEL_DIR, "career_model.joblib")

    # Aptitude test rules.
    PASS_THRESHOLD = 40          # informational only, shown on the result page
    MIN_QUESTIONS_PER_CATEGORY = 1


