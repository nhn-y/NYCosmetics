import hashlib
import math
import pandas as pd
import cloudinary
from datetime import datetime, timedelta
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
from nycosmetics.models import (User, UserRole, KhachHang, NhanVien, Admin, DanhMuc, ThuongHieu, SanPham, NhaCungCap, NhapKho,
                                ChiTietNhapKho, XuatKho, ChiTietXuatKho, DonHang, ChiTietDonHang, HanhVi)
from nycosmetics import db
from sqlalchemy import func

def load_categories():
    return DanhMuc.query.filter_by(trangThai=True).all()

def get_category_by_id(cate_id):
    return db.session.get(DanhMuc, cate_id)

def load_brands():
    return ThuongHieu.query.filter_by(trangThai=True).all()

def get_brand_by_id(brand_id):
    return db.session.get(ThuongHieu, brand_id)


# SẢN PHẨM

def generate_product_code():
    product = SanPham.query.order_by(
        SanPham.maSanPham.desc()
    ).first()

    if not product:
        return "SP000001"

    try:
        number = int(
            product.maSanPham[2:]
        )
    except:
        number = 0

    return f"SP{number + 1:06d}"

def get_product_by_id(ma_san_pham):
    return SanPham.query.filter(SanPham.maSanPham == ma_san_pham).first()

def load_products(cate_id=None, brand_id=None, kw=None, page=1, page_size=8, stock_status='TatCa'):
    query = SanPham.query

    # Lọc theo danh mục
    if cate_id and cate_id not in ['None', '0', '']:
        query = query.filter(SanPham.maDanhMuc == cate_id)

    # Lọc theo thương hiệu
    if brand_id and brand_id not in ['None', '0', '']:
        query = query.filter(SanPham.maThuongHieu == brand_id)

    # Tìm kiếm theo tên sản phẩm
    if kw:
        query = query.filter(SanPham.tenSanPham.ilike(f"%{kw}%"))

    if stock_status == 'DuoiTonToiThieu':
        query = query.filter(SanPham.soLuong <= SanPham.tonToiThieu)

    # Sắp xếp
    query = query.order_by(SanPham.maSanPham.asc())

    # Phân trang
    if page:
        query = query.offset((int(page) - 1) * page_size).limit(page_size)

    return query.all()

def count_product(cate_id=None, brand_id=None, kw=None, stock_status='TatCa'):
    query = SanPham.query

    if cate_id and cate_id not in ['None', '0', '']:
        query = query.filter(SanPham.maDanhMuc == cate_id)

    if brand_id and brand_id not in ['None', '0', '']:
        query = query.filter(SanPham.maThuongHieu == brand_id)

    if kw:
        query = query.filter(SanPham.tenSanPham.ilike(f"%{kw}%"))

    if stock_status == 'DuoiTonToiThieu':
        query = query.filter(SanPham.soLuong <= SanPham.tonToiThieu)

    return query.count()

def get_product_by_name(product_name):
    return SanPham.query.filter_by(tenSanPham=product_name).first()

def upload_product_image(file, ma_san_pham):
    if not file or not file.filename:
        return None

    allowed_extensions = {
        "jpg",
        "jpeg",
        "png",
        "webp"
    }

    extension = file.filename.rsplit(
        ".",
        1
    )[-1].lower()

    if extension not in allowed_extensions:
        raise ValueError(
            "Chỉ chấp nhận ảnh JPG, JPEG, PNG hoặc WEBP!"
        )

    result = cloudinary.uploader.upload(
        file,
        folder="nycosmetics/products",
        public_id=ma_san_pham,
        overwrite=True,
        resource_type="image"
    )

    return result["secure_url"]

# USER
def get_user_by_id(user_id):
    try:
        return db.session.get(User, int(user_id))
    except (ValueError, TypeError):
        return None

def get_user_by_userid(user_id):
    return get_user_by_id(user_id)

def check_username_exists(username):
    return User.query.filter(
        User.username == username.strip()
    ).first() is not None

def check_phone_exists(dienThoai):
    return User.query.filter(
        User.dienThoai == dienThoai.strip()
    ).first() is not None

def check_email_exists(email):
    return User.query.filter(
        User.email == email.strip()
    ).first() is not None

# ĐĂNG NHẬP

def auth_user(role, username, password):

    try:
        role = int(role)
    except (ValueError, TypeError):
        return None

    user = User.query.filter(
        User.userRole == role,
        User.username == username.strip()
    ).first()

    if user and check_password_hash(
        user.password,
        password.strip()
    ):
        return user

    return None

