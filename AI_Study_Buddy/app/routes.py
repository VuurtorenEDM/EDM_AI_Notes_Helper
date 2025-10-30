from flask import render_template, redirect, url_for, request, flash, current_app, Blueprint 
from flask_login import login_user, logout_user, login_required, current_user
from . import db, login_manager
from .models import User, Note, Result, Quiz 
from .forms import LoginForm, RegisterForm, NoteForm
from werkzeug.security import generate_password_hash, check_password_hash
from .ai import summarize_text, generate_structured_quiz, generate_feedback
import json
from sqlalchemy import func
from sqlalchemy.orm import joinedload

# --- DEFINE THE BLUEPRINT ---
bp = Blueprint('main', __name__) 

# --- USER LOADER ---
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ------------------------------------------
# --- DASHBOARD ROUTE ---
# ------------------------------------------
@bp.route("/")
@bp.route("/dashboard")
@login_required
def dashboard():
    user_results = Result.query.filter_by(user_id=current_user.id) \
                               .order_by(Result.date_taken.desc()) \
                               .limit(10).all()
    notes = Note.query.filter_by(user_id=current_user.id).all()

    if user_results:
        reversed_results = list(reversed(user_results))
        labels = [r.date_taken.strftime("%b %d") for r in reversed_results]
        scores = [round((r.score / r.total) * 100, 2) for r in reversed_results]
        avg_score = round(sum(scores) / len(scores), 2)
    else:
        labels = []
        scores = []
        avg_score = 0

    return render_template(
        "dashboard.html",
        notes=notes,
        results=user_results,
        labels=labels,
        scores=scores,
        avg_score=avg_score
    )

# ------------------------------------------
# --- RESTORED LOGIC ROUTES ---
# ------------------------------------------

@bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            return redirect(url_for("main.dashboard"))
        flash("Invalid credentials.")
    return render_template("login.html", form=form)

@bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed = generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password_hash=hashed)
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful! Please log in.")
        return redirect(url_for("main.login"))
    return render_template("register.html", form=form)

@bp.route("/notes/new", methods=["GET", "POST"])
@login_required
def new_note():
    form = NoteForm()
    if form.validate_on_submit():
        note = Note(user_id=current_user.id, title=form.title.data, content=form.content.data)
        db.session.add(note)
        db.session.commit()
        flash("Note saved successfully.")
        return redirect(url_for("main.dashboard"))
    return render_template("notes.html", form=form)

@bp.route("/summarize/<int:note_id>", methods=["POST"])
@login_required
def summarize(note_id):
    note = Note.query.get_or_404(note_id)
    summary = summarize_text(note.content)
    note.summary = summary
    db.session.commit()
    flash("AI summary generated successfully!")
    return redirect(url_for("main.note_detail", note_id=note.id))

@bp.route("/take_quiz/<int:quiz_id>", methods=["GET", "POST"])
@login_required
def take_quiz(quiz_id):
    # 💥 FIX APPLIED: Use joinedload to pre-load the 'note' relationship
    quiz = Quiz.query.options(joinedload(Quiz.note)).get_or_404(quiz_id)
    
    # ⚠️ Data Fix (Based on previous error context):
    # The get_questions() method in models.py MUST correctly parse the JSON string.
    questions = quiz.get_questions() 

    if request.method == "POST":
        score = 0
        total = len(questions)
        user_answers = []
        correct_answers = []

        for i, q in enumerate(questions):
            # This logic assumes your form fields are named q0, q1, q2, etc.
            # NOTE: The client-side template (take_quiz.html) uses loop.parent.index0 for the name attribute.
            user_answer = request.form.get(f"q{i}") 
            user_answers.append(user_answer)
            
            correct_answers.append(q["answer"])
            if user_answer == q["answer"]:
                score += 1

        feedback = generate_feedback(
            # This relies on the quiz.note relationship, which is now pre-loaded:
            note_title=quiz.note.title if quiz.note else "Unknown Topic",
            questions=[q["question"] for q in questions],
            user_answers=user_answers,
            correct_answers=correct_answers,
            score=score,
            total=total
        )

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
        return redirect(url_for("main.view_result", result_id=new_result.id))

    return render_template("take_quiz.html", quiz=quiz, questions=questions)


@bp.route("/note/<int:note_id>")
@login_required
def note_detail(note_id):
    note = Note.query.get_or_404(note_id)
    return render_template("note_detail.html", note=note)

@bp.route("/quiz/<int:quiz_id>")
@login_required
def quiz_view(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    return render_template("quiz.html", quiz=quiz)

@bp.route("/result/<int:result_id>")
@login_required
def view_result(result_id):
    result = Result.query.get_or_404(result_id)
    if result.user_id != current_user.id:
        flash("Unauthorized access.")
        return redirect(url_for("main.dashboard"))
    return render_template("view_result.html", result=result)

@bp.route('/logout')
@login_required 
def logout():
    logout_user() 
    flash("You have been logged out.")
    return redirect(url_for('main.login'))

@bp.route("/quiz/generate/<int:note_id>", methods=["GET", "POST"])
@login_required
def quiz_generate(note_id):
    note = Note.query.get_or_404(note_id)
    if note.user_id != current_user.id:
        flash("Unauthorized access to generate quiz.")
        return redirect(url_for("main.dashboard"))
    
    # 1. Generate the Python list/dict structure
    quiz_data_python_list = generate_structured_quiz(note.content)
    
    # 2. Convert the Python list/dict structure to a JSON string
    quiz_data_json_string = json.dumps(quiz_data_python_list) 
    
    new_quiz = Quiz(
        note_id=note.id, 
        user_id=current_user.id, 
        # 2. Pass the JSON string to the database column
        questions_json=quiz_data_json_string
    )
    
    db.session.add(new_quiz)
    db.session.commit()
    
    flash("AI Quiz generated successfully!")
    return redirect(url_for("main.quiz_view", quiz_id=new_quiz.id))
    
    db.session.add(new_quiz)
    db.session.commit()
    
    flash("AI Quiz generated successfully!")
    return redirect(url_for("main.quiz_view", quiz_id=new_quiz.id))
    
    db.session.add(new_quiz)
    db.session.commit()
    
    flash("AI Quiz generated successfully!")
    return redirect(url_for("main.quiz_view", quiz_id=new_quiz.id))