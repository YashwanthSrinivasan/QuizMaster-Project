from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import db, User, Subject, Chapter, Quiz, Question, Scores
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from sqlalchemy.sql import func, cast
from datetime import date, datetime, timedelta
from uuid import uuid4
import math

main = Blueprint('main', __name__)


def auth_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if 'user_id' in session:
            return func(*args, **kwargs)
        else:
            flash('Please login to continue')
            return redirect(url_for('main.login'))
    return inner

def admin_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to continue')
            return redirect(url_for('main.login'))
        user = User.query.get(session['user_id'])
        if not user.is_admin:
            flash('You are not authorized to access this page')
            return redirect(url_for('main.index'))
        return func(*args, **kwargs)
    return inner

@main.route('/')
def index():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user.is_admin:
            return redirect(url_for('main.adminhome'))
        else:
            return redirect(url_for('main.home'))
    
    return redirect(url_for('main.login'))

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            flash('Please fill out all fields')
            return redirect(url_for('main.login'))
        
        user = User.query.filter_by(username=username).first()
        
        if not user:
            flash('Username does not exist')
            return redirect(url_for('main.login'))
        
        if not check_password_hash(user.passhash, password):
            flash('Incorrect password')
            return redirect(url_for('main.login'))
        
        session['user_id'] = user.id
        if user.is_admin:
            return redirect(url_for('main.adminhome'))
        else:
            return redirect(url_for('main.home'))


@main.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        name = request.form.get('name')
        qualification = request.form.get('qualification')
        dob = request.form.get('dob')

        if not username or not password or not confirm_password or not name:
            flash('Please fill out all fields')
            return redirect(url_for('main.register'))
        
        if password != confirm_password:
            flash('Passwords do not match')
            return redirect(url_for('main.register'))
        
        user = User.query.filter_by(username=username).first()

        if user:
            flash('Username already exists')
            return redirect(url_for('main.register'))
        
        password_hash = generate_password_hash(password)
        
        new_user = User(username=username, passhash=password_hash, name=name, qualification=qualification, dob=dob)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please login.')
        return redirect(url_for('main.login'))

@main.route('/logout')
@auth_required
def logout():
    session.pop('user_id')
    return redirect(url_for('main.login'))


##Admin Interface

@main.route('/adminhome')
@auth_required
@admin_required
def adminhome():
    user = User.query.get(session['user_id'])
    return render_template('admin/adminhome.html', user=user, subjects=Subject.query.all())

@main.route('/search', methods=['POST'])
@admin_required
def search():
    if request.method == 'POST':
        search = request.form['searchq']
        if not search:
            return redirect(url_for('main.adminhome'))
        users=User.query.filter(User.name.contains(search)).all()
        subjects = Subject.query.filter(Subject.name.contains(search)).all()
        chapters = Chapter.query.filter(Chapter.name.contains(search)).all()
        quizzes = Quiz.query.filter(Quiz.remarks.contains(search)).all()
        return render_template('admin/search.html', subjects=subjects, chapters=chapters, quizzes=quizzes, users=users, search=search)
    return render_template('admin/search.html')

@main.route('/addsubject', methods=['GET', 'POST'])
@admin_required
def addsubject():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']

        existing_subject = Subject.query.filter_by(name=name).first()

        if existing_subject:
            flash('Same subject aldready Exists')
            return redirect(url_for('main.adminhome'))
        
        new_subject = Subject(name=name, description=description)
        db.session.add(new_subject)
        db.session.commit()
        flash('Success: Subject added')
        return redirect(url_for('main.adminhome') + '#' + str(new_subject.id))

@main.route('/deletesubject<int:id>')
@admin_required
def deletesubject(id):
    subject = Subject.query.get(id)
    db.session.delete(subject)
    db.session.commit()
    return redirect(url_for('main.adminhome'))

@main.route('/updatesubject<int:id>', methods=['GET', 'POST'])
@admin_required
def updatesubject(id):
    subject = Subject.query.get(id)
    if request.method == 'POST':
        subject.name = request.form['name']
        subject.description = request.form['description']
        db.session.commit()
        return redirect(url_for('main.adminhome') + '#' + str(subject.id))

@main.route('/chapter<int:id>', methods=['GET'])
@admin_required
def chapter(id):
    chapter = Chapter.query.get(id)
    subject = Subject.query.get(chapter.subject_id)
    return render_template('admin/chapter.html', chapter=chapter, subject=subject)

