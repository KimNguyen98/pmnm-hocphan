import csv
import io

from flask import (Flask, render_template_string, request, jsonify,
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


# ---------- Giao diện ----------

STYLE = """
<style>
  html { background: #eef2f7; }
  body {
    font-family: "Segoe UI", Arial, sans-serif;
    max-width: 860px;
    margin: 40px auto;
    padding: 28px 32px;
    background: #ffffff;
    color: #1f2937;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    line-height: 1.6;
  }
  h2 { margin-top: 0; color: #1e3a8a; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px; }
  h3 { color: #374151; margin-top: 28px; }
  a { color: #2563eb; text-decoration: none; }
  a:hover { text-decoration: underline; }

  table {
    border-collapse: collapse;
    width: 100%;
    margin: 12px 0;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 0 0 1px #e5e7eb;
  }
  th, td { padding: 10px 14px; text-align: left; }
  th { background: #1e3a8a; color: #ffffff; font-weight: 600; }
  tr:nth-child(even) td { background: #f9fafb; }
  tr:hover td { background: #eff6ff; }
  td { border-bottom: 1px solid #e5e7eb; }

  .filter a {
    display: inline-block;
    padding: 6px 16px;
    margin: 0 6px 6px 0;
    border: 1px solid #cbd5e1;
    border-radius: 999px;
    color: #374151;
    background: #ffffff;
    transition: all 0.15s;
  }
  .filter a:hover { background: #eff6ff; border-color: #2563eb; text-decoration: none; }
  .filter a.active { background: #2563eb; border-color: #2563eb; color: #ffffff; }

  form { display: flex; gap: 8px; margin-top: 8px; }
  input {
    flex: 1;
    padding: 9px 12px;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    font-size: 15px;
  }
  input:focus { outline: none; border-color: #2563eb; box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.2); }
  button {
    padding: 9px 20px;
    border: none;
    border-radius: 8px;
    background: #2563eb;
    color: #ffffff;
    font-size: 15px;
    cursor: pointer;
  }
  button:hover { background: #1d4ed8; }

  ul { padding-left: 20px; }
  li { margin: 6px 0; }
  b { color: #111827; }
</style>
"""

HOME_PAGE = """
<!doctype html>
<html lang="vi">
<head><meta charset="utf-8"><title>Trang chủ</title>""" + STYLE + """</head>
<body>
  <h2>Quản lý số điểm sinh viên</h2>
  <p>Tổng số sinh viên: <b>{{ tong_sv }}</b></p>
  <p>Số lớp: <b>{{ so_lop }}</b></p>
  <ul>
    <li><a href="{{ url_for('students') }}">Danh sách sinh viên</a> (/students)</li>
    <li><a href="{{ url_for('api_students') }}">API sinh viên (JSON)</a> (/api/students)</li>
  </ul>

  <h3>Tìm sinh viên theo MSSV hoặc họ tên</h3>
  <form method="post" action="{{ url_for('search') }}">
    <input name="q" placeholder="Nhập MSSV hoặc họ tên" required>
    <button type="submit">Tìm</button>
  </form>
</body>
</html>
"""

LIST_PAGE = """
<!doctype html>
<html lang="vi">
<head><meta charset="utf-8"><title>Danh sách sinh viên</title>""" + STYLE + """</head>
<body>
  <h2>Danh sách sinh viên</h2>
  <form method="get" action="{{ url_for('students') }}">
    {% if lop_chon %}<input type="hidden" name="lop" value="{{ lop_chon }}">{% endif %}
    <input name="q" value="{{ q }}" placeholder="Tìm theo MSSV hoặc họ tên">
    <button type="submit">Tìm</button>
  </form>
  <br>
  <div class="filter">
    <a href="{{ url_for('students') }}" class="{{ 'active' if not lop_chon }}">Tất cả</a>
    {% for l in danh_sach_lop %}
      <a href="{{ url_for('students', lop=l) }}"
         class="{{ 'active' if lop_chon and l.lower() == lop_chon.lower() }}">{{ l }}</a>
    {% endfor %}
  </div>
  <br>

  {% if rows %}
  <table>
    <tr><th>MSSV</th><th>Họ tên</th><th>Lớp</th><th>Điểm TB</th><th>Xếp loại</th></tr>
    {% for r in rows %}
    <tr>
      <td><a href="{{ url_for('detail', mssv=r.mssv) }}">{{ r.mssv }}</a></td>
      <td>{{ r.name }}</td>
      <td>{{ r.lop }}</td>
      <td>{{ r.avg if r.avg is not none else '--' }}</td>
      <td>{{ r.rank }}</td>
    </tr>
    {% endfor %}
  </table>
  {% else %}
  <p>Không có sinh viên phù hợp.</p>
  {% endif %}

  <p><a href="{{ url_for('index') }}">&larr; Về trang chủ</a></p>
</body>
</html>
"""

DETAIL_PAGE = """
<!doctype html>
<html lang="vi">
<head><meta charset="utf-8"><title>{{ s.name }}</title>""" + STYLE + """</head>
<body>
  <h2>{{ s.name }}</h2>
  <p>MSSV: <b>{{ mssv }}</b></p>
  <p>Lớp: <a href="{{ url_for('students', lop=s.lop) }}">{{ s.lop }}</a></p>
  <p>Điểm TB: <b>{{ avg if avg is not none else '--' }}</b></p>
  <p>Xếp loại: <b>{{ rank }}</b></p>

  <h3>Bảng điểm từng học phần</h3>
  {% if s.scores %}
  <table>
    <tr><th>Học phần</th><th>Điểm</th></tr>
    {% for mon, diem in s.scores.items() %}
    <tr><td>{{ mon }}</td><td>{{ diem }}</td></tr>
    {% endfor %}
  </table>
  {% else %}
  <p>Chưa có điểm.</p>
  {% endif %}

  <p><a href="{{ url_for('export', mssv=mssv) }}">Tải bảng điểm (CSV)</a></p>
  <p>Link rút gọn: <a href="{{ short_url }}">{{ short_url }}</a></p>
  <p><a href="{{ url_for('students') }}">&larr; Quay lại danh sách</a></p>
</body>
</html>
"""

NOT_FOUND_PAGE = """
<!doctype html>
<html lang="vi">
<head><meta charset="utf-8"><title>Không tìm thấy</title>""" + STYLE + """</head>
<body>
  <h2>Không tìm thấy sinh viên</h2>
  <p>Không có sinh viên nào có MSSV <b>{{ mssv }}</b>.</p>
  <p><a href="{{ url_for('students') }}">&larr; Quay lại danh sách</a></p>
</body>
</html>
"""


# ---------- Route ----------

@app.route("/")
def index():
    tong_sv = len(STUDENTS)
    so_lop = len({s["lop"] for s in STUDENTS.values()})
    return render_template_string(HOME_PAGE, tong_sv=tong_sv, so_lop=so_lop)



@app.route("/students")
def students():
    danh_sach_lop = sorted({s["lop"] for s in STUDENTS.values()})
    lop_chon = request.args.get("lop", "").strip()
    q = request.args.get("q", "").strip()
    return render_template_string(LIST_PAGE, rows=build_rows(lop_chon, q),
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
        return render_template_string(NOT_FOUND_PAGE, mssv=mssv), 404
    avg = diem_tb(s["scores"])
    short_url = url_for("short", mssv=mssv, _external=True)
    return render_template_string(DETAIL_PAGE, mssv=mssv, s=s, avg=avg,
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
        return render_template_string(NOT_FOUND_PAGE, mssv=mssv), 404

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