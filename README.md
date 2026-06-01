# Career AI — AI-Based Career Counselling System

An end-to-end web app that recommends **careers** and **university programs**
to students based on an online aptitude test and interest profile, powered by a
scikit-learn recommendation engine.

> **Full setup instructions are in [`INSTALL_GUIDE.md`](INSTALL_GUIDE.md).**

## Features
- Student registration, login and profile management (Flask-Login)
- Online aptitude test — logical reasoning, analytical thinking, verbal ability
  and interest areas — with automatic scoring and strict input validation
- AI-based career recommendation (RandomForest + cosine-similarity hybrid)
- Matching university-program suggestions
- Result page with score cards, an interest **radar chart** and career
  match rings (Chart.js), plus **PDF report** export (ReportLab)
- Saved assessment history per student (SQLite via SQLAlchemy)
- Full admin panel: manage questions, careers and programs; view student
  reports; retrain the model
- Responsive Bootstrap 5 UI (desktop / tablet / mobile)

## Quick start

```bash
python -m venv venv
# Windows: venv\Scripts\activate     macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
python seed_data.py        # demo data + accounts
python train_model.py      # optional (otherwise trains on first use)
python run.py              # -> http://127.0.0.1:5000
```

**Default logins**

| Role    | Email                    | Password      |
|---------|--------------------------|---------------|
| Admin   | admin@Career AI.com     | Admin@123     |
| Student | student@Career AI.com   | Student@123   |

## Tech stack
Flask · Flask-SQLAlchemy · Flask-Login · scikit-learn · pandas · numpy ·
ReportLab · Bootstrap 5 · Chart.js


