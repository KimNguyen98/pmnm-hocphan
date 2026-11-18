import os
import uuid
from datetime import datetime

from flask import (Blueprint, render_template, request, redirect,
                   url_for, flash, current_app, g, abort)
from sqlalchemy import func, cast, String

from extensions import db
from models import Sach, DanhMuc, Order, OrderHistory, User, TRANG_THAI
from forms import SachForm, DanhMucForm

admin_bp = Blueprint("admin", __name__)

PER_PAGE = 10

# Trạng thái nào được chuyển sang trạng thái nào
CHUYEN_TRANG_THAI = {
    "cho_xac_nhan": ["dang_giao", "da_huy"],
    "dang_giao": ["hoan_tat", "da_huy"],
    "hoan_tat": [],
    "da_huy": [],
}


@admin_bp.before_request
def chi_cho_admin():
    """Chạy trước MỌI route trong /admin: chưa đăng nhập thì chuyển đi đăng nhập, không phải admin thì 403."""
    if not g.user:
        flash("Vui lòng đăng nhập để tiếp tục.", "error")
        return redirect(url_for("auth.login", next=request.path))
    if not g.user.la_admin:
        abort(403)


# ---- Ảnh bìa ---------------------------------------------------------------
def save_image(file):
    ext = file.filename.rsplit(".", 1)[-1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(folder, exist_ok=True)
    file.save(os.path.join(folder, filename))
    return filename


def delete_image(filename):
    if filename:
        path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
        if os.path.exists(path):
            os.remove(path)


def dm_choices():
    return [(dm.id, dm.ten) for dm in DanhMuc.query.order_by(DanhMuc.ten).all()]


# ⑥ Dashboard --------------------------------------------------------------
@admin_bp.route("/")
def dashboard():
    don_cho = Order.query.filter_by(trang_thai="cho_xac_nhan").count()
    dau_thang = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    doanh_thu = db.session.query(func.coalesce(func.sum(Order.tong_tien), 0)).filter(
        Order.trang_thai == "hoan_tat", Order.ngay_dat >= dau_thang
    ).scalar()

    tong_sach = Sach.query.count()
    sach_sap_het = Sach.query.filter(Sach.so_luong <= 5, Sach.so_luong > 0) \
                             .order_by(Sach.so_luong).all()
    don_moi = Order.query.order_by(Order.id.desc()).limit(5).all()
    return render_template("admin/dashboard.html", don_cho=don_cho,
                           doanh_thu=doanh_thu, tong_sach=tong_sach,
                           sach_sap_het=sach_sap_het, don_moi=don_moi)


# ⑦ Quản lý sách -----------------------------------------------------------
@admin_bp.route("/books")
def books():
    dm_id = request.args.get("danh_muc", type=int)
    q = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)

    query = Sach.query
    if dm_id:
        query = query.filter_by(danh_muc_id=dm_id)
    if q:
        query = query.filter(db.or_(Sach.tieu_de.ilike(f"%{q}%"),
                                    Sach.tac_gia.ilike(f"%{q}%")))

    pagination = query.order_by(Sach.id.desc()).paginate(
        page=page, per_page=PER_PAGE, error_out=False)
    ds_dm = DanhMuc.query.order_by(DanhMuc.ten).all()
    return render_template("admin/books.html", pagination=pagination,
                           ds_dm=ds_dm, dm_id=dm_id, q=q)


# ⑧ Thêm / sửa / xoá sách --------------------------------------------------
@admin_bp.route("/books/new", methods=["GET", "POST"])
def book_new():
    form = SachForm()
    form.danh_muc_id.choices = dm_choices()
    if form.validate_on_submit():
        s = Sach(
            tieu_de=form.tieu_de.data.strip(), tac_gia=form.tac_gia.data,
            nxb=form.nxb.data, nam=form.nam.data, gia=form.gia.data,
            so_luong=form.so_luong.data, mo_ta=form.mo_ta.data,
            danh_muc_id=form.danh_muc_id.data,
        )
        if form.anh_bia.data:
            s.anh_bia = save_image(form.anh_bia.data)
        db.session.add(s)
        db.session.commit()
        flash("Đã thêm sách.", "success")
        return redirect(url_for("admin.books"))
    return render_template("admin/book_form.html", form=form, s=None)


@admin_bp.route("/books/<int:id>/edit", methods=["GET", "POST"])
def book_edit(id):
    s = db.get_or_404(Sach, id)
    form = SachForm(obj=s)
    form.danh_muc_id.choices = dm_choices()
    if form.validate_on_submit():
        # Gán từng trường (không dùng populate_obj để khỏi ghi đè anh_bia)
        s.tieu_de = form.tieu_de.data.strip()
        s.tac_gia, s.nxb, s.nam = form.tac_gia.data, form.nxb.data, form.nam.data
        s.gia, s.so_luong = form.gia.data, form.so_luong.data
        s.mo_ta, s.danh_muc_id = form.mo_ta.data, form.danh_muc_id.data
        if form.anh_bia.data:
            delete_image(s.anh_bia)
            s.anh_bia = save_image(form.anh_bia.data)
        db.session.commit()
        flash("Đã cập nhật sách.", "success")
        return redirect(url_for("admin.books"))
    return render_template("admin/book_form.html", form=form, s=s)


