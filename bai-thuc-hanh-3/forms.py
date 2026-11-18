from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (StringField, FloatField, IntegerField, TextAreaField,
                     SelectField, RadioField, SubmitField, PasswordField)
from wtforms.validators import (DataRequired, InputRequired, NumberRange,
                                Length, Regexp, Optional, EqualTo, ValidationError)


class SachForm(FlaskForm):
    """Form thêm/sửa sách"""
    tieu_de = StringField("Tiêu đề", validators=[DataRequired(), Length(max=200)])
    tac_gia = StringField("Tác giả", validators=[Optional(), Length(max=100)])
    nxb = StringField("Nhà xuất bản", validators=[Optional(), Length(max=100)])
    nam = IntegerField("Năm xuất bản", validators=[Optional(), NumberRange(min=1900, max=2100)])
    gia = FloatField("Giá (₫)", validators=[InputRequired(), NumberRange(min=0)], default=0)
    so_luong = IntegerField("Số lượng", validators=[InputRequired(), NumberRange(min=0)], default=0)
    mo_ta = TextAreaField("Mô tả", validators=[Optional()])
    danh_muc_id = SelectField("Danh mục", coerce=int, validators=[InputRequired()])
    anh_bia = FileField("Ảnh bìa", validators=[
        FileAllowed(["jpg", "jpeg", "png", "webp"], "Chỉ chấp nhận JPG, PNG, WEBP")
    ])
    submit = SubmitField("Lưu sách")


class DanhMucForm(FlaskForm):
    """Form thêm danh mục"""
    ten = StringField("Tên danh mục", validators=[DataRequired(), Length(max=100)])
    mo_ta = StringField("Mô tả", validators=[Optional(), Length(max=255)])
    submit = SubmitField("Thêm danh mục")


class CheckoutForm(FlaskForm):
    """Form đặt hàng"""
    ho_ten = StringField("Họ tên", validators=[DataRequired(), Length(min=2, max=100)])
    dien_thoai = StringField("Điện thoại", validators=[
        DataRequired(),
        Regexp(r"^0\d{9}$", message="Số điện thoại gồm 10 chữ số, bắt đầu bằng 0")
    ])
    dia_chi = TextAreaField("Địa chỉ nhận hàng", validators=[DataRequired(), Length(max=300)])
    phuong_thuc = RadioField("Thanh toán", choices=[
        ("cod", "Tiền mặt khi nhận hàng"),
        ("bank", "Chuyển khoản"),
    ], default="cod")
    ghi_chu = TextAreaField("Ghi chú", validators=[Optional()])
    submit = SubmitField("Đặt hàng")

class LoginForm(FlaskForm):
    ten_dang_nhap = StringField("Tên đăng nhập", validators=[DataRequired(), Length(max=50)])
    mat_khau = PasswordField("Mật khẩu", validators=[DataRequired()])
    submit = SubmitField("Đăng nhập")


class RegisterForm(FlaskForm):
    ho_ten = StringField("Họ tên", validators=[DataRequired(), Length(min=2, max=100)])
    ten_dang_nhap = StringField("Tên đăng nhập", validators=[
        DataRequired(), Length(min=3, max=50),
        Regexp(r"^[A-Za-z0-9_.]+$",
               message="Chỉ gồm chữ không dấu, số, dấu chấm và dấu gạch dưới")
    ])
    mat_khau = PasswordField("Mật khẩu", validators=[DataRequired(), Length(min=6, max=128)])
    nhap_lai = PasswordField("Nhập lại mật khẩu", validators=[
        DataRequired(), EqualTo("mat_khau", message="Mật khẩu nhập lại không khớp")
    ])
    submit = SubmitField("Đăng ký")

    def validate_ten_dang_nhap(self, field):
        from models import User
        if User.query.filter_by(ten_dang_nhap=field.data.strip().lower()).first():
            raise ValidationError("Tên đăng nhập đã được dùng.")