@main.route('/addchapter-sub<int:id>', methods=['GET', 'POST'])
@admin_required
def addchapter(id):
    subject = Subject.query.get(id)
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        
        new_chapter = Chapter(name=name, description=description, subject_id=id)
        db.session.add(new_chapter)
        db.session.commit()
        flash('Success: Chapter added')
        return redirect(url_for('main.adminhome') + '#' + str(subject.id))

@main.route('/deletechapter<int:id>')
@admin_required
def deletechapter(id):
    chapter = Chapter.query.get(id)
    subject = Subject.query.get(chapter.subject_id)
    db.session.delete(chapter)
    db.session.commit()
    return redirect(url_for('main.adminhome') + '#' + str(subject.id))

@main.route('/updatechapter<int:id>', methods=['GET', 'POST'])
@admin_required
def updatechapter(id):
    chapter = Chapter.query.get(id)
    if request.method == 'POST':
        subject = Subject.query.get(chapter.subject_id)
        chapter.name = request.form['name']
        chapter.description = request.form['description']
        db.session.commit()
        return redirect(url_for('main.adminhome') + '#' + str(subject.id))

@main.route('/quiz<int:id>', methods=['GET'])
@admin_required
def quiz(id):
    quiz = Quiz.query.get(id)
    chapter = Chapter.query.get(quiz.chapter_id)
    return render_template('admin/quiz.html', quiz=quiz, chapter=chapter)

@main.route('/addquiz-ch<int:id>', methods=['GET', 'POST'])
@admin_required
def addquiz(id):
    if request.method == 'POST':
        hr = int(request.form['hrs'])
        min = int(request.form['min'])
        duration = hr * 60 + min
        remarks = request.form['remarks']
        date = request.form['date']
        if date<datetime.now().strftime('%Y-%m-%d'):
            flash('Please select a valid upcomming date')
            return redirect(url_for('main.chapter', id=id))
        qdate = datetime.strptime(date, '%Y-%m-%d').date()
        new_quiz = Quiz(duration=duration, remarks=remarks, chapter_id=id, date=qdate)
        db.session.add(new_quiz)
        db.session.commit()
        flash('Success: Quiz added')
        return redirect(url_for('main.quiz', id=new_quiz.id))


@main.route('/deletequiz<int:id>')
@admin_required
def deletequiz(id):
    quiz = Quiz.query.get(id)
    db.session.delete(quiz)
    db.session.commit()
    chapter = Chapter.query.get(quiz.chapter_id)
    subject = Subject.query.get(chapter.subject_id)
    return render_template('admin/chapter.html', chapter=chapter, subject=subject)

@main.route('/updatequiz<int:id>', methods=['GET', 'POST'])
@admin_required
def updatequiz(id):
    quiz = Quiz.query.get(id)
    hrs=quiz.duration//60
    min=quiz.duration%60
    if request.method == 'POST':
        hr = int(request.form['hrs'])
        min = int(request.form['min'])
        quiz.duration = hr * 60 + min
        quiz.remarks = request.form['remarks']
        qdate = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        quiz.date = qdate
        db.session.commit()
        chapter = Chapter.query.get(quiz.chapter_id)
        subject = Subject.query.get(chapter.subject_id)
        return render_template('admin/chapter.html', chapter=chapter, subject=subject)


@main.route('/publishquiz<int:id>', methods=['GET'])
@admin_required
def publishquiz(id):
    quiz = Quiz.query.get(id)
    quiz.published = True
    db.session.commit()
    chapter = Chapter.query.get(quiz.chapter_id)
    subject = Subject.query.get(chapter.subject_id)
    flash('Success: Quiz published')
    return render_template('admin/chapter.html', chapter=chapter, subject=subject)


@main.route('/addquestion-qz<int:id>', methods=['GET', 'POST'])
@admin_required
def addquestion(id):
    if request.method == 'POST':
        question = request.form['question']
        option1 = request.form['option1']
        option2 = request.form['option2']
        option3 = request.form['option3']
        option4 = request.form['option4']
        answer = request.form['answer']
        
        new_question = Question(question=question, option1=option1, option2=option2, option3=option3, option4=option4, answer=answer, quiz_id=id)
        db.session.add(new_question)
        db.session.commit()
        return redirect(url_for('main.quiz', id=id))
    

@main.route('/deletequestion<int:id>')
@admin_required
def deletequestion(id):
    question = Question.query.get(id)
    quiz = Quiz.query.get(question.quiz_id)
    db.session.delete(question)
    db.session.commit()
    return redirect(url_for('main.quiz', id=quiz.id))

