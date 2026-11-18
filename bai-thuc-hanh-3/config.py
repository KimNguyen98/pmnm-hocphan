import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
os.makedirs(INSTANCE_DIR, exist_ok=True)  # SQLite cần thư mục này tồn tại

SECRET_KEY = os.environ.get("SECRET_KEY", "doi-khoa-bi-mat-nay")
SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(INSTANCE_DIR, "bookstore.db")
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Upload ảnh bìa
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2 MB
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}