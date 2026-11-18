#Giỏ hàng lưu trong session dưới dạng {id_sách: {"qty": số lượng}}. Mỗi lần xem giỏ, hàm build_cart() đọc lại giá và tồn kho từ CSDL, nên giá luôn mới nhất.
#Thêm vào giỏ từ chối khi hết hàng hoặc khi số lượng vượt tồn kho (tính cả số đã có trong giỏ).
#Thanh toán kiểm tra lại tồn kho lần nữa lúc bấm đặt hàng. Khi đặt thành công, giá và tên sách được chụp lại vào OrderItem, kho bị trừ, và ghi dòng đầu tiên vào lịch sử trạng thái.

from flask import (Blueprint, render_template, request, session,
                   redirect, url_for, flash)

from extensions import db
from models import Sach, DanhMuc, Order, OrderItem, OrderHistory
from forms import CheckoutForm

shop_bp = Blueprint("shop", __name__)


def build_cart():
    """Đọc giỏ từ session -> (danh sách dòng, tổng tiền). Bỏ sách đã bị xoá."""
    cart = session.get("cart", {})
    items, tong = [], 0
    for sach_id, info in list(cart.items()):
        s = db.session.get(Sach, int(sach_id))
        if not s:
            cart.pop(sach_id)
            session["cart"] = cart
            continue
        thanh_tien = s.gia * info["qty"]
        tong += thanh_tien
        items.append({"sach": s, "qty": info["qty"], "thanh_tien": thanh_tien})
    return items, tong


# ① Danh sách sách ---------------------------------------------------------
@shop_bp.route("/")
@shop_bp.route("/books")
def books():
    q = request.args.get("q", "").strip()
    dm_id = request.args.get("danh_muc", type=int)

    query = Sach.query
    if q:
        query = query.filter(db.or_(Sach.tieu_de.ilike(f"%{q}%"),
                                    Sach.tac_gia.ilike(f"%{q}%")))
    if dm_id:
        query = query.filter_by(danh_muc_id=dm_id)

    ds_sach = query.order_by(Sach.id.desc()).all()
    ds_dm = DanhMuc.query.order_by(DanhMuc.ten).all()
    return render_template("shop/books.html", ds_sach=ds_sach, ds_dm=ds_dm,
                           q=q, dm_id=dm_id)


# ② Chi tiết sách ----------------------------------------------------------
@shop_bp.route("/books/<int:id>")
def book_detail(id):
    s = db.get_or_404(Sach, id)
    da_co = session.get("cart", {}).get(str(id), {}).get("qty", 0)
    return render_template("shop/book_detail.html", s=s, da_co=da_co)


# ③ Giỏ hàng ---------------------------------------------------------------
@shop_bp.route("/cart/add/<int:sach_id>", methods=["POST"])
def cart_add(sach_id):
    s = db.get_or_404(Sach, sach_id)
    qty = request.form.get("qty", 1, type=int)

    cart = session.get("cart", {})
    key = str(sach_id)
    da_co = cart.get(key, {}).get("qty", 0)

    if s.so_luong <= 0:
        flash("Sách này đã hết hàng.", "error")
    elif qty < 1 or da_co + qty > s.so_luong:
        flash(f"Số lượng không hợp lệ. Kho còn {s.so_luong}, bạn đã có {da_co} trong giỏ.", "error")
    else:
        cart.setdefault(key, {"qty": 0})["qty"] += qty
        session["cart"] = cart
        flash(f"Đã thêm {qty} × {s.tieu_de} vào giỏ hàng.", "success")
    return redirect(request.referrer or url_for("shop.books"))


@shop_bp.route("/cart")
def cart():
    items, tong = build_cart()
    return render_template("shop/cart.html", items=items, tong=tong)


@shop_bp.route("/cart/update/<int:sach_id>", methods=["POST"])
def cart_update(sach_id):
    action = request.form.get("action")  # "plus" | "minus"
    cart = session.get("cart", {})
    key = str(sach_id)
    if key in cart:
        s = db.session.get(Sach, sach_id)
        if action == "plus":
            if s and cart[key]["qty"] < s.so_luong:
                cart[key]["qty"] += 1
            else:
                flash("Đã đạt số lượng tối đa trong kho.", "error")
        elif action == "minus":
            cart[key]["qty"] -= 1
            if cart[key]["qty"] <= 0:
                del cart[key]
        session["cart"] = cart
    return redirect(url_for("shop.cart"))


@shop_bp.route("/cart/remove/<int:sach_id>", methods=["POST"])
def cart_remove(sach_id):
    cart = session.get("cart", {})
    cart.pop(str(sach_id), None)
    session["cart"] = cart
    flash("Đã xoá khỏi giỏ hàng.", "success")
    return redirect(url_for("shop.cart"))


@shop_bp.route("/cart/clear", methods=["POST"])
def cart_clear():
    session.pop("cart", None)
    flash("Đã xoá toàn bộ giỏ hàng.", "success")
    return redirect(url_for("shop.cart"))


# ④ Thanh toán -------------------------------------------------------------
@shop_bp.route("/checkout", methods=["GET", "POST"])
def checkout():
    items, tong = build_cart()
    if not items:
        flash("Giỏ hàng đang trống.", "error")
        return redirect(url_for("shop.cart"))

    form = CheckoutForm()
    if form.validate_on_submit():
        # Kiểm tra lại tồn kho ngay lúc đặt
        for it in items:
            if it["qty"] > it["sach"].so_luong:
                flash(f"“{it['sach'].tieu_de}” chỉ còn {it['sach'].so_luong} cuốn. "
                      "Vui lòng cập nhật giỏ hàng.", "error")
                return redirect(url_for("shop.cart"))

        order = Order(
            ho_ten=form.ho_ten.data.strip(),
            dien_thoai=form.dien_thoai.data.strip(),
            dia_chi=form.dia_chi.data.strip(),
            phuong_thuc=form.phuong_thuc.data,
            ghi_chu=form.ghi_chu.data,
            tong_tien=tong,
        )
        db.session.add(order)
        db.session.flush()  # lấy order.id

        for it in items:
            s = it["sach"]
            db.session.add(OrderItem(
                order_id=order.id, sach_id=s.id, ten_sach=s.tieu_de,
                don_gia=s.gia, so_luong=it["qty"],  # giá tại thời điểm đặt
            ))
            s.so_luong -= it["qty"]

        db.session.add(OrderHistory(order_id=order.id, trang_thai="cho_xac_nhan"))
        db.session.commit()

        session.pop("cart", None)
        flash("Đặt hàng thành công!", "success")
        return redirect(url_for("shop.order_success", id=order.id))

    return render_template("shop/checkout.html", form=form, items=items, tong=tong)


# ⑤ Đặt hàng thành công ----------------------------------------------------
@shop_bp.route("/orders/<int:id>")
def order_success(id):
    order = db.get_or_404(Order, id)
    return render_template("shop/order_success.html", order=order)