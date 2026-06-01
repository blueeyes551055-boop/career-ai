"""Admin panel: manage questions, careers, programs; view student reports."""
import json
from functools import wraps

from flask import (
    Blueprint, render_template, redirect, url_for, request, flash, abort, current_app,
)
from flask_login import login_required, current_user

from ..extensions import db
from ..models import User, Question, Career, Program, TestAttempt
from ..ml.dataset import INTEREST_AREAS
from ..ml.recommender import train_and_save

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

APT_CATEGORIES = [
    ("logical_reasoning", "Logical Reasoning"),
    ("analytical_thinking", "Analytical Thinking"),
    ("verbal_ability", "Verbal Ability"),
]


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return view(*args, **kwargs)
    return wrapped


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
@admin_bp.route("/dashboard")
@admin_required
def dashboard():
    stats = {
        "students": User.query.filter_by(role="student").count(),
        "questions": Question.query.count(),
        "active_questions": Question.query.filter_by(is_active=True).count(),
        "careers": Career.query.count(),
        "programs": Program.query.count(),
        "attempts": TestAttempt.query.count(),
    }
    recent = (TestAttempt.query.order_by(TestAttempt.created_at.desc()).limit(8).all())

    # Aggregate: how often each career is recommended (for a quick report chart).
    career_counts = {}
    for a in TestAttempt.query.all():
        for rec in a.recommendations:
            career_counts[rec["name"]] = career_counts.get(rec["name"], 0) + 1
    top_careers = sorted(career_counts.items(), key=lambda kv: kv[1], reverse=True)[:8]

    return render_template(
        "admin/dashboard.html", stats=stats, recent=recent,
        top_careers=top_careers,
    )


# ---------------------------------------------------------------------------
# Questions CRUD
# ---------------------------------------------------------------------------
@admin_bp.route("/questions")
@admin_required
def questions():
    qs = Question.query.order_by(Question.category, Question.id).all()
    return render_template("admin/questions.html", questions=qs)


@admin_bp.route("/questions/new", methods=["GET", "POST"])
@admin_bp.route("/questions/<int:qid>/edit", methods=["GET", "POST"])
@admin_required
def question_form(qid=None):
    q = db.session.get(Question, qid) if qid else None
    if qid and q is None:
        abort(404)

    if request.method == "POST":
        category = request.form.get("category", "")
        text = (request.form.get("text") or "").strip()
        errors = []

        if not text:
            errors.append("Question text is required.")
        if category not in ("logical_reasoning", "analytical_thinking",
                             "verbal_ability", "interest"):
            errors.append("Please choose a valid category.")

        qtype = "likert" if category == "interest" else "mcq"
        options, correct_index, interest_area = [], None, None

        if qtype == "mcq":
            options = [o.strip() for o in request.form.getlist("option") if o.strip()]
            if len(options) < 2:
                errors.append("Provide at least two answer options.")
            try:
                correct_index = int(request.form.get("correct_index"))
            except (TypeError, ValueError):
                correct_index = None
            if correct_index is None or correct_index < 0 or correct_index >= len(options):
                errors.append("Select which option is correct.")
        else:  # interest -> likert
            interest_area = request.form.get("interest_area")
            if interest_area not in INTEREST_AREAS:
                errors.append("Choose a valid interest area.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template(
                "admin/question_form.html", q=q, categories=APT_CATEGORIES,
                interest_areas=INTEREST_AREAS, form=request.form,
            )

        if q is None:
            q = Question()
            db.session.add(q)
        q.text = text
        q.category = category
        q.qtype = qtype
        q.interest_area = interest_area
        q.options = options
        q.correct_index = correct_index
        q.is_active = bool(request.form.get("is_active"))
        db.session.commit()
        flash("Question saved.", "success")
        return redirect(url_for("admin.questions"))

    return render_template(
        "admin/question_form.html", q=q, categories=APT_CATEGORIES,
        interest_areas=INTEREST_AREAS, form=None,
    )


@admin_bp.route("/questions/<int:qid>/delete", methods=["POST"])
@admin_required
def question_delete(qid):
    q = db.session.get(Question, qid)
    if q:
        db.session.delete(q)
        db.session.commit()
        flash("Question deleted.", "info")
    return redirect(url_for("admin.questions"))


@admin_bp.route("/questions/<int:qid>/toggle", methods=["POST"])
@admin_required
def question_toggle(qid):
    q = db.session.get(Question, qid)
    if q:
        q.is_active = not q.is_active
        db.session.commit()
    return redirect(url_for("admin.questions"))


# ---------------------------------------------------------------------------
# Careers CRUD
# ---------------------------------------------------------------------------
@admin_bp.route("/careers")
@admin_required
def careers():
    cs = Career.query.order_by(Career.name).all()
    return render_template("admin/careers.html", careers=cs)


