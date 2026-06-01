"""
Database models for the AI-Based Career Counselling System.

Tables
------
User            : students and admins (role column distinguishes them)
Question        : aptitude / interest questions managed from the admin panel
Career          : careers with an "ideal aptitude profile" used by the recommender
Program         : university degree programs
career_program  : many-to-many link between careers and programs
TestAttempt     : one completed aptitude test (scores + recommendation snapshot)
"""
import json
from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from .extensions import db, login_manager


# ---------------------------------------------------------------------------
# Many-to-many association table: a career can map to several programs and a
# program can serve several careers.
# ---------------------------------------------------------------------------
career_program = db.Table(
    "career_program",
    db.Column("career_id", db.Integer, db.ForeignKey("career.id", ondelete="CASCADE"), primary_key=True),
    db.Column("program_id", db.Integer, db.ForeignKey("program.id", ondelete="CASCADE"), primary_key=True),
)


class User(UserMixin, db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="student")  # 'student' or 'admin'

    # Optional profile fields
    phone = db.Column(db.String(30))
    education_level = db.Column(db.String(60))   # e.g. "High School", "Intermediate", "Undergraduate"
    institution = db.Column(db.String(150))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    attempts = db.relationship(
        "TestAttempt", backref="student", lazy=True, cascade="all, delete-orphan"
    )

    # --- password helpers -------------------------------------------------
    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"


class Question(db.Model):
    __tablename__ = "question"

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)

    # category: logical_reasoning | analytical_thinking | verbal_ability | interest
    category = db.Column(db.String(40), nullable=False, index=True)

    # For interest questions: which interest area this statement maps to.
    # (science, technology, business, arts, healthcare, engineering, social)
    interest_area = db.Column(db.String(40))

    # Question type: 'mcq' (one correct option) or 'likert' (1-5 agreement).
    qtype = db.Column(db.String(20), nullable=False, default="mcq")

    # Options stored as JSON list of strings (only used for mcq).
    options_json = db.Column(db.Text, default="[]")
    # Index (0-based) of the correct option (only used for mcq).
    correct_index = db.Column(db.Integer)

    is_active = db.Column(db.Boolean, default=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # --- convenience accessors -------------------------------------------
    @property
    def options(self):
        try:
            return json.loads(self.options_json or "[]")
        except (ValueError, TypeError):
            return []

    @options.setter
    def options(self, value):
        self.options_json = json.dumps(value or [])

    def __repr__(self) -> str:
        return f"<Question {self.id} {self.category}>"


class Career(db.Model):
    __tablename__ = "career"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(40), default="bi-briefcase")  # Bootstrap icon name
    avg_salary = db.Column(db.String(60))
    growth_outlook = db.Column(db.String(60))

    # The "ideal profile" — target scores (0-100) the recommender matches against.
    # Stored as JSON: {"logical":.., "analytical":.., "verbal":..,
    #                  "science":.., "technology":.., "business":..,
    #                  "arts":.., "healthcare":.., "engineering":.., "social":..}
    profile_json = db.Column(db.Text, default="{}")

    is_active = db.Column(db.Boolean, default=True, index=True)

    programs = db.relationship(
        "Program", secondary=career_program, back_populates="careers", lazy="subquery"
    )

    @property
    def profile(self):
        try:
            return json.loads(self.profile_json or "{}")
        except (ValueError, TypeError):
            return {}

    @profile.setter
    def profile(self, value):
        self.profile_json = json.dumps(value or {})

    def __repr__(self) -> str:
        return f"<Career {self.name}>"


class Program(db.Model):
    __tablename__ = "program"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    degree_level = db.Column(db.String(60))   # e.g. "Bachelor", "Master"
    duration = db.Column(db.String(40))       # e.g. "4 years"
    description = db.Column(db.Text)
    universities = db.Column(db.Text)         # comma/newline separated suggestions
    is_active = db.Column(db.Boolean, default=True, index=True)

    careers = db.relationship(
        "Career", secondary=career_program, back_populates="programs", lazy="subquery"
    )

    def __repr__(self) -> str:
        return f"<Program {self.name}>"


class TestAttempt(db.Model):
    __tablename__ = "test_attempt"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # Category scores (0-100, normalised).
    logical_score = db.Column(db.Float, default=0)
    analytical_score = db.Column(db.Float, default=0)
    verbal_score = db.Column(db.Float, default=0)
    overall_score = db.Column(db.Float, default=0)

    # Interest scores per area + raw answers + recommendation snapshot (JSON).
    interest_json = db.Column(db.Text, default="{}")
    answers_json = db.Column(db.Text, default="{}")
    recommendations_json = db.Column(db.Text, default="[]")
    programs_json = db.Column(db.Text, default="[]")

    @property
    def interest(self):
        try:
            return json.loads(self.interest_json or "{}")
        except (ValueError, TypeError):
            return {}

    @interest.setter
    def interest(self, value):
        self.interest_json = json.dumps(value or {})

    @property
    def recommendations(self):
        try:
            return json.loads(self.recommendations_json or "[]")
        except (ValueError, TypeError):
            return []

    @recommendations.setter
    def recommendations(self, value):
        self.recommendations_json = json.dumps(value or [])

    @property
    def programs(self):
        try:
            return json.loads(self.programs_json or "[]")
        except (ValueError, TypeError):
            return []

    @programs.setter
    def programs(self, value):
        self.programs_json = json.dumps(value or [])

    @property
    def answers(self):
        try:
            return json.loads(self.answers_json or "{}")
        except (ValueError, TypeError):
            return {}

    @answers.setter
    def answers(self, value):
        self.answers_json = json.dumps(value or {})

    def __repr__(self) -> str:
        return f"<TestAttempt {self.id} user={self.user_id}>"


# ---------------------------------------------------------------------------
# Flask-Login user loader
# ---------------------------------------------------------------------------
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


