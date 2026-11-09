import csv
import io
import re
from datetime import datetime, timedelta
from functools import wraps
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import func

from flask import (Flask, render_template, request, jsonify, redirect,
                   url_for, make_response, session, flash)
from werkzeug.routing import BaseConverter
from werkzeug.security import generate_password_hash, check_password_hash

TEXT = {"Content-Type": "text/plain; charset=utf-8"}

#Ket noi CSDL
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

app = Flask(__name__)
app.config["SECRET_KEY"] = "dev-chi-dung-khi-phat-trien"
app.config["SQLALCHEMY_DATABASE_URI"] = \
    "sqlite:///qlsv.db"
db.init_app(app)

class Student(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    mssv: Mapped[str] = mapped_column(String(10), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    gpa: Mapped[float] = mapped_column(default=0.0)

    def __repr__(self):
        return f"<Student {self.mssv} {self.name}>"

with app.app_context():
       db.create_all()

@app.get("/them-mau")
def add_sample():
    total = db.session.scalar(
        db.select(func.count(Student.id))
    )
    if total > 0:
        return f"Da co {total} sinh vien trong CSDL, khong them nua."
    an = Student(mssv="23T1020001", name="Nguyễn Văn An", gpa=8.5)
    before = an.id                  # chưa ghi xuống CSDL
    db.session.add(an)              # đưa vào "giỏ" chờ ghi
    db.session.add_all([
        Student(mssv="23T1020002", name="Trần Thị Bình", gpa=6.8),
        Student(mssv="23T1020003", name="Lê Hoàng Cường", gpa=9.1),
        Student(mssv="23T1020004", name="Phạm Minh Dũng", gpa=4.5),
        Student(mssv="23T1020005", name="Hoàng Thu Hà", gpa=7.4),
    ])
    db.session.commit()             # ghi thật sự
    return (f"Đã thêm 5 sinh viên. id của An: "
            f"trước commit = {before}, "
            f"sau commit = {an.id}")

#Truy vấn
@app.get("/thu-truy-van")
def try_queries():
    if db.session.scalar(
            db.select(func.count(Student.id))) == 0:
        return "Chưa có dữ liệu, hãy mở /them-mau trước."
    lines = []
    lines.append(f"1. get(3): {db.session.get(Student, 3)}")
    lines.append(f"2. get(99): {db.session.get(Student, 99)}")
    everyone = db.session.execute(
        db.select(Student)).scalars().all()
    lines.append(f"3. Tất cả: {len(everyone)} sinh viên")
    stmt = (db.select(Student)
            .where(Student.gpa >= 8)
            .order_by(Student.gpa.desc()))
    good = db.session.execute(stmt).scalars().all()
    lines.append(f"4. Điểm >= 8: {good}")
    binh = db.session.scalar(db.select(Student)
                             .filter_by(mssv="23T1020002"))
    lines.append(f"5. MSSV 23T1020002: {binh}")
    count = db.session.scalar(
        db.select(func.count(Student.id)))
    avg = db.session.scalar(db.select(func.avg(Student.gpa)))
    lines.append(f"6. Số SV: {count}, điểm TB: {avg:.2f}")
    return "\n".join(lines), TEXT


@app.route("/list_sinhvien")
def list_sinhvien():
    ds = db.session.scalars(db.select(Student).order_by(Student.mssv)).all()
    return render_template("list_sinhvien.html", ds=ds)


# [Nguồn: sodiem.py] JSON hiển thị tiếng Việt có dấu
app.json.ensure_ascii = False

# [Nguồn: login.py] khóa bí mật cho session + thời gian "Ghi nhớ đăng nhập"
app.secret_key = "doi-chuoi-bi-mat-nay"
app.permanent_session_lifetime = timedelta(days=7)


# ======================================================================
# [Nguồn: app.py] BỘ CHUYỂN ĐỔI URL "list"
# ======================================================================
class ListConverter(BaseConverter):
    # Danh sách số nguyên (có thể âm) cách nhau bởi dấu phẩy
    regex = r"-?\d+(?:,-?\d+)*"

    def to_python(self, value):
        return [int(x) for x in value.split(",")]

    def to_url(self, value):
        return ",".join(str(int(x)) for x in value)


# Đăng ký converter TRƯỚC khi khai báo route
app.url_map.converters["list"] = ListConverter


# ======================================================================
# [BỔ SUNG khi gộp] Biến "now" cho template
# base.html dùng {{ now.year }} ở chân trang,
# nhưng trong các file .py cũ không có file nào truyền "now" vào.
# ======================================================================
@app.context_processor
def inject_now():
    # [MỚI] RANK_CLASS: đổi xếp loại -> tên class màu của huy hiệu (badge) trong CSS
    return {
        "now": datetime.now(),
        "RANK_CLASS": {"Giỏi": "good", "Khá": "fair", "Trung bình": "avg",
                       "Yếu": "weak", "Kém": "weak"},
    }


# ======================================================================
# [Nguồn: login.py] DỮ LIỆU + DECORATOR ĐĂNG NHẬP
# ======================================================================
# [MỚI] Mật khẩu được băm (không lưu chữ thường). Tài khoản đăng ký mới được
# lưu trong bộ nhớ nên sẽ mất khi tắt server.
USERS = {
    "admin": generate_password_hash("admin123"),
    "an": generate_password_hash("an123456"),
}


def safe_next(target):
    """[MỚI] Chỉ cho phép quay lại đường dẫn nội bộ của web (chống chuyển hướng ra ngoài)."""
    if target and target.startswith("/") and not target.startswith("//"):
        return target
    return None


def login_required(f):
    """Chưa đăng nhập -> chuyển sang trang Đăng nhập, đăng nhập xong quay lại trang đang mở."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            flash("Vui lòng đăng nhập hoặc đăng ký để sử dụng chức năng này.", "info")
            return redirect(url_for("login", next=request.full_path.rstrip("?")))
        return f(*args, **kwargs)
    return wrapper


# ======================================================================
# [Nguồn: baitap.py + maytinh.py] DỮ LIỆU + HÀM MÁY TÍNH
# (maytinh.py và phần máy tính của baitap.py giống nhau -> giữ một bản)
# ======================================================================
OPS = [("+", "Cộng"), ("-", "Trừ"), ("*", "Nhân"), ("/", "Chia")]


def calculate(a, b, op):
    if op == "+":
        return a + b
    if op == "-":
        return a - b
    if op == "*":
        return a * b
    if op == "/":
        if b == 0:
            raise ZeroDivisionError("Không thể chia cho 0")
        return a / b
    raise ValueError("Phép tính không hợp lệ")


# ======================================================================
# [Nguồn: baitap.py + hocphan.py] DỮ LIỆU + HÀM TÍNH ĐIỂM HỌC PHẦN
# Lưu ý: hocphan.py khác baitap.py ở 2 chỗ (thang 4 cho điểm A là 3.7 và
# có thêm xếp loại "Xuất sắc"). Bản dưới đây lấy theo baitap.py (bản mới hơn).
# ======================================================================
# (điểm tối thiểu, điểm chữ, điểm hệ 4)
THANG_DIEM = [
    (8.5, "A", 4.0),
    (7.0, "B", 3.0),
    (5.5, "C", 2.0),
    (4.0, "D", 1.0),
    (0.0, "F", 0.0),
]

DEFAULT = {"cc": "", "gk": "", "ck": "", "w_cc": "10", "w_gk": "30", "w_ck": "60"}


def doc_so(form, ten, thap_nhat=0, cao_nhat=10):
    try:
        v = float(form.get(ten, ""))
    except ValueError:
        raise ValueError("Vui lòng nhập đầy đủ và đúng định dạng số")
    if not thap_nhat <= v <= cao_nhat:
        raise ValueError(f"Giá trị phải nằm trong khoảng {thap_nhat} - {cao_nhat}")
    return v


def quy_doi(diem10):
    for min_diem, chu, he4 in THANG_DIEM:
        if diem10 >= min_diem:
            return chu, he4


# Đổi tên từ xep_loai -> xep_loai_hocphan vì sodiem.py cũng có hàm xep_loai
# (khác nội dung), nếu giữ nguyên tên thì hàm này sẽ đè lên hàm kia.
def xep_loai_hocphan(he4):
    if he4 >= 4.0:
        return "Giỏi"
    if he4 >= 3.0:
        return "Khá"
    if he4 >= 2.0:
        return "Trung bình"
    if he4 >= 1.0:
        return "Yếu"
    return "Kém"


# ======================================================================
# [Nguồn: sodiem.py] DỮ LIỆU + HÀM QUẢN LÝ SỐ ĐIỂM SINH VIÊN
# ======================================================================
STUDENTS = {
    "23T1020001": {"name": "Nguyễn Văn An", "lop": "K47A",
                   "scores": {"PMMNM": 8.5, "CSDL": 7.0, "MMT": 9.0}},
    "23T1020002": {"name": "Trần Thị Bình", "lop": "K47A",
                   "scores": {"PMMNM": 6.0, "CSDL": 5.5, "MMT": 7.0}},
    "23T1020003": {"name": "Lê Hoàng Cường", "lop": "K47B",
                   "scores": {"PMMNM": 9.5, "CSDL": 9.0}},
    "23T1020004": {"name": "Phạm Minh Dũng", "lop": "K47B",
                   "scores": {"PMMNM": 4.0, "CSDL": 3.5, "MMT": 5.0}},
    "23T1020005": {"name": "Hoàng Thu Hà", "lop": "K47A",
                   "scores": {}},
    "23T1020006": {"name": "Võ Quốc Khánh", "lop": "K47C",
                   "scores": {"PMMNM": 7.5, "MMT": 8.0}},
}


def diem_tb(scores):
    """Điểm trung bình, None nếu chưa có điểm."""
    if not scores:
        return None
    return round(sum(scores.values()) / len(scores), 2)


# Đổi tên từ xep_loai -> xep_loai_sv (xem ghi chú ở xep_loai_hocphan)
def xep_loai_sv(avg):
    if avg is None:
        return "--"
    if avg >= 8.0:
        return "Giỏi"
    if avg >= 6.5:
        return "Khá"
    if avg >= 5.0:
        return "Trung bình"
    return "Yếu"


def build_rows(lop_chon="", q=""):
    """Danh sách sinh viên, lọc theo lớp và từ khóa (tên hoặc MSSV), không phân biệt hoa thường."""
    rows = []
    for mssv, s in STUDENTS.items():
        if lop_chon and s["lop"].lower() != lop_chon.lower():
            continue
        if q and q.lower() not in s["name"].lower() and q.lower() not in mssv.lower():
            continue
        avg = diem_tb(s["scores"])
        rows.append({"mssv": mssv, "name": s["name"], "lop": s["lop"],
                     "avg": avg, "rank": xep_loai_sv(avg)})
    return rows


# ======================================================================
# ROUTE: TRANG CHỦ   (template: home.html) - KHÔNG cần đăng nhập
# [Nguồn: login.py (home) + sodiem.py (index) + baitap.py (home -> Homes.html)]
# Ba route "/" cũ được gộp thành một; số liệu thống kê lấy từ sodiem.py.
# ======================================================================
@app.route("/")
def home():
    tong_sv = len(STUDENTS)
    so_lop = len({s["lop"] for s in STUDENTS.values()})
    return render_template("home.html", tong_sv=tong_sv, so_lop=so_lop)


# ======================================================================
# ROUTE: /sum/<list:numbers>
# [Nguồn: app.py]
# ======================================================================
@app.route("/sum/<list:numbers>")
@login_required
def sum_numbers(numbers):
    return jsonify({"numbers": numbers, "sum": sum(numbers)})


# ======================================================================
# ROUTE: MÁY TÍNH   (template: index.html, css: maytinh.css)
# [Nguồn: baitap.py (route /maytinh) - giống maytinh.py (route "/")]
# ======================================================================
@app.route("/maytinh", methods=["GET", "POST"])
@login_required
def maytinh():
    a = b = ""
    op = "+"
    result = None
    error = None

    if request.method == "POST":
        a = request.form.get("a", "")
        b = request.form.get("b", "")
        op = request.form.get("op", "+")
        try:
            value = calculate(float(a), float(b), op)
            result = int(value) if value == int(value) else round(value, 6)
        except ValueError:
            error = "Vui lòng nhập số hợp lệ"
        except ZeroDivisionError as e:
            error = str(e)

    return render_template("index.html",
                           a=a, b=b, op=op, ops=OPS, result=result, error=error)


# ======================================================================
# ROUTE: TÍNH ĐIỂM HỌC PHẦN   (template: hocphan.html, css: hocphan.css)
# [Nguồn: baitap.py (route /hocphan) - giống hocphan.py (route "/")]
# ======================================================================
@app.route("/hocphan", methods=["GET", "POST"])
@login_required
def hocphan():
    form = dict(DEFAULT)
    ket_qua = None
    loi = None

    if request.method == "POST":
        form.update({k: request.form.get(k, "") for k in DEFAULT})
        try:
            diem = {k: doc_so(request.form, k) for k in ("cc", "gk", "ck")}
            trong_so = {k: doc_so(request.form, "w_" + k, 0, 100) for k in ("cc", "gk", "ck")}

            if round(sum(trong_so.values()), 6) != 100:
                raise ValueError("Tổng trọng số phải bằng 100%")

            diem10 = sum(diem[k] * trong_so[k] for k in diem) / 100
            diem10 = round(diem10, 1)
            chu, he4 = quy_doi(diem10)
            ket_qua = {
                "diem10": diem10,
                "chu": chu,
                "he4": he4,
                "xep_loai": xep_loai_hocphan(he4),
                "dat": diem10 >= 4.0,
            }
        except ValueError as e:
            loi = str(e)

    return render_template("hocphan.html",
                           form=form, ket_qua=ket_qua, loi=loi)


# ======================================================================
# ROUTE: ĐĂNG NHẬP / ĐĂNG KÝ / HỒ SƠ / ĐĂNG XUẤT   (template: login.html, register.html, profile.html)
# [Nguồn: login.py]
# ======================================================================
@app.route("/login", methods=["GET", "POST"])
def login():
    next_url = safe_next(request.values.get("next"))
    if "user" in session:
        return redirect(next_url or url_for("home"))

    username = ""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if username in USERS and check_password_hash(USERS[username], password):
            session.clear()
            session["user"] = username
            session.permanent = bool(request.form.get("remember"))
            flash(f"Đăng nhập thành công. Xin chào {username}!", "success")
            return redirect(next_url or url_for("home"))
        flash("Sai tên đăng nhập hoặc mật khẩu.", "error")

    return render_template("login.html", username=username, next_url=next_url or "")


# [MỚI] Đăng ký tài khoản
@app.route("/register", methods=["GET", "POST"])
def register():
    next_url = safe_next(request.values.get("next"))
    if "user" in session:
        return redirect(next_url or url_for("home"))

    username = ""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")

        loi = None
        if not re.fullmatch(r"[A-Za-z0-9_]{3,20}", username):
            loi = "Tên đăng nhập gồm 3-20 ký tự: chữ không dấu, số hoặc dấu gạch dưới."
        elif any(u.lower() == username.lower() for u in USERS):
            loi = "Tên đăng nhập đã tồn tại."
        elif len(password) < 6:
            loi = "Mật khẩu phải có ít nhất 6 ký tự."
        elif password != confirm:
            loi = "Mật khẩu nhập lại không khớp."

        if loi:
            flash(loi, "error")
        else:
            USERS[username] = generate_password_hash(password)
            session.clear()
            session["user"] = username  # đăng ký xong tự động đăng nhập
            flash(f"Đăng ký thành công. Xin chào {username}!", "success")
            return redirect(next_url or url_for("home"))

    return render_template("register.html", username=username, next_url=next_url or "")


@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("Bạn đã đăng xuất.", "success")
    return redirect(url_for("login"))


# ======================================================================
# ROUTE: QUẢN LÝ SỐ ĐIỂM SINH VIÊN
# (template: list.html, detail.html, not_found.html)
# [Nguồn: sodiem.py]
# ======================================================================
@app.route("/students")
@login_required
def students():
    danh_sach_lop = sorted({s["lop"] for s in STUDENTS.values()})
    lop_chon = request.args.get("lop", "").strip()
    q = request.args.get("q", "").strip()
    return render_template("list.html", rows=build_rows(lop_chon, q),
                           danh_sach_lop=danh_sach_lop, lop_chon=lop_chon, q=q)


@app.route("/api/students")
@login_required
def api_students():
    lop_chon = request.args.get("lop", "").strip()
    q = request.args.get("q", "").strip()
    return jsonify(build_rows(lop_chon, q))


@app.route("/students/<mssv>")
@login_required
def detail(mssv):
    s = STUDENTS.get(mssv)
    if s is None:
        return render_template("not_found.html", mssv=mssv), 404
    avg = diem_tb(s["scores"])
    short_url = url_for("short", mssv=mssv, _external=True)
    return render_template("detail.html", mssv=mssv, s=s, avg=avg,
                           rank=xep_loai_sv(avg), short_url=short_url)


@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    """Tìm theo MSSV hoặc họ tên. Đúng MSSV thì chuyển hướng 303 sang trang chi tiết."""
    q = (request.values.get("q") or request.values.get("mssv") or "").strip()
    if not q:
        return redirect(url_for("students"), code=303)

    mssv_khop = next((m for m in STUDENTS if m.lower() == q.lower()), None)
    if mssv_khop:
        return redirect(url_for("detail", mssv=mssv_khop), code=303)
    return redirect(url_for("students", q=q), code=303)


@app.route("/s/<mssv>")
@login_required
def short(mssv):
    """Link rút gọn, chuyển hướng 303 sang trang chi tiết."""
    return redirect(url_for("detail", mssv=mssv), code=303)


@app.route("/students/<mssv>/export")
@login_required
def export(mssv):
    s = STUDENTS.get(mssv)
    if s is None:
        return render_template("not_found.html", mssv=mssv), 404

    avg = diem_tb(s["scores"])
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["MSSV", "Họ tên", "Lớp", "Học phần", "Điểm"])
    for mon, diem in s["scores"].items():
        writer.writerow([mssv, s["name"], s["lop"], mon, diem])
    writer.writerow([mssv, s["name"], s["lop"], "Điểm TB", avg if avg is not None else "--"])
    writer.writerow([mssv, s["name"], s["lop"], "Xếp loại", xep_loai_sv(avg)])

    # utf-8-sig thêm BOM để Excel đọc đúng tiếng Việt có dấu
    resp = make_response(buf.getvalue().encode("utf-8-sig"))
    resp.headers["Content-Type"] = "text/csv; charset=utf-8"
    resp.headers["Content-Disposition"] = f'attachment; filename="bangdiem_{mssv}.csv"'
    return resp


# ======================================================================
# CHẠY ỨNG DỤNG
# [Nguồn: app.py] in thử URL tạo từ converter "list", rồi chạy server.
# (các file khác đều có app.run(debug=True) riêng -> chỉ giữ một lệnh này)
# ======================================================================
if __name__ == "__main__":
    with app.test_request_context():
        print(url_for("sum_numbers", numbers=[4, 5, 6]))  # /sum/4,5,6

    app.run(debug=True)