@main.route('/updatequestion<int:id>', methods=['GET', 'POST'])
@admin_required
def updatequestion(id):
    question = Question.query.get(id)
    quiz = Quiz.query.get(question.quiz_id)
    if request.method == 'POST':
        question.question = request.form['question']
        question.option1 = request.form['option1']
        question.option2 = request.form['option2']
        question.option3 = request.form['option3']
        question.option4 = request.form['option4']
        question.answer = request.form['answer']
        db.session.commit()
        return redirect(url_for('main.quiz', id=quiz.id))


@main.route('/quizzes', methods=['GET'])
@admin_required
def quizzes():
    Subjects = Subject.query.all()
    chapters = Chapter.query.all()
    quizzes = Quiz.query.order_by(Quiz.date.asc()).all()
    return render_template('admin/quizzes.html', subjects=Subjects, chapters=chapters, quizzes=quizzes)

@main.route('/summary', methods=['GET'])
@admin_required
def summary():
    subjects = Subject.query.all()
    quizzes = Quiz.query.all()
    subquery = (
        db.session.query(
            Question.quiz_id,
            func.count(Question.id).label("total_questions")
        )
        .group_by(Question.quiz_id)
        .subquery()
    )

    attempted_quizzes = []
    average_scores = []
    top_scores = []
    for subject in subjects:
        num_attempted = (
            db.session.query(func.count(Scores.id))
            .join(Quiz, Scores.quiz_id == Quiz.id)
            .join(Chapter, Quiz.chapter_id == Chapter.id)
            .filter( Chapter.subject_id == subject.id)
            .scalar()
        )
        attempted_quizzes.append((subject.name, num_attempted))

        avg_score_query = (
            db.session.query(
                func.avg((Scores.score / cast(subquery.c.total_questions, db.Float)) * 100)
            )
            .join(subquery, Scores.quiz_id == subquery.c.quiz_id)
            .join(Quiz, Scores.quiz_id == Quiz.id)
            .join(Chapter, Quiz.chapter_id == Chapter.id)
            .filter(Chapter.subject_id == subject.id)
            .scalar()
        )

        avg_score = round(avg_score_query, 2) if avg_score_query is not None else 0
        average_scores.append((subject.name, avg_score))
        
        top_score_query = (
            db.session.query(
                func.max((Scores.score / cast(subquery.c.total_questions, db.Float)) * 100)
            )
            .join(subquery, Scores.quiz_id == subquery.c.quiz_id)
            .join(Quiz, Scores.quiz_id == Quiz.id)
            .join(Chapter, Quiz.chapter_id == Chapter.id)
            .filter(Chapter.subject_id == subject.id)
            .scalar()
        )

        top_score = round(top_score_query, 2) if top_score_query is not None else 0
        top_scores.append((subject.name, top_score))


    return render_template(
        'admin/summary.html',
        attempted_quizzes=attempted_quizzes,
        average_scores=average_scores,
        top_scores=top_scores,
        quizzes=quizzes,
        subjects=subjects
    )


##User Interface

@main.route('/home')
@auth_required
def home():
    user = User.query.get(session['user_id'])
    current_date = date.today()
    quizzes = Quiz.query.filter(Quiz.published == True, Quiz.date >= current_date).order_by(Quiz.date.asc()).all()
    return render_template('user/home.html', user=user, subjects=Subject.query.all(), quizzes=quizzes, current_date=current_date)

        
@main.route('/userchapter<int:id>', methods=['GET'])
@auth_required
def userchapter(id):
    user = User.query.get(session['user_id'])
    current_date = date.today()
    past_quizzes = Quiz.query.filter(Quiz.chapter_id == id, Quiz.date < current_date).order_by(Quiz.date.desc()).all()
    upcoming_quizzes = Quiz.query.filter(Quiz.chapter_id == id, Quiz.date >= current_date).order_by(Quiz.date.asc()).all()
    return render_template('user/chapter.html', user=user, chapter=Chapter.query.get(id), current_date=current_date,past_quizzes=past_quizzes, upcoming_quizzes=upcoming_quizzes)


