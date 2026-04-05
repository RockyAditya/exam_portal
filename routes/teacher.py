import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime
from db import get_db

teacher_bp = Blueprint('teacher', __name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@teacher_bp.before_request
@login_required
def require_teacher():
    if current_user.role != 'Teacher':
        flash("Access restricted to teachers.", "error")
        return redirect(url_for('auth.login'))
    if not current_user.profile_complete:
        return redirect(url_for('auth.profile_setup'))

@teacher_bp.route('/')
def dashboard():
    conn = get_db()
    with conn.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) as count FROM student_profiles WHERE branch = %s", (current_user.branch,))
        student_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM assessments WHERE teacher_id = %s", (current_user.id,))
        assessment_count = cursor.fetchone()['count']
        
    return render_template('teacher/dashboard.html', student_count=student_count, assessment_count=assessment_count)

@teacher_bp.route('/assessments', methods=['GET', 'POST'])
def assessments():
    conn = get_db()
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        due_date = request.form.get('due_date')
        
        if 'file' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)
            
        file = request.files['file']
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)
            
        if file and allowed_file(file.filename):
            filename = secure_filename(f"{current_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'assessments', filename)
            file.save(os.path.join(current_app.root_path, file_path))
            
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO assessments (teacher_id, title, description, due_date, file_path)
                    VALUES (%s, %s, %s, %s, %s)
                """, (current_user.id, title, description, due_date, file_path.replace("\\", "/")))
                conn.commit()
            flash('Assessment created successfully', 'success')
            return redirect(url_for('teacher.assessments'))

    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM assessments WHERE teacher_id = %s ORDER BY created_at DESC", (current_user.id,))
        assessments_list = cursor.fetchall()
        
    return render_template('teacher/assessments.html', assessments=assessments_list)

@teacher_bp.route('/assessments/<int:assessment_id>/submissions')
def view_submissions(assessment_id):
    conn = get_db()
    with conn.cursor() as cursor:
        # Get assessment details
        cursor.execute("SELECT * FROM assessments WHERE id = %s AND teacher_id = %s", (assessment_id, current_user.id))
        assessment = cursor.fetchone()
        if not assessment:
            flash('Assessment not found or unauthorized', 'error')
            return redirect(url_for('teacher.assessments'))
            
        cursor.execute("""
            SELECT s.*, sp.full_name, sp.roll_number
            FROM student_profiles sp
            LEFT JOIN submissions s ON s.student_id = sp.user_id AND s.assessment_id = %s
            WHERE sp.branch = %s
        """, (assessment_id, current_user.branch))
        submissions = cursor.fetchall()
        
    return render_template('teacher/submissions.html', assessment=assessment, submissions=submissions)

@teacher_bp.route('/grade/<int:submission_id>', methods=['POST'])
def grade_submission(submission_id):
    grade = request.form.get('grade')
    feedback = request.form.get('feedback')
    assessment_id = request.form.get('assessment_id')
    
    conn = get_db()
    with conn.cursor() as cursor:
        cursor.execute("""
            UPDATE submissions 
            SET grade = %s, feedback = %s, graded_at = NOW() 
            WHERE id = %s
        """, (grade, feedback, submission_id))
        conn.commit()
        
    flash('Grade updated successfully', 'success')
    return redirect(url_for('teacher.view_submissions', assessment_id=assessment_id))

@teacher_bp.route('/quizzes', methods=['GET', 'POST'])
def quizzes():
    conn = get_db()
    if request.method == 'POST':
        title = request.form.get('title')
        time_limit = request.form.get('time_limit_minutes')
        
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO quizzes (teacher_id, branch, title, time_limit_minutes) 
                VALUES (%s, %s, %s, %s)
            """, (current_user.id, current_user.branch, title, time_limit))
            quiz_id = cursor.lastrowid
            
            # Loop through questions (assuming a dynamic form submitting arrays)
            questions = request.form.getlist('question_text[]')
            opt_a = request.form.getlist('option_a[]')
            opt_b = request.form.getlist('option_b[]')
            opt_c = request.form.getlist('option_c[]')
            opt_d = request.form.getlist('option_d[]')
            correct = request.form.getlist('correct_option[]')
            
            for i in range(len(questions)):
                if questions[i].strip():
                    cursor.execute("""
                        INSERT INTO quiz_questions (quiz_id, question_text, option_a, option_b, option_c, option_d, correct_option)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (quiz_id, questions[i], opt_a[i], opt_b[i], opt_c[i], opt_d[i], correct[i]))
            conn.commit()
            flash('Quiz created successfully', 'success')
            return redirect(url_for('teacher.quizzes'))
            
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM quizzes WHERE teacher_id = %s", (current_user.id,))
        quizzes_list = cursor.fetchall()
        
    return render_template('teacher/quizzes.html', quizzes=quizzes_list)

@teacher_bp.route('/quizzes/<int:quiz_id>/results')
def quiz_results(quiz_id):
    conn = get_db()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM quizzes WHERE id = %s AND teacher_id = %s", (quiz_id, current_user.id))
        quiz = cursor.fetchone()
        
        cursor.execute("""
            SELECT qa.*, sp.full_name, sp.roll_number 
            FROM quiz_attempts qa
            JOIN student_profiles sp ON qa.student_id = sp.user_id
            WHERE qa.quiz_id = %s
        """, (quiz_id,))
        results = cursor.fetchall()
        
    return render_template('teacher/quiz_results.html', quiz=quiz, results=results)
