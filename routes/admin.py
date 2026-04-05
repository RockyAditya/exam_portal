from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from db import get_db

admin_bp = Blueprint('admin', __name__)

@admin_bp.before_request
@login_required
def require_admin():
    if current_user.role != 'Admin':
        flash("You do not have permission to view that page.", "error")
        return redirect(url_for('auth.login'))

@admin_bp.route('/')
def dashboard():
    conn = get_db()
    with conn.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) as count FROM users WHERE role = 'Student'")
        student_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM users WHERE role = 'Teacher'")
        teacher_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(DISTINCT branch) as count FROM users WHERE branch IS NOT NULL")
        branch_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM assessments")
        assessment_count = cursor.fetchone()['count']
        
        # Latest submissions
        cursor.execute("""
            SELECT s.id, s.submitted_at, s.grade, a.title as assessment_title, sp.full_name as student_name
            FROM submissions s
            JOIN assessments a ON s.assessment_id = a.id
            JOIN student_profiles sp ON s.student_id = sp.user_id
            ORDER BY s.submitted_at DESC LIMIT 5
        """)
        submissions = cursor.fetchall()
        
    return render_template('admin/dashboard.html', 
                            student_count=student_count, 
                            teacher_count=teacher_count, 
                            branch_count=branch_count,
                            assessment_count=assessment_count,
                            submissions=submissions)

@admin_bp.route('/users')
def users():
    conn = get_db()
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT u.id, u.username, u.role, u.branch, u.profile_complete,
                   COALESCE(sp.full_name, tp.full_name) as full_name
            FROM users u
            LEFT JOIN student_profiles sp ON u.id = sp.user_id
            LEFT JOIN teacher_profiles tp ON u.id = tp.user_id
            WHERE u.role != 'Admin'
        """)
        users_list = cursor.fetchall()
    return render_template('admin/users.html', users=users_list)

@admin_bp.route('/users/delete/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    conn = get_db()
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
    flash("User deleted.", "success")
    return redirect(url_for('admin.users'))

@admin_bp.route('/assessments')
def assessments():
    conn = get_db()
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT a.*, tp.full_name as teacher_name 
            FROM assessments a
            JOIN teacher_profiles tp ON a.teacher_id = tp.user_id
        """)
        assessments_list = cursor.fetchall()
    return render_template('admin/assessments.html', assessments=assessments_list)

@admin_bp.route('/assessments/delete/<int:assessment_id>', methods=['POST'])
def delete_assessment(assessment_id):
    conn = get_db()
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM assessments WHERE id = %s", (assessment_id,))
        conn.commit()
    flash("Assessment deleted.", "success")
    return redirect(url_for('admin.assessments'))
