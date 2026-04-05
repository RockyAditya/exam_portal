from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from db import get_db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect_based_on_role(current_user)

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        conn = get_db()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            
            if user and check_password_hash(user['password_hash'], password):
                from app import User
                u = User(user['id'], user['username'], user['role'], bool(user['profile_complete']), user['branch'])
                login_user(u)
                if not u.profile_complete and u.role != 'Admin':
                    return redirect(url_for('auth.profile_setup'))
                return redirect_based_on_role(u)
            else:
                flash("Invalid username or password.", "error")
                
    return render_template('login.html', is_register=False)

def redirect_based_on_role(user):
    if user.role == 'Admin':
        return redirect(url_for('admin.dashboard'))
    elif user.role == 'Teacher':
        return redirect(url_for('teacher.dashboard'))
    elif user.role == 'Student':
        return redirect(url_for('student.dashboard'))
    return redirect(url_for('auth.login'))

@auth_bp.route('/register/student', methods=['GET', 'POST'])
def register_student():
    if current_user.is_authenticated:
        return redirect_based_on_role(current_user)
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = get_db()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                flash("Username already exists.", "error")
                return redirect(url_for('auth.register_student'))
                
            hashed_pw = generate_password_hash(password)
            cursor.execute(
                "INSERT INTO users (username, password_hash, role, profile_complete) VALUES (%s, %s, %s, %s)",
                (username, hashed_pw, 'Student', False)
            )
            conn.commit()
            flash("Registration successful. Please log in.", "success")
            return redirect(url_for('auth.login'))
            
    return render_template('login.html', is_register=True, role='student')

@auth_bp.route('/register/teacher', methods=['GET', 'POST'])
def register_teacher():
    if current_user.is_authenticated:
        return redirect_based_on_role(current_user)
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = get_db()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                flash("Username already exists.", "error")
                return redirect(url_for('auth.register_teacher'))
                
            hashed_pw = generate_password_hash(password)
            cursor.execute(
                "INSERT INTO users (username, password_hash, role, profile_complete) VALUES (%s, %s, %s, %s)",
                (username, hashed_pw, 'Teacher', False)
            )
            conn.commit()
            flash("Registration successful. Please log in.", "success")
            return redirect(url_for('auth.login'))
            
    return render_template('login.html', is_register=True, role='teacher')

@auth_bp.route('/profile_setup', methods=['GET', 'POST'])
@login_required
def profile_setup():
    if current_user.profile_complete:
        return redirect_based_on_role(current_user)

    if request.method == 'POST':
        conn = get_db()
        with conn.cursor() as cursor:
            if current_user.role == 'Student':
                full_name = request.form.get('full_name')
                roll_number = request.form.get('roll_number')
                branch = request.form.get('branch')
                age = request.form.get('age')
                course = request.form.get('course')
                phone = request.form.get('phone')
                parent_phone = request.form.get('parent_phone')
                
                cursor.execute("SELECT user_id FROM student_profiles WHERE full_name = %s OR roll_number = %s", (full_name, roll_number))
                if cursor.fetchone():
                    flash("Name or Roll Number already registered.", "error")
                    return redirect(url_for('auth.profile_setup'))
                
                cursor.execute("""
                    INSERT INTO student_profiles (user_id, full_name, roll_number, branch, age, course, phone, parent_phone)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (current_user.id, full_name, roll_number, branch, age, course, phone, parent_phone))
                
                cursor.execute("UPDATE users SET profile_complete = 1, branch = %s WHERE id = %s", (branch, current_user.id))
                
            elif current_user.role == 'Teacher':
                full_name = request.form.get('full_name')
                employee_id = request.form.get('employee_id')
                branch = request.form.get('branch')
                phone = request.form.get('phone')
                
                cursor.execute("SELECT user_id FROM teacher_profiles WHERE full_name = %s OR employee_id = %s", (full_name, employee_id))
                if cursor.fetchone():
                    flash("Name or Employee ID already registered.", "error")
                    return redirect(url_for('auth.profile_setup'))
                    
                cursor.execute("""
                    INSERT INTO teacher_profiles (user_id, full_name, employee_id, branch, phone)
                    VALUES (%s, %s, %s, %s, %s)
                """, (current_user.id, full_name, employee_id, branch, phone))
                
                cursor.execute("UPDATE users SET profile_complete = 1, branch = %s WHERE id = %s", (branch, current_user.id))
                
            conn.commit()
            
            current_user.profile_complete = True
            current_user.branch = request.form.get('branch')
            
            flash("Profile updated successfully!", "success")
            return redirect_based_on_role(current_user)

    return render_template('profile_setup.html', role=current_user.role)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for('auth.login'))