# ĐĂNG KÝ KHÁCH HÀNG

def generate_customer_code():
    last_customer = KhachHang.query.order_by(
        KhachHang.maKhachHang.desc()
    ).first()

    if not last_customer:
        return "KH000001"

    try:
        number = int(
            last_customer.maKhachHang[2:]
        ) + 1

        return f"KH{number:06d}"

    except (ValueError, TypeError):
        return "KH000001"

def add_user(name, username, password, email=None, dienThoai=None, avatar=None,
             gioiTinh=None, ngaySinh=None, diaChi=None):
    ma_khach_hang = generate_customer_code()

    customer = KhachHang(
        name=name.strip(),
        username=username.strip(),
        password=generate_password_hash(password.strip()),
        email=email.strip() if email else None,
        dienThoai=dienThoai.strip() if dienThoai else None,
        avatar=avatar,
        gioiTinh=gioiTinh.strip() if gioiTinh else None,
        ngaySinh=ngaySinh,
        diaChi=diaChi.strip() if diaChi else None,
        maKhachHang=ma_khach_hang,
        userRole=UserRole.KHACH_HANG,
        ngayDangKy=datetime.now(),
        trangThai=True
    )

    db.session.add(customer)
    db.session.commit()

    return customer

# TÌM USER THEO USERNAME + EMAIL
def get_user(username, email):

    return User.query.filter(
        User.username == username.strip(),
        User.email == email.strip()
    ).first()

# TÌM KHÁCH HÀNG THEO SDT
def get_customer_by_phone(dienThoai):
    return KhachHang.query.filter_by(dienThoai=dienThoai.strip()).first()


# TÌM KHÁCH HÀNG THEO MÃ
def get_customer_by_code(ma_khach_hang):
    return KhachHang.query.filter_by(maKhachHang=ma_khach_hang.strip()).first()

# TÌM USER THEO EMAIL
def get_user_by_email(email):

    return User.query.filter(
        User.email == email.strip()
    ).first()

# ĐỔI MẬT KHẨU
def update_password(email, new_password):

    try:
        user = User.query.filter(
            User.email == email.strip()
        ).first()

        if not user:
            return False

        user.password = generate_password_hash(
            new_password.strip()
        )

        db.session.commit()

        return True

    except Exception as e:

        print(f"Lỗi đổi mật khẩu: {e}")

        db.session.rollback()

        return False

# THÊM TÀI KHOẢN ADMIN
def add_admin(name, username, password, email, dienThoai, maAdmin):
    if Admin.query.filter_by(username=username).first():
        return False, "Username đã tồn tại!"

    if Admin.query.filter_by(email=email).first():
        return False, "Email đã tồn tại!"

    if Admin.query.filter_by(dienThoai=dienThoai).first():
        return False, "Số điện thoại đã tồn tại!"

    if Admin.query.filter_by(maAdmin=maAdmin).first():
        return False, "Mã Admin đã tồn tại!"

    admin = Admin(
        name=name,
        username=username,
        password=generate_password_hash(password),
        userRole=UserRole.ADMIN,
        email=email,
        dienThoai=dienThoai,
        maAdmin=maAdmin
    )

    db.session.add(admin)
    db.session.commit()

    return True, "Tạo tài khoản Admin thành công!"

# THÊM TÀI KHOẢN NHÂN VIÊN
def add_nhan_vien(name, username, password, email, dienThoai, maNhanVien):
    if NhanVien.query.filter_by(username=username).first():
        return False, "Username đã tồn tại!"

    if NhanVien.query.filter_by(email=email).first():
        return False, "Email đã tồn tại!"

    if NhanVien.query.filter_by(dienThoai=dienThoai).first():
        return False, "Số điện thoại đã tồn tại!"

    if NhanVien.query.filter_by(maNhanVien=maNhanVien).first():
        return False, "Mã nhân viên đã tồn tại!"

    nhan_vien = NhanVien(
        name=name,
        username=username,
        password=generate_password_hash(password),
        userRole=UserRole.NHAN_VIEN,
        email=email,
        dienThoai=dienThoai,
        maNhanVien=maNhanVien,
        trangThai=True
    )

    db.session.add(nhan_vien)
    db.session.commit()

    return True, "Tạo tài khoản nhân viên thành công!"

# ĐƠN HÀNG

def generate_order_code():
    last_order = (
        DonHang.query
        .filter(DonHang.maDonHang.like("DH%"))
        .order_by(DonHang.maDonHang.desc())
        .first()
    )

    if last_order:
        last_number = int(last_order.maDonHang[2:])
        new_number = last_number + 1
    else:
        new_number = 1

    return f"DH{new_number:010d}"

