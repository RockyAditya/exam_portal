from flask import Flask, redirect, url_for
from config import Config
from db import close_db, get_db
import os
from werkzeug.security import generate_password_hash
from flask_login import LoginManager, UserMixin

class User(UserMixin):
    def __init__(self, id, username, role, profile_complete, branch=None):
        self.id = id
        self.username = username
        self.role = role
        self.profile_complete = profile_complete
        self.branch = branch

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    os.makedirs(os.path.join(app.root_path, 'static', 'uploads', 'assessments'), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, 'static', 'uploads', 'submissions'), exist_ok=True)

    app.teardown_appcontext(close_db)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message = "Please log in to access this page."
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        conn = get_db()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, username, role, profile_complete, branch FROM users WHERE id = %s", (user_id,))
            user_data = cursor.fetchone()
            if user_data:
                return User(
                    id=user_data['id'],
                    username=user_data['username'],
                    role=user_data['role'],
                    profile_complete=bool(user_data['profile_complete']),
                    branch=user_data['branch']
                )
        return None

    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.teacher import teacher_bp
    from routes.student import student_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(teacher_bp, url_prefix='/teacher')
    app.register_blueprint(student_bp, url_prefix='/student')

    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))

    # Initialize DB and seed admin
    with app.app_context():
        try:
            conn = get_db()
            with conn.cursor() as cursor:
                cursor.execute("SELECT id FROM users WHERE username = 'admin'")
                if not cursor.fetchone():
                    admin_hash = generate_password_hash('admin')
                    cursor.execute(
                        "INSERT INTO users (username, password_hash, role, profile_complete) VALUES (%s, %s, %s, %s)",
                        ('admin', admin_hash, 'Admin', True)
                    )
                    conn.commit()
        except pymysql.err.OperationalError as e:
            # DB probably not setup yet, ignore here - handled by manual schema init
            print("DB init error (expected if DB doesn't exist yet):", e)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
