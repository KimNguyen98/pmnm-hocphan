from functools import wraps

from flask import session, redirect, url_for, flash, request, abort, g

from extensions import db
from models import User


def load_user():
    """Đọc người dùng từ session. Tài khoản bị khoá hoặc đã xoá thì coi như chưa đăng nhập."""
    uid = session.get("user_id")
    if not uid:
        return None
    user = db.session.get(User, uid)
    if user is None or not user.hoat_dong:
        session.pop("user_id", None)
        return None
    return user


def _chuyen_den_dang_nhap():
    flash("Vui lòng đăng nhập để tiếp tục.", "error")
    return redirect(url_for("auth.login", next=request.path))


def login_required(f):
    """Phải đăng nhập (khách hay admin đều được)."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not g.user:
            return _chuyen_den_dang_nhap()
        return f(*args, **kwargs)
    return wrapper


def admin_required(f):
    """Chỉ admin. Chưa đăng nhập thì chuyển tới trang đăng nhập, là khách thì báo 403."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not g.user:
            return _chuyen_den_dang_nhap()
        if not g.user.la_admin:
            abort(403)
        return f(*args, **kwargs)
    return wrapper