def get_order_by_id(ma_don_hang):
    return db.session.get(
        DonHang,
        ma_don_hang
    )
    #Lọc đơn chưa thanh toán
def get_unpaid_order(ma_don_hang):

    return DonHang.query.filter_by(
        maDonHang=ma_don_hang,
        trangThaiThanhToan="ChuaThanhToan"
    ).first()

def load_orders_by_customer(ma_khach_hang):

    return DonHang.query.filter(
        DonHang.maKhachHang == ma_khach_hang
    ).order_by(
        DonHang.ngayDat.desc()
    ).all()

def count_orders(
    status="TatCa",
    q=""
):
    query = DonHang.query

    if status != "TatCa":
        query = query.filter(
            DonHang.trangThai == status
        )

    if q:
        query = query.filter(
            db.or_(
                DonHang.maDonHang.ilike(
                    f"%{q}%"
                ),
                DonHang.khachHangRef.has(
                    KhachHang.dienThoai.ilike(
                        f"%{q}%"
                    )
                )
            )
        )

    return query.count()

def load_orders(
    status="TatCa",
    page=1,
    page_size=5,
    q=""
):
    query = DonHang.query

    if status != "TatCa":
        query = query.filter(
            DonHang.trangThai == status
        )

    if q:
        query = query.filter(
            db.or_(
                DonHang.maDonHang.ilike(
                    f"%{q}%"
                ),
                DonHang.khachHangRef.has(
                    KhachHang.dienThoai.ilike(
                        f"%{q}%"
                    )
                )
            )
        )

    query = query.order_by(
        DonHang.ngayDat.desc()
    )

    return query.paginate(
        page=page,
        per_page=page_size,
        error_out=False
    ).items

# CHI TIẾT ĐƠN HÀNG
    #Hủy đơn => Hoàn kho
def restore_order_stock(don_hang):
    for chi_tiet in don_hang.chiTietDonHangs:

        product = chi_tiet.sanPham

        if not product:
            continue

        product.soLuong += chi_tiet.soLuong

def load_order_details(order_id):

    return ChiTietDonHang.query.filter(
        ChiTietDonHang.maDonHang == order_id
    ).all()

# QL ĐƠN HÀNG
def count_pending_orders():
    return DonHang.query.filter(
        DonHang.trangThai == "ChoXacNhan"
    ).count()

def get_allowed_order_statuses(trang_thai):
    quy_tac = {
        "ChoXacNhan": [
            "ChoXacNhan",
            "DaXacNhan",
            "DaHuy"
        ],

        "DaXacNhan": [
            "DaXacNhan",
            "DangGiao",
            "DaHuy"
        ],

        "DangGiao": [
            "DangGiao",
            "DaGiao"
        ],

        "DaGiao": [
            "DaGiao"
        ],

        "DaHuy": [
            "DaHuy"
        ]
    }

    return quy_tac.get(
        trang_thai,
        []
    )

# TÀI KHOẢN
def load_accounts(
    q="",
    role="",
    page=1,
    page_size=5
):
    query = User.query.filter(
        User.type.in_([
            "admin",
            "nhanVien"
        ])
    )

    # Tìm kiếm
    if q:
        keyword = f"%{q}%"

        query = query.filter(
            db.or_(
                User.name.ilike(keyword),
                User.username.ilike(keyword),
                User.email.ilike(keyword),
                User.dienThoai.ilike(keyword)
            )
        )

    # Lọc loại tài khoản
    if role:
        if role == "admin":

            query = query.filter(
                User.type == "admin"
            )

        elif role == "nhanVien":

            query = query.filter(
                User.type == "nhanVien"
            )

    query = query.order_by(
        User.id.desc()
    )

    return query.paginate(
        page=page,
        per_page=page_size,
        error_out=False
    )

def count_accounts(
    q="",
    role=""
):
    query = User.query.filter(
        User.type.in_([
            "admin",
            "nhanVien"
        ])
    )

    if q:
        keyword = f"%{q}%"

        query = query.filter(
            db.or_(
                User.name.ilike(keyword),
                User.username.ilike(keyword),
                User.email.ilike(keyword),
                User.dienThoai.ilike(keyword)
            )
        )

    if role == "admin":

        query = query.filter(
            User.type == "admin"
        )

    elif role == "nhanVien":

        query = query.filter(
            User.type == "nhanVien"
        )

    return query.count()

