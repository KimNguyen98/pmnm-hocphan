from flask import (Blueprint, render_template, request, session,
                   redirect, url_for, flash, g)

from extensions import db
from models import User
from forms import LoginForm, RegisterForm

auth_bp = Blueprint("auth", __name__)


def safe_next(url):
    """Chỉ cho chuyển hướng tới đường dẫn nội bộ, chặn link ra trang ngoài."""
    if url and url.startswith("/") and not url.startswith("//") and "\\" not in url:
        return url
    return None


def trang_dau(user):
    return url_for("admin.dashboard") if user.la_admin else url_for("shop.books")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if g.user:
        return redirect(trang_dau(g.user))

    form = LoginForm()
    if form.validate_on_submit():
        ten = form.ten_dang_nhap.data.strip().lower()
        user = User.query.filter_by(ten_dang_nhap=ten).first()
        if not user or not user.check_password(form.mat_khau.data):
            flash("Sai tên đăng nhập hoặc mật khẩu.", "error")
        elif not user.hoat_dong:
            flash("Tài khoản đã bị khoá. Vui lòng liên hệ quản trị viên.", "error")
        else:
            session["user_id"] = user.id
            flash(f"Xin chào, {user.ho_ten}!", "success")
            return redirect(safe_next(request.args.get("next")) or trang_dau(user))
    return render_template("auth/login.html", form=form)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if g.user:
        return redirect(trang_dau(g.user))

    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            ten_dang_nhap=form.ten_dang_nhap.data.strip().lower(),
            ho_ten=form.ho_ten.data.strip(),
            vai_tro="khach",  # đăng ký công khai luôn chỉ là khách hàng
        )
        user.set_password(form.mat_khau.data)
        db.session.add(user)
        db.session.commit()

        session["user_id"] = user.id  # đăng nhập luôn sau khi đăng ký
        flash("Tạo tài khoản thành công!", "success")
        return redirect(safe_next(request.args.get("next")) or url_for("shop.books"))
    return render_template("auth/register.html", form=form)


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.pop("user_id", None)
    flash("Đã đăng xuất.", "success")
    return redirect(url_for("shop.books"))