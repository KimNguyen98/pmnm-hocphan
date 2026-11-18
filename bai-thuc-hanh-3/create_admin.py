import getpass

from app import create_app
from extensions import db
from models import User

app = create_app()
with app.app_context():
    ten = input("Tên đăng nhập admin: ").strip().lower()
    if not ten:
        raise SystemExit("Tên đăng nhập không được để trống.")
    ho_ten = input("Họ tên: ").strip() or ten
    mat_khau = getpass.getpass("Mật khẩu (từ 6 ký tự, gõ sẽ không hiện chữ): ")
    if len(mat_khau) < 6:
        raise SystemExit("Mật khẩu quá ngắn.")

    user = User.query.filter_by(ten_dang_nhap=ten).first()
    if user is None:
        user = User(ten_dang_nhap=ten)
        db.session.add(user)
    user.ho_ten = ho_ten
    user.vai_tro = "admin"
    user.hoat_dong = True
    user.set_password(mat_khau)
    db.session.commit()
    print(f"Đã tạo/cập nhật tài khoản admin: {ten}")