def get_account_by_id(user_id):
    return User.query.filter(
        User.id == user_id,
        User.type.in_([
            "admin",
            "nhanVien"
        ])
    ).first()

def generate_admin_code():
    last_admin = Admin.query.order_by(
        Admin.maAdmin.desc()
    ).first()

    if not last_admin:
        return "AD000001"

    number = int(
        last_admin.maAdmin[2:]
    ) + 1

    return f"AD{number:06d}"

def generate_employee_code():
    last_employee = NhanVien.query.order_by(
        NhanVien.maNhanVien.desc()
    ).first()

    if not last_employee:
        return "NV000001"

    number = int(
        last_employee.maNhanVien[2:]
    ) + 1

    return f"NV{number:06d}"

# BÁO CÁO
def get_dashboard_statistics():
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)

    # =========================
    # DOANH THU HÔM NAY
    # =========================
    revenue_today = db.session.query(
        func.coalesce(func.sum(DonHang.tongTien), 0)
    ).filter(
        func.date(DonHang.ngayDat) == today,
        DonHang.trangThaiThanhToan == "DaThanhToan"
    ).scalar()

    # =========================
    # DOANH THU HÔM QUA
    # =========================
    revenue_yesterday = db.session.query(
        func.coalesce(func.sum(DonHang.tongTien), 0)
    ).filter(
        func.date(DonHang.ngayDat) == yesterday,
        DonHang.trangThaiThanhToan == "DaThanhToan"
    ).scalar()

    # =========================
    # SỐ ĐƠN HÔM NAY
    # =========================
    orders_today = DonHang.query.filter(
        func.date(DonHang.ngayDat) == today
    ).count()

    orders_yesterday = DonHang.query.filter(
        func.date(DonHang.ngayDat) == yesterday
    ).count()

    # =========================
    # KHÁCH HÀNG MỚI HÔM NAY
    # =========================
    customers_today = KhachHang.query.filter(
        func.date(KhachHang.ngayDangKy) == today
    ).count()

    customers_yesterday = KhachHang.query.filter(
        func.date(KhachHang.ngayDangKy) == yesterday
    ).count()

    # =========================
    # SẢN PHẨM BÁN RA HÔM NAY
    # =========================
    best_product_today = db.session.query(
        SanPham.tenSanPham,
        func.sum(ChiTietDonHang.soLuong).label("soLuongBan")
    ).join(
        ChiTietDonHang,
        SanPham.maSanPham == ChiTietDonHang.maSanPham
    ).join(
        DonHang,
        DonHang.maDonHang == ChiTietDonHang.maDonHang
    ).filter(
        func.date(DonHang.ngayDat) == today,
        DonHang.trangThaiThanhToan == "DaThanhToan"
    ).group_by(
        SanPham.maSanPham,
        SanPham.tenSanPham
    ).order_by(
        func.sum(ChiTietDonHang.soLuong).desc()
    ).first()

    best_product_name = (
        best_product_today.tenSanPham
        if best_product_today
        else "Chưa có"
    )

    best_product_quantity = (
        best_product_today.soLuongBan
        if best_product_today
        else 0
    )

    return {
        "revenue_today": revenue_today,
        "revenue_yesterday": revenue_yesterday,

        "orders_today": orders_today,
        "orders_yesterday": orders_yesterday,

        "customers_today": customers_today,
        "customers_yesterday": customers_yesterday,

        "best_product_name": best_product_name,
        "best_product_quantity": best_product_quantity
    }

    #Tính phần trăm tăng/giảm
def calculate_growth(current, previous):
    if previous == 0:
        if current == 0:
            return 0
        return 100

    return round(
        ((current - previous) / previous) * 100,
        1
    )

def get_revenue_last_7_days():
    today = datetime.now().date()

    result = []

    for i in range(6, -1, -1):
        date = today - timedelta(days=i)

        revenue = db.session.query(
            func.coalesce(func.sum(DonHang.tongTien), 0)
        ).filter(
            func.date(DonHang.ngayDat) == date,
            DonHang.trangThaiThanhToan == "DaThanhToan"
        ).scalar()

        result.append({
            "date": date.strftime("%d/%m"),
            "revenue": float(revenue or 0)
        })

    return result

    # Thống kê danh mục bán chạy, tính theo số lượng sản phẩm đã bán trong 7 ngày gần nhất.