@admin_bp.route("/careers/new", methods=["GET", "POST"])
@admin_bp.route("/careers/<int:cid>/edit", methods=["GET", "POST"])
@admin_required
def career_form(cid=None):
    c = db.session.get(Career, cid) if cid else None
    if cid and c is None:
        abort(404)
    all_programs = Program.query.order_by(Program.name).all()
    feature_keys = ["logical", "analytical", "verbal"] + INTEREST_AREAS

    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        errors = []
        if not name:
            errors.append("Career name is required.")
        existing = Career.query.filter_by(name=name).first()
        if existing and (c is None or existing.id != c.id):
            errors.append("A career with that name already exists.")

        profile = {}
        for k in feature_keys:
            try:
                v = float(request.form.get(f"profile_{k}", 0))
            except ValueError:
                v = 0
            profile[k] = max(0, min(100, v))

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template(
                "admin/career_form.html", c=c, all_programs=all_programs,
                feature_keys=feature_keys, form=request.form,
            )

        if c is None:
            c = Career()
            db.session.add(c)
        c.name = name
        c.description = (request.form.get("description") or "").strip()
        c.icon = (request.form.get("icon") or "bi-briefcase").strip()
        c.avg_salary = (request.form.get("avg_salary") or "").strip()
        c.growth_outlook = (request.form.get("growth_outlook") or "").strip()
        c.profile = profile
        c.is_active = bool(request.form.get("is_active"))

        # link programs
        selected = request.form.getlist("programs")
        c.programs = Program.query.filter(Program.id.in_(selected)).all() if selected else []
        db.session.commit()
        flash("Career saved.", "success")
        return redirect(url_for("admin.careers"))

    return render_template(
        "admin/career_form.html", c=c, all_programs=all_programs,
        feature_keys=feature_keys, form=None,
    )


@admin_bp.route("/careers/<int:cid>/delete", methods=["POST"])
@admin_required
def career_delete(cid):
    c = db.session.get(Career, cid)
    if c:
        db.session.delete(c)
        db.session.commit()
        flash("Career deleted.", "info")
    return redirect(url_for("admin.careers"))


# ---------------------------------------------------------------------------
# Programs CRUD
# ---------------------------------------------------------------------------
@admin_bp.route("/programs")
@admin_required
def programs():
    ps = Program.query.order_by(Program.name).all()
    return render_template("admin/programs.html", programs=ps)


@admin_bp.route("/programs/new", methods=["GET", "POST"])
@admin_bp.route("/programs/<int:pid>/edit", methods=["GET", "POST"])
@admin_required
def program_form(pid=None):
    p = db.session.get(Program, pid) if pid else None
    if pid and p is None:
        abort(404)
    all_careers = Career.query.order_by(Career.name).all()

    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        errors = []
        if not name:
            errors.append("Program name is required.")
        existing = Program.query.filter_by(name=name).first()
        if existing and (p is None or existing.id != p.id):
            errors.append("A program with that name already exists.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("admin/program_form.html", p=p,
                                   all_careers=all_careers, form=request.form)

        if p is None:
            p = Program()
            db.session.add(p)
        p.name = name
        p.degree_level = (request.form.get("degree_level") or "").strip()
        p.duration = (request.form.get("duration") or "").strip()
        p.description = (request.form.get("description") or "").strip()
        p.universities = (request.form.get("universities") or "").strip()
        p.is_active = bool(request.form.get("is_active"))

        selected = request.form.getlist("careers")
        p.careers = Career.query.filter(Career.id.in_(selected)).all() if selected else []
        db.session.commit()
        flash("Program saved.", "success")
        return redirect(url_for("admin.programs"))

    return render_template("admin/program_form.html", p=p,
                           all_careers=all_careers, form=None)


@admin_bp.route("/programs/<int:pid>/delete", methods=["POST"])
@admin_required
def program_delete(pid):
    p = db.session.get(Program, pid)
    if p:
        db.session.delete(p)
        db.session.commit()
        flash("Program deleted.", "info")
    return redirect(url_for("admin.programs"))


# ---------------------------------------------------------------------------
# Students & reports
# ---------------------------------------------------------------------------
@admin_bp.route("/students")
@admin_required
def students():
    rows = (db.session.query(User)
            .filter_by(role="student")
            .order_by(User.created_at.desc()).all())
    data = []
    for u in rows:
        attempts = u.attempts
        last = max(attempts, key=lambda a: a.created_at) if attempts else None
        data.append({"user": u, "attempts": len(attempts), "last": last})
    return render_template("admin/students.html", data=data)


@admin_bp.route("/students/<int:uid>")
@admin_required
def student_detail(uid):
    u = db.session.get(User, uid)
    if u is None or u.role != "student":
        abort(404)
    attempts = sorted(u.attempts, key=lambda a: a.created_at, reverse=True)
    return render_template("admin/student_detail.html", student=u, attempts=attempts)


@admin_bp.route("/retrain", methods=["POST"])
@admin_required
def retrain():
    """Retrain the ML model (useful after editing careers)."""
    info = train_and_save(current_app.config["MODEL_PATH"], verbose=False)
    # Reset the in-memory recommender so it reloads the new model.
    current_app.recommender._bundle = None
    flash(f"Model retrained on {info['n_samples']} samples "
          f"({info['n_careers']} careers), accuracy {info['accuracy']:.2f}.", "success")
    return redirect(url_for("admin.dashboard"))


