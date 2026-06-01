"""Seed the database with an admin account, careers, programs, and a question bank.

Run once after installing:  python seed_data.py
The script is idempotent: it will not create duplicates if run again.
"""
from app import create_app
from app.extensions import db
from app.models import User, Career, Program, Question
from app.ml.dataset import CAREER_PROFILES, PROGRAMS

# ---------------------------------------------------------------------------
# Default accounts
# ---------------------------------------------------------------------------
ADMIN_EMAIL = "admin@Career AI.com"
ADMIN_PASSWORD = "Admin@123"

DEMO_STUDENT_EMAIL = "student@Career AI.com"
DEMO_STUDENT_PASSWORD = "Student@123"

# ---------------------------------------------------------------------------
# Question bank
#   Aptitude MCQs -> category in (logical_reasoning, analytical_thinking, verbal_ability)
#   Interest items -> category 'interest', answered on a 1-5 agreement scale
# ---------------------------------------------------------------------------
MCQ_QUESTIONS = [
    # --- Logical reasoning ---
    ("logical_reasoning", "Which number completes the sequence: 2, 4, 8, 16, __ ?",
     ["20", "24", "32", "30"], 2),
    ("logical_reasoning", "If all roses are flowers and some flowers fade quickly, which is certainly true?",
     ["All roses fade quickly", "Some roses may fade quickly", "No roses fade", "Roses are not flowers"], 1),
    ("logical_reasoning", "Find the odd one out: 3, 5, 7, 9, 11",
     ["3", "9", "7", "5"], 1),
    ("logical_reasoning", "A is taller than B, B is taller than C. Who is shortest?",
     ["A", "B", "C", "Cannot tell"], 2),
    ("logical_reasoning", "Complete the pattern: AZ, BY, CX, __ ?",
     ["DW", "DV", "EW", "DX"], 0),
    ("logical_reasoning", "If MONDAY is coded as 123456, what is the code for DAY?",
     ["456", "356", "256", "465"], 0),

    # --- Analytical thinking ---
    ("analytical_thinking", "A car travels 60 km in 1.5 hours. What is its average speed?",
     ["30 km/h", "40 km/h", "45 km/h", "50 km/h"], 1),
    ("analytical_thinking", "If 3 workers build a wall in 6 days, how long for 6 workers (same rate)?",
     ["3 days", "6 days", "12 days", "2 days"], 0),
    ("analytical_thinking", "A shirt costs $40 after a 20% discount. What was the original price?",
     ["$48", "$50", "$52", "$60"], 1),
    ("analytical_thinking", "Which fraction is largest?",
     ["1/2", "2/5", "3/8", "5/12"], 0),
    ("analytical_thinking", "The average of 5 numbers is 20. Their total sum is?",
     ["80", "100", "120", "25"], 1),
    ("analytical_thinking", "If x + 7 = 12, then 2x = ?",
     ["5", "10", "12", "14"], 1),

    # --- Verbal ability ---
    ("verbal_ability", "Choose the synonym of 'abundant':",
     ["Scarce", "Plentiful", "Empty", "Rare"], 1),
    ("verbal_ability", "Choose the antonym of 'transparent':",
     ["Clear", "Opaque", "Visible", "Glassy"], 1),
    ("verbal_ability", "Complete: 'She was praised for her ____ handwriting.'",
     ["legible", "illegible", "messy", "vague"], 0),
    ("verbal_ability", "Which word is spelled correctly?",
     ["Definately", "Definitely", "Definitly", "Definetely"], 1),
    ("verbal_ability", "'Book' is to 'Library' as 'Painting' is to ____:",
     ["Frame", "Museum", "Artist", "Color"], 1),
    ("verbal_ability", "Identify the correctly punctuated sentence:",
     ["Its raining outside.", "It's raining outside.", "Its' raining outside.", "It raining outside."], 1),
]

