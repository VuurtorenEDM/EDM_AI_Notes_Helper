from . import db
from flask_login import UserMixin
from datetime import datetime
import json


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    notes = db.relationship("Note", backref="user", lazy=True)
    results = db.relationship("Result", backref="user", lazy=True)

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    content = db.Column(db.Text, nullable=False)
    summary = db.Column(db.Text)
    date_added = db.Column(db.DateTime)
    quizzes = db.relationship("Quiz", backref="note", lazy=True)


class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    note_id = db.Column(db.Integer, db.ForeignKey("note.id"), nullable=False)
    question = db.Column(db.Text, nullable=False)
    questions_json = db.Column(db.Text, nullable=False)  # store list of dicts
    options = db.Column(db.Text)
    correct_answer = db.Column(db.String(255))
    date_created = db.Column(db.DateTime)
    
    def get_questions(self):
        """Return parsed list of questions."""
        return json.loads(self.questions_json)
    
class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quiz.id"), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    total = db.Column(db.Integer, nullable=False)
    date_taken = db.Column(db.DateTime, default=datetime.utcnow)
    feedback = db.Column(db.Text)  # new field

    quiz = db.relationship("Quiz", backref="results", lazy=True)