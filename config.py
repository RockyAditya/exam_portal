import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "super_secret_exam_portal_key_2026")
    DB_HOST = "localhost"
    DB_USER = "root"
    DB_PASS = "28299"
    DB_NAME = "exam_portal"
    UPLOAD_FOLDER = os.path.join("static", "uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max limit for uploads
    
    # Allowed extensions
    ALLOWED_EXTENSIONS = {'pdf', 'docx'}
