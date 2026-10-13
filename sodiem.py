import csv
import io

from flask import (Flask, render_template, request, jsonify,
                   redirect, url_for, make_response)

app = Flask(__name__)
app.json.ensure_ascii = False  # JSON hiển thị tiếng Việt có dấu

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


# ---------- Hàm hỗ trợ ----------

def diem_tb(scores):
    """Điểm trung bình, None nếu chưa có điểm."""
    if not scores:
        return None
    return round(sum(scores.values()) / len(scores), 2)


def xep_loai(avg):
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
                     "avg": avg, "rank": xep_loai(avg)})
    return rows


# ---------- Route ----------

@app.route("/")
def index():
    tong_sv = len(STUDENTS)
    so_lop = len({s["lop"] for s in STUDENTS.values()})
    return render_template("home.html", tong_sv=tong_sv, so_lop=so_lop)


@app.route("/students")
def students():
    danh_sach_lop = sorted({s["lop"] for s in STUDENTS.values()})
    lop_chon = request.args.get("lop", "").strip()
    q = request.args.get("q", "").strip()
    return render_template("list.html", rows=build_rows(lop_chon, q),
                           danh_sach_lop=danh_sach_lop, lop_chon=lop_chon, q=q)


@app.route("/api/students")
def api_students():
    lop_chon = request.args.get("lop", "").strip()
    q = request.args.get("q", "").strip()
    return jsonify(build_rows(lop_chon, q))


@app.route("/students/<mssv>")
def detail(mssv):
    s = STUDENTS.get(mssv)
    if s is None:
        return render_template("not_found.html", mssv=mssv), 404
    avg = diem_tb(s["scores"])
    short_url = url_for("short", mssv=mssv, _external=True)
    return render_template("detail.html", mssv=mssv, s=s, avg=avg,
                           rank=xep_loai(avg), short_url=short_url)


@app.route("/search", methods=["GET", "POST"])
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
def short(mssv):
    """Link rút gọn, chuyển hướng 303 sang trang chi tiết."""
    return redirect(url_for("detail", mssv=mssv), code=303)


@app.route("/students/<mssv>/export")
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
    writer.writerow([mssv, s["name"], s["lop"], "Xếp loại", xep_loai(avg)])

    # utf-8-sig thêm BOM để Excel đọc đúng tiếng Việt có dấu
    resp = make_response(buf.getvalue().encode("utf-8-sig"))
    resp.headers["Content-Type"] = "text/csv; charset=utf-8"
    resp.headers["Content-Disposition"] = f'attachment; filename="bangdiem_{mssv}.csv"'
    return resp


if __name__ == "__main__":
    app.run(debug=True)