# Interest items: (interest_area, statement)
INTEREST_QUESTIONS = [
    ("science", "I enjoy understanding how natural phenomena and experiments work."),
    ("science", "I like reading about scientific discoveries and research."),
    ("technology", "I enjoy working with computers, software, or new gadgets."),
    ("technology", "I like solving problems by building or programming things."),
    ("business", "I am interested in how companies operate, market, and make profit."),
    ("business", "I enjoy leading teams, planning, and managing resources."),
    ("arts", "I enjoy creative activities like design, drawing, writing, or music."),
    ("arts", "I like expressing ideas visually or through storytelling."),
    ("healthcare", "I find caring for people's health and wellbeing rewarding."),
    ("healthcare", "I am interested in the human body, medicine, and treatment."),
    ("engineering", "I enjoy designing, constructing, or improving physical structures and machines."),
    ("engineering", "I like figuring out how mechanical or structural systems work."),
    ("social", "I enjoy helping, teaching, or counselling other people."),
    ("social", "I am motivated by making a positive difference in my community."),
]


def seed_users():
    created = []
    if not User.query.filter_by(email=ADMIN_EMAIL).first():
        admin = User(full_name="System Administrator", email=ADMIN_EMAIL, role="admin")
        admin.set_password(ADMIN_PASSWORD)
        db.session.add(admin)
        created.append("admin")
    if not User.query.filter_by(email=DEMO_STUDENT_EMAIL).first():
        stu = User(full_name="Demo Student", email=DEMO_STUDENT_EMAIL, role="student",
                   education_level="Intermediate", institution="Demo College")
        stu.set_password(DEMO_STUDENT_PASSWORD)
        db.session.add(stu)
        created.append("demo student")
    db.session.commit()
    return created


def seed_careers():
    count = 0
    for name, info in CAREER_PROFILES.items():
        if Career.query.filter_by(name=name).first():
            continue
        c = Career(
            name=name,
            description=info.get("description", ""),
            icon=info.get("icon", "bi-briefcase"),
            avg_salary=info.get("avg_salary", ""),
            growth_outlook=info.get("growth_outlook", ""),
            is_active=True,
        )
        c.profile = info.get("profile", {})
        db.session.add(c)
        count += 1
    db.session.commit()
    return count


def seed_programs():
    count = 0
    for p in PROGRAMS:
        if Program.query.filter_by(name=p["name"]).first():
            continue
        prog = Program(
            name=p["name"],
            degree_level=p.get("degree_level", ""),
            duration=p.get("duration", ""),
            description=p.get("description", ""),
            universities=p.get("universities", ""),
            is_active=True,
        )
        # link careers by name
        linked = Career.query.filter(Career.name.in_(p.get("careers", []))).all()
        prog.careers = linked
        db.session.add(prog)
        count += 1
    db.session.commit()
    return count


def seed_questions():
    count = 0
    for category, text, options, correct in MCQ_QUESTIONS:
        if Question.query.filter_by(text=text).first():
            continue
        q = Question(text=text, category=category, qtype="mcq",
                     correct_index=correct, is_active=True)
        q.options = options
        db.session.add(q)
        count += 1

    for area, text in INTEREST_QUESTIONS:
        if Question.query.filter_by(text=text).first():
            continue
        q = Question(text=text, category="interest", qtype="likert",
                     interest_area=area, is_active=True)
        q.options = []
        db.session.add(q)
        count += 1

    db.session.commit()
    return count


def main():
    app = create_app()
    with app.app_context():
        db.create_all()
        users = seed_users()
        careers = seed_careers()
        programs = seed_programs()
        questions = seed_questions()

        print("=" * 56)
        print(" Career AI database seed complete")
        print("=" * 56)
        print(f"  Users created     : {', '.join(users) if users else 'none (already existed)'}")
        print(f"  Careers added     : {careers}")
        print(f"  Programs added    : {programs}")
        print(f"  Questions added   : {questions}")
        print("-" * 56)
        print("  Admin login   ->  {}  /  {}".format(ADMIN_EMAIL, ADMIN_PASSWORD))
        print("  Student login ->  {}  /  {}".format(DEMO_STUDENT_EMAIL, DEMO_STUDENT_PASSWORD))
        print("=" * 56)


if __name__ == "__main__":
    main()


