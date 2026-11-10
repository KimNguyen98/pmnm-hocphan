from flask import Flask, render_template
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


if __name__ == "__main__":
    app.run(debug=True)