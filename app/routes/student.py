"""Student-facing routes: dashboard, profile, test, results, history, PDF."""
from flask import (
    Blueprint, render_template, redirect, url_for, request, flash,
    current_app, abort, send_file, jsonify,
)
from flask_login import login_required, current_user

from ..extensions import db
from ..models import Question, Career, Program, TestAttempt
from ..scoring import score_submission, InvalidTestSubmission
from ..pdf_report import build_report

student_bp = Blueprint("student", __name__, url_prefix="/student")


def _student_only():
    if not current_user.is_authenticated or current_user.is_admin:
        abort(403)


@student_bp.before_request
@login_required
def _guard():
    # Admins use the admin panel; keep the student area for students.
    if current_user.is_admin:
        return redirect(url_for("admin.dashboard"))


@student_bp.route("/dashboard")
def dashboard():
    attempts = (TestAttempt.query.filter_by(user_id=current_user.id)
                .order_by(TestAttempt.created_at.desc()).all())
    latest = attempts[0] if attempts else None
    n_questions = Question.query.filter_by(is_active=True).count()
    return render_template(
        "student/dashboard.html",
        attempts=attempts, latest=latest, n_questions=n_questions,
    )


@student_bp.route("/profile", methods=["GET", "POST"])
def profile():
    if request.method == "POST":
        current_user.full_name = (request.form.get("full_name") or current_user.full_name).strip()
        current_user.phone = (request.form.get("phone") or "").strip()
        current_user.education_level = (request.form.get("education_level") or "").strip()
        current_user.institution = (request.form.get("institution") or "").strip()
        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("student.profile"))
    return render_template("student/profile.html")


@student_bp.route("/test")
def test():
    questions = (Question.query.filter_by(is_active=True)
                 .order_by(Question.category, Question.id).all())
    if not questions:
        flash("The test is not available yet. Please check back later.", "warning")
        return redirect(url_for("student.dashboard"))

    # Group questions for a clean, sectioned layout.
    sections = {
        "logical_reasoning": [], "analytical_thinking": [],
        "verbal_ability": [], "interest": [],
    }
    for q in questions:
        sections.setdefault(q.category, []).append(q)
    return render_template("student/test.html", sections=sections, total=len(questions))


@student_bp.route("/test/submit", methods=["POST"])
def submit_test():
    questions = Question.query.filter_by(is_active=True).all()

    # Collect answers from the form: fields are named "q<question_id>".
    answers = {}
    for q in questions:
        val = request.form.get(f"q{q.id}")
        if val is not None and val != "":
            answers[str(q.id)] = val

    try:
        result = score_submission(questions, answers)
    except InvalidTestSubmission as exc:
        flash(str(exc), "danger")
        return redirect(url_for("student.test"))

    # AI recommendation
    recommender = current_app.recommender
    recommendations = recommender.recommend(result["profile"], top_n=4)

    # Map recommended careers -> university programs (DB lookup, de-duplicated).
    rec_names = [r["name"] for r in recommendations]
    programs = _programs_for_careers(rec_names)

    # Persist the attempt (results saved in the database).
    attempt = TestAttempt(
        user_id=current_user.id,
        logical_score=result["logical"],
        analytical_score=result["analytical"],
        verbal_score=result["verbal"],
        overall_score=result["overall"],
    )
    attempt.interest = result["interest"]
    attempt.answers = answers
    attempt.recommendations = recommendations
    attempt.programs = programs
    db.session.add(attempt)
    db.session.commit()

    return redirect(url_for("student.result", attempt_id=attempt.id))


def _programs_for_careers(career_names):
    """Return a de-duplicated list of program dicts for the given career names."""
    seen = set()
    programs = []
    careers = Career.query.filter(Career.name.in_(career_names)).all()
    # Preserve the recommendation ranking order.
    by_name = {c.name: c for c in careers}
    for name in career_names:
        career = by_name.get(name)
        if not career:
            continue
        for p in career.programs:
            if not p.is_active or p.id in seen:
                continue
            seen.add(p.id)
            programs.append({
                "name": p.name,
                "degree_level": p.degree_level,
                "duration": p.duration,
                "description": p.description,
                "universities": p.universities,
                "for_career": name,
            })
    return programs


@student_bp.route("/result/<int:attempt_id>")
def result(attempt_id):
    attempt = db.session.get(TestAttempt, attempt_id)
    if attempt is None or attempt.user_id != current_user.id:
        abort(404)
    return render_template(
        "student/result.html",
        attempt=attempt, pass_threshold=current_app.config["PASS_THRESHOLD"],
    )


@student_bp.route("/result/<int:attempt_id>/pdf")
def result_pdf(attempt_id):
    attempt = db.session.get(TestAttempt, attempt_id)
    if attempt is None or attempt.user_id != current_user.id:
        abort(404)
    buffer = build_report(current_user, attempt)
    filename = f"career_report_{attempt.id}.pdf"
    return send_file(buffer, mimetype="application/pdf",
                     as_attachment=True, download_name=filename)


@student_bp.route("/history")
def history():
    attempts = (TestAttempt.query.filter_by(user_id=current_user.id)
                .order_by(TestAttempt.created_at.desc()).all())
    return render_template("student/history.html", attempts=attempts)


