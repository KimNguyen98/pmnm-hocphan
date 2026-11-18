from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (StringField, FloatField, IntegerField, TextAreaField,
                     SelectField, RadioField, SubmitField)
from wtforms.validators import (DataRequired, InputRequired, NumberRange,
                                Length, Regexp, Optional)


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