@main.route('/attemptquiz<int:id>', methods=['GET','POST'])
@auth_required
def attemptquiz(id):
    user = User.query.get(session['user_id'])
    quiz = Quiz.query.get(id)
    if quiz.date != date.today() or quiz.published == False:
        flash('Quiz not available')
        return redirect(url_for('main.home'))
    
    if 'quiz_start_time' not in session:
        session['quiz_start_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    sttime = datetime.strptime(session['quiz_start_time'], '%Y-%m-%d %H:%M:%S')
    endtime = sttime + timedelta(seconds=quiz.duration*60)
    remtime = int(max((endtime - datetime.now()).total_seconds(), 0)) 
    
    if request.method == 'POST':
        score=0
        for question in quiz.questions:
            user_answer = request.form.get(f'ans{question.id}')
            if user_answer == str(question.answer):
                score += 1
        
        new_score = Scores(user_id=user.id, quiz_id=quiz.id, score=score, timeofattempt=datetime.now().replace(microsecond=0))
        db.session.add(new_score)
        db.session.commit()
        session.pop('quiz_start_time', None)
        return redirect(url_for('main.qscore', id=quiz.id))
    
    return render_template('user/attemptquiz.html', user=user, quiz=quiz, remtime=remtime)



@main.route('/scorelog')
@auth_required
def scorelog():
    user = User.query.get(session['user_id'])
    scores = Scores.query.filter_by(user_id=user.id).order_by(Scores.timeofattempt.desc()).all()
    return render_template('user/scorelog.html', user=user, scores=scores)

@main.route('/qscore<int:id>')
@auth_required
def qscore(id):
    user = User.query.get(session['user_id'])
    quiz = Quiz.query.get(id)
    scores = Scores.query.filter_by(user_id=user.id, quiz_id=id).order_by(Scores.timeofattempt.desc()).all()
    if scores:
        maxscore = math.ceil((max(scores, key=lambda x: x.score).score)*100)/100
        avg = math.ceil((sum([score.score for score in scores])/len(scores))*100)/100 if scores else 0
    else:
        maxscore = 0
        avg = 0
    return render_template('user/qscore.html', user=user, quiz=quiz, scores=scores, maxscore=maxscore, avg=avg)

@main.route('/usummary')
@auth_required
def usummary():
    user = User.query.get(session['user_id'])
    subjects = Subject.query.all()

    subquery = (
        db.session.query(
            Question.quiz_id,
            func.count(Question.id).label("total_questions")
        )
        .group_by(Question.quiz_id)
        .subquery()
    )

    attempted_quizzes = []
    average_scores = []
    for subject in subjects:
        num_attempted = (
            db.session.query(func.count(Scores.id))
            .join(Quiz, Scores.quiz_id == Quiz.id)
            .join(Chapter, Quiz.chapter_id == Chapter.id)
            .filter(Scores.user_id == user.id, Chapter.subject_id == subject.id)
            .scalar()
        )
        attempted_quizzes.append((subject.name, num_attempted))

        avg_score_query = (
            db.session.query(
                func.avg((Scores.score / cast(subquery.c.total_questions, db.Float)) * 100)
            )
            .join(subquery, Scores.quiz_id == subquery.c.quiz_id)
            .join(Quiz, Scores.quiz_id == Quiz.id)
            .join(Chapter, Quiz.chapter_id == Chapter.id)
            .filter(Scores.user_id == user.id, Chapter.subject_id == subject.id)
            .scalar()
        )

        avg_score = round(avg_score_query, 2) if avg_score_query is not None else 0
        average_scores.append((subject.name, avg_score))


    max_score = (
        db.session.query(func.max((Scores.score / cast(subquery.c.total_questions, db.Float)) * 100))
        .join(subquery, Scores.quiz_id == subquery.c.quiz_id)
        .filter(Scores.user_id == user.id)
        .scalar()
    )

    min_score = (
        db.session.query(func.min((Scores.score / cast(subquery.c.total_questions, db.Float)) * 100))
        .join(subquery, Scores.quiz_id == subquery.c.quiz_id)
        .filter(Scores.user_id == user.id)
        .scalar()
    )

    avg_score = (
        db.session.query(func.avg((Scores.score / cast(subquery.c.total_questions, db.Float)) * 100))
        .join(subquery, Scores.quiz_id == subquery.c.quiz_id)
        .filter(Scores.user_id == user.id)
        .scalar()
    )

    max_score = round(max_score, 2) if max_score is not None else 0
    min_score = round(min_score, 2) if min_score is not None else 0
    avg_score = round(avg_score, 2) if avg_score is not None else 0

    return render_template(
        'user/usummary.html', 
        user=user,
        attempted_quizzes=attempted_quizzes,
        average_scores=average_scores,
        max_score=max_score,
        min_score=min_score,
        avg_score=avg_score
    )