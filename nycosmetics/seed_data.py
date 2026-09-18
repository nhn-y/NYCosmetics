import json
from werkzeug.security import generate_password_hash
from datetime import datetime
from nycosmetics import app, db
from nycosmetics.models import UserRole, NhanVien, Admin, DanhMuc, ThuongHieu, SanPham




# ============================================================
# ĐỌC FILE JSON
# ============================================================

def load_json(file_path):

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# ============================================================
# IMPORT DANH MỤC
# ============================================================

def import_categories():

    categories = load_json(
        "data/category.json"
    )

    count = 0

    for item in categories:

        existing = db.session.get(
            DanhMuc,
            item["maDanhMuc"]
        )

        if existing:
            print(
                f"Danh mục {item['maDanhMuc']} đã tồn tại."
            )
            continue

        category = DanhMuc(
            maDanhMuc=item["maDanhMuc"],
            tenDanhMuc=item["tenDanhMuc"],
            moTa=item.get("moTa"),
            trangThai=True
        )

        db.session.add(category)

        count += 1

    db.session.commit()

    print(
        f"Đã thêm {count} danh mục."
    )


# ============================================================
# IMPORT THƯƠNG HIỆU
# ============================================================

def import_brands():

    brands = load_json(
        "data/brand.json"
    )

    count = 0

    for item in brands:

        existing = db.session.get(
            ThuongHieu,
            item["maThuongHieu"]
        )

        if existing:
            print(
                f"Thương hiệu {item['maThuongHieu']} đã tồn tại."
            )
            continue

        brand = ThuongHieu(
            maThuongHieu=item["maThuongHieu"],
            tenThuongHieu=item["tenThuongHieu"],
            quocGia=item.get("quocGia"),
            logo=item.get("logo"),
            moTa=item.get("moTa"),
            trangThai=True
        )

        db.session.add(brand)

        count += 1

    db.session.commit()

    print(
        f"Đã thêm {count} thương hiệu."
    )


# ============================================================
# IMPORT SẢN PHẨM
# ============================================================

def import_products():

    products = load_json(
        "data/product.json"
    )

    count = 0

    for item in products:

        existing = db.session.get(
            SanPham,
            item["maSanPham"]
        )

        if existing:
            print(
                f"Sản phẩm {item['maSanPham']} đã tồn tại."
            )
            continue


        # Kiểm tra danh mục

        category = db.session.get(
            DanhMuc,
            item["maDanhMuc"]
        )

        if not category:

            print(
                f"Không tìm thấy danh mục "
                f"{item['maDanhMuc']} "
                f"của sản phẩm "
                f"{item['maSanPham']}."
            )

            continue


        # Kiểm tra thương hiệu

        brand = db.session.get(
            ThuongHieu,
            item["maThuongHieu"]
        )

        if not brand:

            print(
                f"Không tìm thấy thương hiệu "
                f"{item['maThuongHieu']} "
                f"của sản phẩm "
                f"{item['maSanPham']}."
            )

            continue


        # Tạo sản phẩm

        product = SanPham(
            maSanPham=item["maSanPham"],
            tenSanPham=item["tenSanPham"],
            maDanhMuc=item["maDanhMuc"],
            maThuongHieu=item["maThuongHieu"],
            giaBan=item["giaBan"],
            giaNhap=item["giaNhap"],
            soLuong=item.get("soLuong", 0),
            hinhAnh=item.get("hinhAnh"),
            moTa=item.get("moTa"),
            thanhPhan=item.get("thanhPhan"),
            congDung=item.get("congDung"),
            trangThai=True,
            tonToiThieu=0
        )

        db.session.add(product)

        count += 1

    db.session.commit()

    print(
        f"Đã thêm {count} sản phẩm."
    )

def create_admin():

    if Admin.query.filter_by(username="admin").first():
        print("Tài khoản admin đã tồn tại!")
        return

    admin = Admin(
        name="Quản trị viên",
        username="admin",
        password=generate_password_hash("Admin@123"),
        userRole=UserRole.ADMIN,
        avatar=None,
        email="admin@nycosmetic.com",
        dienThoai="0900000000",
        maAdmin="AD000001"
    )

    db.session.add(admin)
    db.session.commit()

    print("Đã tạo tài khoản ADMIN")


def create_nhan_vien():

    if NhanVien.query.filter_by(username="nhanvien01").first():
        print("Tài khoản nhân viên đã tồn tại!")
        return

    nhan_vien = NhanVien(
        name="Nhân viên 01",
        username="nhanvien01",
        password=generate_password_hash("NhanVien@123"),
        userRole=UserRole.NHAN_VIEN,
        avatar=None,
        email="nhanvien01@nycosmetic.com",
        dienThoai="0911111111",
        maNhanVien="NV000001",
        trangThai=True
    )

    db.session.add(nhan_vien)
    db.session.commit()

    print("Đã tạo tài khoản NHÂN VIÊN")

# ============================================================
# CHẠY IMPORT
# ============================================================

if __name__ == "__main__":

    with app.app_context():
        print(
            "BẮT ĐẦU IMPORT DỮ LIỆU"
        )
        #
        # # 1. Danh mục
        #
        # import_categories()
        #
        #
        # # 2. Thương hiệu
        #
        import_brands()
        #
        #
        # # 3. Sản phẩm
        #
        import_products()
        #
        # create_admin()
        # create_nhan_vien()
        print(
            "IMPORT DỮ LIỆU HOÀN TẤT!"
        )
