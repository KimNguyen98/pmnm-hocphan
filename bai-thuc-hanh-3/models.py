from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db

TRANG_THAI = {
    "cho_xac_nhan": "Chờ xác nhận",
    "dang_giao": "Đang giao",
    "hoan_tat": "Hoàn tất",
    "da_huy": "Đã huỷ",
}

VAI_TRO = {
    "khach": "Khách hàng",
    "admin": "Quản trị viên",
}

class User(db.Model):
    __tablename__ = "nguoi_dung"

    id = db.Column(db.Integer, primary_key=True)
    ten_dang_nhap = db.Column(db.String(50), nullable=False, unique=True, index=True)
    ho_ten = db.Column(db.String(100), nullable=False)
    mat_khau_hash = db.Column(db.String(255), nullable=False)
    vai_tro = db.Column(db.String(20), nullable=False, default="khach")
    hoat_dong = db.Column(db.Boolean, nullable=False, default=True)
    ngay_tao = db.Column(db.DateTime, default=datetime.now)

    orders = db.relationship("Order", backref="user", lazy=True)

    def set_password(self, mat_khau):
        self.mat_khau_hash = generate_password_hash(mat_khau)

    def check_password(self, mat_khau):
        return check_password_hash(self.mat_khau_hash, mat_khau)

    @property
    def la_admin(self):
        return self.vai_tro == "admin"

class DanhMuc(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ten = db.Column(db.String(100), nullable=False, unique=True)
    mo_ta = db.Column(db.String(255))
    sach = db.relationship("Sach", backref="danh_muc", lazy=True)


class Sach(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tieu_de = db.Column(db.String(200), nullable=False)
    tac_gia = db.Column(db.String(100))
    nxb = db.Column(db.String(100))
    nam = db.Column(db.Integer)
    gia = db.Column(db.Float, default=0)
    so_luong = db.Column(db.Integer, default=0)
    mo_ta = db.Column(db.Text)
    anh_bia = db.Column(db.String(200))  # tên file ảnh trong static/uploads
    danh_muc_id = db.Column(db.Integer, db.ForeignKey("danh_muc.id"), nullable=False)

    order_items = db.relationship("OrderItem", backref="sach", lazy=True)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("nguoi_dung.id"))  # đơn của khách nào
    ho_ten = db.Column(db.String(100), nullable=False)
    dien_thoai = db.Column(db.String(15), nullable=False)
    dia_chi = db.Column(db.String(300), nullable=False)
    phuong_thuc = db.Column(db.String(20), default="cod")
    ghi_chu = db.Column(db.Text)
    trang_thai = db.Column(db.String(20), default="cho_xac_nhan")
    ngay_dat = db.Column(db.DateTime, default=datetime.now)
    tong_tien = db.Column(db.Float, default=0)

    items = db.relationship("OrderItem", backref="order", lazy=True)
    history = db.relationship("OrderHistory", backref="order", lazy=True,
                              order_by="OrderHistory.thoi_diem")


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)
    sach_id = db.Column(db.Integer, db.ForeignKey("sach.id"), nullable=False)
    ten_sach = db.Column(db.String(200))            # tên tại thời điểm đặt
    don_gia = db.Column(db.Float, nullable=False)   # giá tại thời điểm đặt
    so_luong = db.Column(db.Integer, nullable=False)

    @property
    def thanh_tien(self):
        return self.don_gia * self.so_luong


class OrderHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)
    trang_thai = db.Column(db.String(20), nullable=False)
    thoi_diem = db.Column(db.DateTime, default=datetime.now)