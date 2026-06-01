"""Authentication routes: register, login, logout."""
import re

from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user

from ..extensions import db
from ..models import User

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _validate_registration(full_name, email, password, confirm):
    errors = []
    if not full_name or len(full_name.strip()) < 2:
        errors.append("Please enter your full name.")
    if not email or not EMAIL_RE.match(email):
        errors.append("Please enter a valid email address.")
    if not password or len(password) < 6:
        errors.append("Password must be at least 6 characters long.")
    if password != confirm:
        errors.append("Passwords do not match.")
    return errors


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        full_name = (request.form.get("full_name") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        confirm = request.form.get("confirm_password") or ""

        errors = _validate_registration(full_name, email, password, confirm)
        if User.query.filter_by(email=email).first():
            errors.append("An account with that email already exists.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("auth/register.html", full_name=full_name, email=email)

        user = User(full_name=full_name, email=email, role="student")
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash("Account created successfully. Welcome aboard!", "success")
        login_user(user)
        return redirect(url_for("student.dashboard"))

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""

        user = User.query.filter_by(email=email).first()
        if user is None or not user.check_password(password):
            flash("Invalid email or password.", "danger")
            return render_template("auth/login.html", email=email)

        login_user(user, remember=bool(request.form.get("remember")))
        flash(f"Welcome back, {user.full_name.split()[0]}!", "success")
        if user.is_admin:
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("student.dashboard"))

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.index"))


