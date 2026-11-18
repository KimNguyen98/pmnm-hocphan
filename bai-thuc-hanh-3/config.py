import os
import secrets

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
os.makedirs(INSTANCE_DIR, exist_ok=True)  # SQLite cần thư mục này tồn tại


def _secret_key():
    """Ưu tiên biến môi trường; nếu không có thì đọc khoá trong instance/, rỗng thì sinh lại."""
    key = os.environ.get("SECRET_KEY")
    if key:
        return key
    path = os.path.join(INSTANCE_DIR, "secret.key")
    key = ""
    if os.path.exists(path):
        with open(path) as f:
            key = f.read().strip()
    if not key:
        key = secrets.token_hex(32)
        with open(path, "w") as f:
            f.write(key)
    return key


SECRET_KEY = _secret_key()
SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(INSTANCE_DIR, "bookstore.db")
SQLALCHEMY_TRACK_MODIFICATIONS = False
SESSION_COOKIE_SAMESITE = "Lax"

# Upload ảnh bìa
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2 MB
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}