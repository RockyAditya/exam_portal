import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime
from db import get_db

student_bp = Blueprint('student', __name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@student_bp.before_request
@login_required
def require_student():
    if current_user.role != 'Student':
        flash("Access restricted to students.", "error")
        return redirect(url_for('auth.login'))
    if not current_user.profile_complete:
        return redirect(url_for('auth.profile_setup'))

@student_bp.route('/')
def dashboard():
    conn = get_db()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM student_profiles WHERE user_id = %s", (current_user.id,))
        profile = cursor.fetchone()
        
        # Count pending assessments (assessments for branch without a submission)
        cursor.execute("""
            SELECT COUNT(a.id) as count FROM assessments a
            JOIN teacher_profiles tp ON a.teacher_id = tp.user_id
            LEFT JOIN submissions s ON s.assessment_id = a.id AND s.student_id = %s
            WHERE tp.branch = %s AND s.id IS NULL
        """, (current_user.id, current_user.branch))
        pending_assessments = cursor.fetchone()['count']
        
    return render_template('student/dashboard.html', profile=profile, pending_assessments=pending_assessments)

@student_bp.route('/assessments')
def assessments():
    conn = get_db()
    with conn.cursor() as cursor:
        # Get all assessments from teachers of the same branch
        cursor.execute("""
            SELECT a.*, tp.full_name as teacher_name, 
                   s.id as submission_id, s.grade, s.file_path as submission_file
            FROM assessments a
            JOIN teacher_profiles tp ON a.teacher_id = tp.user_id
            LEFT JOIN submissions s ON s.assessment_id = a.id AND s.student_id = %s
            WHERE tp.branch = %s
            ORDER BY a.due_date ASC
        """, (current_user.id, current_user.branch))
        assessments_list = cursor.fetchall()
        
    return render_template('student/assessments.html', assessments=assessments_list, now=datetime.now())

@student_bp.route('/assessments/submit/<int:assessment_id>', methods=['POST'])
def submit_assessment(assessment_id):
    if 'file' not in request.files:
        flash('No file provided', 'error')
        return redirect(url_for('student.assessments'))
        
    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('student.assessments'))
        
    if file and allowed_file(file.filename):
        filename = secure_filename(f"sub_{current_user.id}_{assessment_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'submissions', filename)
        file.save(os.path.join(current_app.root_path, file_path))
        
        conn = get_db()
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO submissions (assessment_id, student_id, file_path)
                VALUES (%s, %s, %s)
            """, (assessment_id, current_user.id, file_path.replace("\\", "/")))
            conn.commit()
        flash('Assignment submitted successfully!', 'success')
        
    return redirect(url_for('student.assessments'))

@student_bp.route('/grades')
def grades():
    conn = get_db()
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT s.*, a.title as assessment_title, tp.full_name as teacher_name
            FROM submissions s
            JOIN assessments a ON s.assessment_id = a.id
            JOIN teacher_profiles tp ON a.teacher_id = tp.user_id
            WHERE s.student_id = %s AND s.grade IS NOT NULL
        """, (current_user.id,))
        grades_list = cursor.fetchall()
    return render_template('student/grades.html', grades=grades_list)

@student_bp.route('/quizzes')
def quizzes():
    conn = get_db()
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT q.*, qa.id as attempt_id, qa.score, qa.total 
            FROM quizzes q
            LEFT JOIN quiz_attempts qa ON qa.quiz_id = q.id AND qa.student_id = %s
            WHERE q.branch = %s
        """, (current_user.id, current_user.branch))
        quizzes_list = cursor.fetchall()
    return render_template('student/quizzes.html', quizzes=quizzes_list)

@student_bp.route('/quizzes/<int:quiz_id>/attempt', methods=['GET', 'POST'])
def attempt_quiz(quiz_id):
    conn = get_db()
    with conn.cursor() as cursor:
        # Check if already attempted
        cursor.execute("SELECT * FROM quiz_attempts WHERE quiz_id = %s AND student_id = %s", (quiz_id, current_user.id))
        if cursor.fetchone():
            flash('You have already attempted this quiz.', 'error')
            return redirect(url_for('student.quizzes'))
            
        cursor.execute("SELECT * FROM quizzes WHERE id = %s AND branch = %s", (quiz_id, current_user.branch))
        quiz = cursor.fetchone()
        if not quiz:
            flash('Quiz not found.', 'error')
            return redirect(url_for('student.quizzes'))
            
        cursor.execute("SELECT * FROM quiz_questions WHERE quiz_id = %s", (quiz_id,))
        questions = cursor.fetchall()
        
        if request.method == 'POST':
            score = 0
            for idx, q in enumerate(questions):
                answer = request.form.get(f'q_{q["id"]}')
                if answer == q['correct_option']:
                    score += 1
            
            cursor.execute("""
                INSERT INTO quiz_attempts (quiz_id, student_id, score, total, submitted_at)
                VALUES (%s, %s, %s, %s, NOW())
            """, (quiz_id, current_user.id, score, len(questions)))
            conn.commit()
            
            flash(f'Quiz completed! Your score: {score}/{len(questions)}', 'success')
            return redirect(url_for('student.quizzes'))
            
    return render_template('student/attempt_quiz.html', quiz=quiz, questions=questions)
