from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///books.db"
app.config["SECRET_KEY"] = "doi-khoa-bi-mat-nay"
db = SQLAlchemy(app)


class DanhMuc(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ten = db.Column(db.String(100), nullable=False)
    mo_ta = db.Column(db.String(255))
    sach = db.relationship("Sach", backref="danh_muc", lazy=True)


class Sach(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tieu_de = db.Column(db.String(200), nullable=False)
    tac_gia = db.Column(db.String(100))
    gia = db.Column(db.Float, default=0)
    so_luong = db.Column(db.Integer, default=0)
    danh_muc_id = db.Column(db.Integer, db.ForeignKey("danh_muc.id"), nullable=False)


with app.app_context():
    db.create_all()


@app.route("/")
def dashboard():
    return render_template(
        "dashboard.html",
        so_danh_muc=DanhMuc.query.count(),
        so_sach=Sach.query.count(),
    )

@app.route("/danh-muc")
def danh_muc_list():
    ds = DanhMuc.query.order_by(DanhMuc.id).all()
    return render_template("danhmuc/danh_sach.html", ds=ds)

@app.route("/danh-muc/them", methods=["GET", "POST"])
def danh_muc_them():
    if request.method == "POST":
        ten = request.form["ten"].strip()
        if not ten:
            flash("Tên danh mục không được để trống", "loi")
            return render_template("danhmuc/form.html", dm=None)
        db.session.add(DanhMuc(ten=ten, mo_ta=request.form["mo_ta"].strip()))
        db.session.commit()
        flash("Đã thêm danh mục", "ok")
        return redirect(url_for("danh_muc_list"))
    return render_template("danhmuc/form.html", dm=None)

@app.route("/danh-muc/<int:id>/sua", methods=["GET", "POST"])
def danh_muc_sua(id):
    dm = db.get_or_404(DanhMuc, id)
    if request.method == "POST":
        ten = request.form["ten"].strip()
        if not ten:
            flash("Tên danh mục không được để trống", "loi")
            return render_template("danhmuc/form.html", dm=dm)
        dm.ten = ten
        dm.mo_ta = request.form["mo_ta"].strip()
        db.session.commit()
        flash("Đã cập nhật danh mục", "ok")
        return redirect(url_for("danh_muc_list"))
    return render_template("danhmuc/form.html", dm=dm)

@app.route("/danh-muc/<int:id>/xoa", methods=["POST"])
def danh_muc_xoa(id):
    dm = db.get_or_404(DanhMuc, id)
    if dm.sach:
        flash("Không thể xóa: danh mục này còn sách", "loi")
    else:
        db.session.delete(dm)
        db.session.commit()
        flash("Đã xóa danh mục", "ok")
    return redirect(url_for("danh_muc_list"))



def doc_form_sach():
    return {
        "tieu_de": request.form["tieu_de"].strip(),
        "tac_gia": request.form["tac_gia"].strip(),
        "gia": float(request.form["gia"] or 0),
        "so_luong": int(request.form["so_luong"] or 0),
        "danh_muc_id": int(request.form["danh_muc_id"]),
    }

@app.route("/sach")
def sach_list():
    dm_id = request.args.get("danh_muc", type=int)
    q = Sach.query
    if dm_id:
        q = q.filter_by(danh_muc_id=dm_id)
    ds = q.order_by(Sach.id).all()
    ds_dm = DanhMuc.query.order_by(DanhMuc.ten).all()
    return render_template("sach/danh_sach.html", ds=ds, ds_dm=ds_dm, dm_id=dm_id)


if __name__ == "__main__":
    app.run(debug=True)