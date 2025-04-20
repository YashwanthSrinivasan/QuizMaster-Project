import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(32), unique=True)
    passhash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(64), nullable=True)
    qualification = db.Column(db.String(256), nullable=True)
    dob = db.Column(db.Date, nullable=True)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)

class Subject(db.Model):
    __tablename__ = "subject"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(256), nullable=True)
    chapters = db.relationship('Chapter', backref='subject', cascade="all, delete", lazy=True)

class Chapter(db.Model):
    __tablename__ = "chapter"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(256), nullable=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id', ondelete='CASCADE'), nullable=False)
    quizzes = db.relationship('Quiz', backref='chapter', cascade="all, delete", lazy=True)

class Quiz(db.Model):
    __tablename__ = "quiz"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    duration = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date, nullable=False, default=db.func.current_date())
    remarks = db.Column(db.String(256), nullable=True)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id', ondelete='CASCADE'), nullable=False)
    questions = db.relationship('Question', backref='quiz', cascade="all, delete", lazy=True)
    scores = db.relationship('Scores', backref='quiz', cascade='all, delete-orphan')
    published=db.Column(db.Boolean, nullable=False, default=False)

class Question(db.Model):
    __tablename__ = "question"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    question = db.Column(db.String(256), nullable=False)
    option1 = db.Column(db.String(256), nullable=False)
    option2 = db.Column(db.String(256), nullable=False)
    option3 = db.Column(db.String(256), nullable=False)
    option4 = db.Column(db.String(256), nullable=False)
    answer = db.Column(db.Integer, nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)

class Scores(db.Model):
    __tablename__ = "scores"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    score = db.Column(db.Integer, nullable=False, default=0)
    timeofattempt = db.Column(db.DateTime, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('scores', lazy=True))
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)


def init_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()
        admin = User.query.filter_by(is_admin=True).first()
        if not admin:
            passhash = generate_password_hash('admin')
            admin = User(username='admin', passhash=passhash, name='Admin', is_admin=True)
            db.session.add(admin)
            db.session.commit()