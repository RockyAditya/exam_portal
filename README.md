# Exam Portal

A robust, glassmorphism-styled Flask-based web application for managing assessments, quizzes, submissions, and grading across different users (Admins, Teachers, and Students).

## Technical Stack
- **Backend:** Flask, Python, PyMySQL
- **Database:** MySQL
- **Frontend:** Vanilla HTML/CSS with Glassmorphism and CSS variables
- **Auth:** Flask-Login, Werkzeug Security

## Requirements
- Python 3.8+
- MySQL Server running on `localhost`
- Pip packages: `flask`, `pymysql`, `flask-login`, `werkzeug`

## Setup Instructions

1. **Clone/Download** this repository.
2. **Setup Virtual Environment:**
   ```bash
   python -m venv venv
   source venv/Scripts/activate  # On Windows PowerShell: .\venv\Scripts\Activate.ps1
   pip install flask pymysql flask-login werkzeug
   ```
3. **Database Initialization:**
   The base tables and the `admin` user have already been sourced. For reference, the login details for MySQL are user: `root`, password: `28299`, database: `exam_portal`. Run `schema.sql` if the DB is blank.
4. **Run Application:**
   ```bash
   python app.py
   ```
5. **Accessing:** Open browser to `http://localhost:5000`

## Default Users
- **Admin**: Username: `admin` / Password: `admin`
- **Teachers & Students**: Register via the "New Student/Teacher" links on the login screen. Profile completion is enforced on the first login.