@admin_bp.route("/books/<int:id>/delete", methods=["POST"])
def book_delete(id):
    s = db.get_or_404(Sach, id)
    if s.order_items:
        flash("Không thể xoá: sách đã có trong đơn hàng.", "error")
    else:
        delete_image(s.anh_bia)
        db.session.delete(s)
        db.session.commit()
        flash("Đã xoá sách.", "success")
    return redirect(url_for("admin.books"))


# ⑨ Danh mục ---------------------------------------------------------------
@admin_bp.route("/categories", methods=["GET", "POST"])
def categories():
    form = DanhMucForm()
    if form.validate_on_submit():
        ten = form.ten.data.strip()
        trung = DanhMuc.query.filter(func.lower(DanhMuc.ten) == ten.lower()).first()
        if trung:
            flash("Danh mục này đã tồn tại.", "error")
        else:
            db.session.add(DanhMuc(ten=ten, mo_ta=form.mo_ta.data))
            db.session.commit()
            flash("Đã thêm danh mục.", "success")
            return redirect(url_for("admin.categories"))

    ds = db.session.query(
        DanhMuc.id, DanhMuc.ten, DanhMuc.mo_ta, func.count(Sach.id).label("so_sach")
    ).outerjoin(Sach).group_by(DanhMuc.id, DanhMuc.ten, DanhMuc.mo_ta) \
     .order_by(DanhMuc.ten).all()
    return render_template("admin/categories.html", ds=ds, form=form)


@admin_bp.route("/categories/<int:id>/delete", methods=["POST"])
def category_delete(id):
    dm = db.get_or_404(DanhMuc, id)
    if dm.sach:
        flash(f"Không thể xoá: danh mục còn {len(dm.sach)} cuốn sách.", "error")
    else:
        db.session.delete(dm)
        db.session.commit()
        flash("Đã xoá danh mục.", "success")
    return redirect(url_for("admin.categories"))


# ⑩ Danh sách đơn hàng -----------------------------------------------------
@admin_bp.route("/orders")
def orders():
    status = request.args.get("status", "")
    q = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)
    if status not in TRANG_THAI:
        status = ""

    query = Order.query
    if status:
        query = query.filter(Order.trang_thai == status)
    if q:
        query = query.filter(db.or_(
            cast(Order.id, String).ilike(f"%{q}%"),
            Order.ho_ten.ilike(f"%{q}%"),
            Order.dien_thoai.ilike(f"%{q}%"),
        ))

    pagination = query.order_by(Order.ngay_dat.desc()).paginate(
        page=page, per_page=PER_PAGE, error_out=False)

    dem = dict(db.session.query(Order.trang_thai, func.count(Order.id))
               .group_by(Order.trang_thai).all())
    tong_don = sum(dem.values())

    tong_q = db.session.query(func.coalesce(func.sum(Order.tong_tien), 0))
    if status:
        tong_q = tong_q.filter(Order.trang_thai == status)
    tong_gia_tri = tong_q.scalar()

    return render_template("admin/orders.html", pagination=pagination, dem=dem,
                           tong_don=tong_don, tong_gia_tri=tong_gia_tri,
                           status=status, q=q)


# ⑪ Chi tiết đơn + đổi trạng thái -----------------------------------------
@admin_bp.route("/orders/<int:id>")
def order_detail(id):
    order = db.get_or_404(Order, id)
    chuyen_duoc = CHUYEN_TRANG_THAI.get(order.trang_thai, [])
    return render_template("admin/order_detail.html", order=order,
                           chuyen_duoc=chuyen_duoc)


@admin_bp.route("/orders/<int:id>/status", methods=["POST"])
def order_status(id):
    order = db.get_or_404(Order, id)
    new = request.form.get("trang_thai")
    if new not in CHUYEN_TRANG_THAI.get(order.trang_thai, []):
        flash("Không thể chuyển sang trạng thái này.", "error")
        return redirect(url_for("admin.order_detail", id=id))

    if new == "da_huy":  # huỷ đơn -> hoàn lại tồn kho
        for item in order.items:
            s = db.session.get(Sach, item.sach_id)
            if s:
                s.so_luong += item.so_luong

    order.trang_thai = new
    db.session.add(OrderHistory(order_id=order.id, trang_thai=new))
    db.session.commit()
    flash(f"Đã chuyển đơn #{order.id} sang: {TRANG_THAI[new]}.", "success")
    return redirect(url_for("admin.order_detail", id=id))


# ⑫ Quản lý người dùng -----------------------------------------------------
@admin_bp.route("/users")
def users():
    ds = User.query.order_by(User.ngay_tao.desc()).all()
    return render_template("admin/users.html", ds=ds)


@admin_bp.route("/users/<int:id>/role", methods=["POST"])
def user_role(id):
    u = db.get_or_404(User, id)
    if u.id == g.user.id:
        flash("Bạn không thể đổi vai trò của chính mình.", "error")
    else:
        u.vai_tro = "khach" if u.la_admin else "admin"
        db.session.commit()
        flash(f"Đã đổi vai trò của {u.ten_dang_nhap} thành: "
              f"{'Quản trị viên' if u.la_admin else 'Khách hàng'}.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:id>/active", methods=["POST"])
def user_active(id):
    u = db.get_or_404(User, id)
    if u.id == g.user.id:
        flash("Bạn không thể khoá chính mình.", "error")
    else:
        u.hoat_dong = not u.hoat_dong
        db.session.commit()
        flash(f"Đã {'mở khoá' if u.hoat_dong else 'khoá'} tài khoản {u.ten_dang_nhap}.", "success")
    return redirect(url_for("admin.users"))