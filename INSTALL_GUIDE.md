# Career AI — AI-Based Career Counselling System
### Installation & Usage Guide

Career AI helps students discover suitable **career paths** and **university
programs** based on an online aptitude test and interest profile, using a
machine-learning recommendation engine (scikit-learn).

This guide takes you from a clean machine all the way to a running app.

---

## 1. Prerequisites

- **Python 3.10 or newer** (developed and tested on Python 3.12)
- **pip** (comes with Python)
- A terminal / command prompt

Check your Python version:

```bash
python --version
```
*(On some systems use `python3` instead of `python`.)*

---

## 2. Get the project

Unzip the delivered file and open a terminal **inside** the project folder
(the folder that contains `run.py`):

```bash
cd career_counselling_system
```

---

## 3. Create a virtual environment

A virtual environment keeps this project's dependencies isolated.

**Windows (PowerShell or CMD):**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

After activation your prompt shows `(venv)`. To leave it later, type `deactivate`.

---

## 4. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This installs Flask, Flask-SQLAlchemy, Flask-Login, scikit-learn, pandas,
numpy, joblib and reportlab.

---

## 5. Seed the database

This creates the SQLite database and fills it with careers, university
programs, a ready-made question bank, an **admin** account and a **demo
student** account.

```bash
python seed_data.py
```

You should see a summary ending with the default login credentials.

> The script is safe to run more than once — it never creates duplicates.

---

## 6. (Optional) Train the AI model ahead of time

```bash
python train_model.py
```

This trains the recommendation model and saves it to `models/`. It is
**optional**: if you skip it, the app trains the model automatically the first
time a student submits a test (that first submission just takes a few extra
seconds).

---

## 7. Run the application

```bash
python run.py
```

Open your browser at:

```
http://127.0.0.1:5000
```

To stop the server, press **Ctrl + C** in the terminal.

---

## 8. Default login credentials

| Role    | Email                     | Password      |
|---------|---------------------------|---------------|
| Admin   | `admin@Career AI.com`    | `Admin@123`   |
| Student | `student@Career AI.com`  | `Student@123` |

> Please change these after your first login in a real deployment.

---

## 9. How to use it

**As a student:**
1. Register a new account (or use the demo student above).
2. From the dashboard, open **Take the test**.
3. Answer the aptitude questions (logical, analytical, verbal) and rate the
   interest statements. The submit button stays disabled until every question
   is answered, and the server re-validates all answers.
4. Click **Submit** to see your result page: category scores, an interest
   radar chart, recommended careers with match percentages, and matching
   university programs.
5. Download a **PDF report**, or revisit any past attempt under **History**.

**As an admin:**
1. Log in with the admin account.
2. **Dashboard** — system stats and a "most recommended careers" chart.
3. **Questions** — add/edit/activate/delete aptitude and interest questions.
4. **Careers** — manage careers and tune each career's aptitude/interest
   profile (which drives the recommendations), and link programs.
5. **Programs** — manage university programs and link them to careers.
6. **Students** — browse students and view each one's full assessment history.
7. **Retrain AI model** — rebuild the model after editing careers.

---

## 10. Project structure

```
career_counselling_system/
├── run.py                 # Entry point  ->  python run.py
├── seed_data.py           # Populate DB with demo data + accounts
├── train_model.py         # Train & save the ML model (optional)
├── config.py              # App configuration
├── requirements.txt       # Dependencies
├── app/
│   ├── __init__.py        # App factory
│   ├── extensions.py      # db, login manager
│   ├── models.py          # User, Question, Career, Program, TestAttempt
│   ├── scoring.py         # Test scoring + input validation
│   ├── pdf_report.py      # PDF report generation (ReportLab)
│   ├── ml/
│   │   ├── dataset.py     # Synthetic training data + career profiles
│   │   └── recommender.py # scikit-learn model + cosine-similarity blend
│   ├── routes/            # main / auth / student / admin blueprints
│   ├── templates/         # HTML (Bootstrap 5) views
│   └── static/            # CSS + JS
├── instance/              # SQLite database (created at runtime)
└── models/                # Saved ML model (created at runtime)
```

---

## 11. How the recommendation works

1. **Scoring** (`app/scoring.py`) turns the student's answers into a 10-feature
   profile: three aptitude scores (logical, analytical, verbal) and seven
   interest scores (science, technology, business, arts, healthcare,
   engineering, social), each on a 0–100 scale. Empty or invalid submissions
   are rejected before any scoring happens.
2. **Model** (`app/ml/recommender.py`) is a `StandardScaler` +
   `RandomForestClassifier` pipeline trained on a synthetic dataset generated
   from each career's ideal profile. It outputs a probability per career.
3. **Hybrid blend** — those probabilities are blended with the **cosine
   similarity** between the student's profile and each career profile, giving a
   stable, explainable match percentage plus a short reason for each
   recommendation.
4. **Programs** — university programs linked to the top careers are collected
   (de-duplicated, best match first) and shown alongside the careers.

---

## 12. Troubleshooting

- **`ModuleNotFoundError`** — make sure the virtual environment is activated and
  `pip install -r requirements.txt` finished without errors.
- **`python` not found** — try `python3` (and `pip3`).
- **Port 5000 already in use** — edit the port at the bottom of `run.py`.
- **Want a fresh start** — stop the server, delete the `instance/` folder and
  the file in `models/`, then run `python seed_data.py` again.

---

*Built with Flask, scikit-learn, Bootstrap 5 and Chart.js.*


