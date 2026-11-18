from app import create_app
from extensions import db
from models import DanhMuc, Sach

app = create_app()
with app.app_context():
    if DanhMuc.query.count() == 0:
        dm1 = DanhMuc(ten="Lập trình", mo_ta="Sách lập trình")
        dm2 = DanhMuc(ten="Cơ sở dữ liệu", mo_ta="Sách CSDL")
        dm3 = DanhMuc(ten="Mạng", mo_ta="Sách mạng máy tính")
        dm4 = DanhMuc(ten="Công cụ", mo_ta="Git, Docker...")
        dm5 = DanhMuc(ten="Kỹ năng lập trình", mo_ta="Clean Code...")
        db.session.add_all([dm1, dm2, dm3, dm4, dm5])
        db.session.flush()

        db.session.add_all([
            Sach(tieu_de="Lập trình Python cơ bản", tac_gia="Nguyễn Văn A", nxb="NXB ĐH Huế",
                 nam=2024, gia=95000, so_luong=30, danh_muc_id=dm1.id,
                 mo_ta="Nhập môn Python qua các ví dụ ngắn."),
            Sach(tieu_de="Giáo trình Flask", tac_gia="Trần Thị B", nxb="NXB ĐH Huế",
                 nam=2024, gia=120000, so_luong=20, danh_muc_id=dm1.id,
                 mo_ta="Xây dựng ứng dụng web với Flask, từ route đến CSDL."),
            Sach(tieu_de="Cơ sở dữ liệu", tac_gia="Lê Văn C", gia=85000, so_luong=0, danh_muc_id=dm2.id),
            Sach(tieu_de="Pro Git", tac_gia="Scott Chacon", gia=150000, so_luong=15, danh_muc_id=dm4.id),
            Sach(tieu_de="Mạng máy tính", tac_gia="Phạm D", gia=110000, so_luong=12, danh_muc_id=dm3.id),
            Sach(tieu_de="Clean Code", tac_gia="Robert C. Martin", gia=180000, so_luong=5, danh_muc_id=dm5.id),
        ])
        db.session.commit()
        print("Đã thêm dữ liệu mẫu!")
    else:
        print("Dữ liệu đã có.")