from flask import render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from . import db, login_manager
from .models import User, Note
from .forms import LoginForm, RegisterForm, NoteForm
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Blueprint
from .ai import summarize_text, generate_quiz  # import AI functions

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

@app.route("/generate_quiz/<int:note_id>", methods=["POST"])
@login_required
def quiz_generate(note_id):
    note = Note.query.get_or_404(note_id)
    quiz_text = generate_quiz(note.content)

    # Save quiz as raw text for now
    new_quiz = Quiz(note_id=note.id, question=quiz_text)
    db.session.add(new_quiz)
    db.session.commit()

    flash("Quiz generated successfully!")
    return redirect(url_for("quiz_view", quiz_id=new_quiz.id))

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