def get_category_statistics():
    today = datetime.now().date()
    start_date = today - timedelta(days=6)

    result = db.session.query(
        DanhMuc.tenDanhMuc,
        func.sum(ChiTietDonHang.soLuong).label("soLuong")
    ).join(
        SanPham,
        SanPham.maDanhMuc == DanhMuc.maDanhMuc
    ).join(
        ChiTietDonHang,
        ChiTietDonHang.maSanPham == SanPham.maSanPham
    ).join(
        DonHang,
        DonHang.maDonHang == ChiTietDonHang.maDonHang
    ).filter(
        func.date(DonHang.ngayDat) >= start_date,
        func.date(DonHang.ngayDat) <= today,
        DonHang.trangThaiThanhToan == "DaThanhToan"
    ).group_by(
        DanhMuc.maDanhMuc,
        DanhMuc.tenDanhMuc
    ).order_by(
        func.sum(ChiTietDonHang.soLuong).desc()
    ).all()

    total = sum(item.soLuong for item in result)

    categories = []

    for item in result:
        percentage = (
            round((item.soLuong / total) * 100, 1)
            if total > 0
            else 0
        )

        categories.append({
            "name": item.tenDanhMuc,
            "quantity": item.soLuong,
            "percentage": percentage
        })

    return categories
    # Top 5 sản phẩm bán chạy
def get_top_products():
    today = datetime.now().date()
    start_date = today - timedelta(days=6)

    products = db.session.query(
        SanPham.maSanPham,
        SanPham.tenSanPham,
        SanPham.hinhAnh,
        DanhMuc.tenDanhMuc,
        func.sum(ChiTietDonHang.soLuong).label("soLuongBan"),
        func.sum(ChiTietDonHang.thanhTien).label("doanhThu")
    ).join(
        ChiTietDonHang,
        SanPham.maSanPham == ChiTietDonHang.maSanPham
    ).join(
        DonHang,
        DonHang.maDonHang == ChiTietDonHang.maDonHang
    ).join(
        DanhMuc,
        SanPham.maDanhMuc == DanhMuc.maDanhMuc
    ).filter(
        func.date(DonHang.ngayDat) >= start_date,
        func.date(DonHang.ngayDat) <= today,
        DonHang.trangThaiThanhToan == "DaThanhToan"
    ).group_by(
        SanPham.maSanPham,
        SanPham.tenSanPham,
        SanPham.hinhAnh,
        DanhMuc.tenDanhMuc
    ).order_by(
        func.sum(ChiTietDonHang.soLuong).desc()
    ).limit(5).all()

    return products

# HÀNH VI NGƯỜI DÙNG

def generate_behavior_code():
    last_behavior = HanhVi.query.order_by(
        HanhVi.maHanhVi.desc()
    ).first()

    if not last_behavior:
        return "HV00000001"

    try:
        number = int(last_behavior.maHanhVi[2:]) + 1
        return f"HV{number:08d}"

    except (ValueError, TypeError):
        return "HV00000001"


def add_behavior(user_id, ma_san_pham, loai_hanh_vi):
    try:
        # Kiểm tra dữ liệu đầu vào
        if not user_id or not ma_san_pham or not loai_hanh_vi:
            return None

        # Kiểm tra sản phẩm có tồn tại không
        san_pham = SanPham.query.filter(
            SanPham.maSanPham == ma_san_pham
        ).first()

        if not san_pham:
            print(f"Không tìm thấy sản phẩm: {ma_san_pham}")
            return None

        # Tạo mã hành vi
        ma_hanh_vi = generate_behavior_code()

        behavior = HanhVi(
            maHanhVi=ma_hanh_vi,
            userId=user_id,
            maSanPham=ma_san_pham,
            loaiHanhVi=loai_hanh_vi,
            thoiGian=datetime.now()
        )

        db.session.add(behavior)
        db.session.commit()

        return behavior

    except Exception as e:
        print(f"Lỗi lưu hành vi: {e}")
        db.session.rollback()

        return None

    # LẤY LỊCH SỬ HÀNH VI CỦA USER
def get_user_behaviors(user_id):
    return HanhVi.query.filter_by(
        userId=user_id
    ).order_by(
        HanhVi.thoiGian.desc()
    ).all()

    # LẤY HÀNH VI THEO SẢN PHẨM
def get_product_behaviors(ma_san_pham):
    return HanhVi.query.filter_by(
        maSanPham=ma_san_pham
    ).order_by(
        HanhVi.thoiGian.desc()
    ).all()

def get_all_behaviors():
    return HanhVi.query.order_by(HanhVi.thoiGian.desc()).all()

def get_behaviors_by_type(loai_hanh_vi):

    return HanhVi.query.filter(
        HanhVi.loaiHanhVi == loai_hanh_vi
    ).order_by(
        HanhVi.thoiGian.desc()
    ).all()
