from flask import render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from . import db, login_manager
from .models import User, Note, Result
from .forms import LoginForm, RegisterForm, NoteForm
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Blueprint
from .ai import summarize_text, generate_structured_quiz, generate_feedback
import json
from sqlalchemy import func

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Basic routes
from flask import current_app as app

@app.route("/")
@login_required
def dashboard():
    notes = Note.query.filter_by(user_id=current_user.id).all()
    return render_template("dashboard.html", notes=notes)

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            return redirect(url_for("dashboard"))
        flash("Invalid credentials.")
    return render_template("login.html", form=form)

@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed = generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password_hash=hashed)
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful! Please log in.")
        return redirect(url_for("login"))
    return render_template("register.html", form=form)

@app.route("/notes/new", methods=["GET", "POST"])
@login_required
def new_note():
    form = NoteForm()
    if form.validate_on_submit():
        note = Note(user_id=current_user.id, title=form.title.data, content=form.content.data)
        db.session.add(note)
        db.session.commit()
        flash("Note saved successfully.")
        return redirect(url_for("dashboard"))
    return render_template("notes.html", form=form)

@app.route("/summarize/<int:note_id>", methods=["POST"])
@login_required
def summarize(note_id):
    note = Note.query.get_or_404(note_id)
    summary = summarize_text(note.content)
    note.summary = summary
    db.session.commit()
    flash("AI summary generated successfully!")
    return redirect(url_for("note_detail", note_id=note.id))

from .ai import generate_feedback

@app.route("/take_quiz/<int:quiz_id>", methods=["GET", "POST"])
@login_required
def take_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = quiz.get_questions()

    if request.method == "POST":
        score = 0
        total = len(questions)
        user_answers = []
        correct_answers = []

        for i, q in enumerate(questions):
            user_answer = request.form.get(f"q{i}")
            user_answers.append(user_answer)
            correct_answers.append(q["answer"])
            if user_answer == q["answer"]:
                score += 1

        # Generate feedback via AI
        feedback = generate_feedback(
            note_title=quiz.note.title if quiz.note else "Unknown Topic",
            questions=[q["question"] for q in questions],
            user_answers=user_answers,
            correct_answers=correct_answers,
            score=score,
            total=total
        )

        # Save the result
        new_result = Result(
            user_id=current_user.id,
            quiz_id=quiz.id,
            score=score,
            total=total,
            feedback=feedback
        )
        db.session.add(new_result)
        db.session.commit()

        flash(f"You scored {score}/{total}! AI feedback generated below.")
        return redirect(url_for("view_result", result_id=new_result.id))

    return render_template("take_quiz.html", quiz=quiz, questions=questions)


@app.route("/note/<int:note_id>")
@login_required
def note_detail(note_id):
    note = Note.query.get_or_404(note_id)
    return render_template("note_detail.html", note=note)

@app.route("/quiz/<int:quiz_id>")
@login_required
def quiz_view(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    return render_template("quiz.html", quiz=quiz)

@app.route("/dashboard")
@login_required
def dashboard():
    user_results = Result.query.filter_by(user_id=current_user.id).order_by(Result.date_taken.desc()).limit(10).all()
    
    # Prepare data for chart
    labels = [r.date_taken.strftime("%b %d") for r in reversed(user_results)]
    scores = [round((r.score / r.total) * 100, 2) for r in reversed(user_results)]
    avg_score = round(sum(scores) / len(scores), 2) if scores else 0

    return render_template(
        "dashboard.html",
        results=user_results,
        labels=labels,
        scores=scores,
        avg_score=avg_score
    )

@app.route("/result/<int:result_id>")
@login_required
def view_result(result_id):
    result = Result.query.get_or_404(result_id)
    if result.user_id != current_user.id:
        flash("Unauthorized access.")
        return redirect(url_for("dashboard"))
    return render_template("view_result.html", result=result)
