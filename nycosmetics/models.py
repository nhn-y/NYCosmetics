from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash
import json
import os
from nycosmetics import db


# ============================================================
# PHÂN QUYỀN
# ============================================================
class UserRole:
    KHACH_HANG = 0
    ADMIN = 1
    NHAN_VIEN = 2


# ============================================================
# 1. USER - LỚP CHA
# ============================================================
class User(db.Model, UserMixin):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    userRole = db.Column(db.Integer, nullable=False, default=UserRole.KHACH_HANG)
    avatar = db.Column(db.String(255))
    email = db.Column(db.String(100), unique=True)
    dienThoai = db.Column(db.String(15), unique=True)
    type = db.Column(db.String(20), nullable=False)

    __mapper_args__ = {
        "polymorphic_on": type,
        "polymorphic_identity": "user"
    }


# ============================================================
# 2. KHÁCH HÀNG
# ============================================================
class KhachHang(User):
    __tablename__ = "khachHang"

    id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    maKhachHang = db.Column(db.String(8), unique=True, nullable=False)
    gioiTinh = db.Column(db.String(10))
    ngaySinh = db.Column(db.Date)
    diaChi = db.Column(db.String(255))
    ngayDangKy = db.Column(db.DateTime)
    trangThai = db.Column(db.Boolean, nullable=False, default=True)

    donHangs = db.relationship("DonHang", backref="khachHangRef", lazy=True)

    __mapper_args__ = {
        "polymorphic_identity": "khachHang"
    }


# ============================================================
# 3. NHÂN VIÊN
# ============================================================
class NhanVien(User):
    __tablename__ = "nhanVien"

    id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    maNhanVien = db.Column(db.String(8), unique=True, nullable=False)
    trangThai = db.Column(db.Boolean, nullable=False, default=True)

    donHangs = db.relationship("DonHang", backref="nhanVienRef", lazy=True)
    phieuNhapKhos = db.relationship("NhapKho", backref="nhanVienRef", lazy=True)
    phieuXuatKhos = db.relationship("XuatKho", backref="nhanVienRef", lazy=True)

    __mapper_args__ = {
        "polymorphic_identity": "nhanVien"
    }


# ============================================================
# 4. ADMIN
# ============================================================
class Admin(User):
    __tablename__ = "admin"

    id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    maAdmin = db.Column(db.String(8), unique=True, nullable=False)

    __mapper_args__ = {
        "polymorphic_identity": "admin"
    }


# ============================================================
# 5. DANH MỤC
# ============================================================
class DanhMuc(db.Model):
    __tablename__ = "danhMuc"

    maDanhMuc = db.Column(db.String(8), primary_key=True)
    tenDanhMuc = db.Column(db.String(100), unique=True, nullable=False)
    moTa = db.Column(db.Text)
    trangThai = db.Column(db.Boolean, nullable=False, default=True)

    sanPhams = db.relationship("SanPham", backref="danhMucRef", lazy=True)


# ============================================================
# 6. THƯƠNG HIỆU
# ============================================================
class ThuongHieu(db.Model):
    __tablename__ = "thuongHieu"

    maThuongHieu = db.Column(db.String(8), primary_key=True)
    tenThuongHieu = db.Column(db.String(100), unique=True, nullable=False)
    quocGia = db.Column(db.String(100))
    logo = db.Column(db.String(255))
    moTa = db.Column(db.Text)
    trangThai = db.Column(db.Boolean, nullable=False, default=True)

    sanPhams = db.relationship("SanPham", backref="thuongHieuRef", lazy=True)


# ============================================================
# 7. SẢN PHẨM
# ============================================================
class SanPham(db.Model):
    __tablename__ = "sanPham"

    maSanPham = db.Column(db.String(8), primary_key=True)
    tenSanPham = db.Column(db.String(150), nullable=False)

    maDanhMuc = db.Column(
        db.String(8),
        db.ForeignKey("danhMuc.maDanhMuc"),
        nullable=False
    )

    maThuongHieu = db.Column(
        db.String(8),
        db.ForeignKey("thuongHieu.maThuongHieu"),
        nullable=False
    )

    giaBan = db.Column(db.Numeric(12, 2), nullable=False)
    giaNhap = db.Column(db.Numeric(12, 2), nullable=False)
    soLuong = db.Column(db.Integer, nullable=False, default=0)
    hinhAnh = db.Column(db.String(255))
    moTa = db.Column(db.Text)
    thanhPhan = db.Column(db.Text)
    congDung = db.Column(db.Text)
    trangThai = db.Column(db.Boolean, nullable=False, default=True)

    tonToiThieu = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    chiTietDonHangs = db.relationship(
        "ChiTietDonHang",
        back_populates="sanPham",
        lazy=True
    )

    chiTietNhapKhos = db.relationship(
        "ChiTietNhapKho",
        back_populates="sanPham",
        lazy=True
    )

    chiTietXuatKhos = db.relationship(
        "ChiTietXuatKho",
        back_populates="sanPham",
        lazy=True
    )

# ============================================================
# 8. NHÀ CUNG CẤP
# ============================================================
class NhaCungCap(db.Model):
    __tablename__ = "nhaCungCap"

    maNhaCungCap = db.Column(db.String(8), primary_key=True)
    tenNhaCungCap = db.Column(db.String(150), nullable=False)
    dienThoai = db.Column(db.String(15))
    email = db.Column(db.String(100))
    diaChi = db.Column(db.String(255))
    trangThai = db.Column(db.Boolean, nullable=False, default=True)

    phieuNhapKhos = db.relationship(
        "NhapKho",
        backref="nhaCungCapRef",
        lazy=True
    )

# ============================================================
# 9. PHIẾU NHẬP KHO
# ============================================================
class NhapKho(db.Model):
    __tablename__ = "nhapKho"

    maPhieuNhap = db.Column(db.String(10), primary_key=True)

    maNhaCungCap = db.Column(
        db.String(8),
        db.ForeignKey("nhaCungCap.maNhaCungCap"),
        nullable=False
    )

    maNhanVien = db.Column(
        db.String(8),
        db.ForeignKey("nhanVien.maNhanVien"),
        nullable=False
    )

    ngayNhap = db.Column(db.DateTime, nullable=False)
    tongTien = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    ghiChu = db.Column(db.Text)

    chiTiet = db.relationship(
        "ChiTietNhapKho",
        backref="nhapKhoRef",
        lazy=True
    )


# ============================================================
# 10. CHI TIẾT NHẬP KHO
# ============================================================
class ChiTietNhapKho(db.Model):
    __tablename__ = "chiTietNhapKho"

    maPhieuNhap = db.Column(
        db.String(10),
        db.ForeignKey("nhapKho.maPhieuNhap"),
        primary_key=True
    )

    maSanPham = db.Column(
        db.String(8),
        db.ForeignKey("sanPham.maSanPham"),
        primary_key=True
    )

    soLuong = db.Column(db.Integer, nullable=False)
    giaNhap = db.Column(db.Numeric(12, 2), nullable=False)
    thanhTien = db.Column(db.Numeric(14, 2), nullable=False)

    sanPham = db.relationship(
        "SanPham",
        back_populates="chiTietNhapKhos"
    )

# ============================================================
# 11. PHIẾU XUẤT KHO
# ============================================================
class XuatKho(db.Model):
    __tablename__ = "xuatKho"

    maPhieuXuat = db.Column(db.String(10), primary_key=True)

    maNhanVien = db.Column(
        db.String(8),
        db.ForeignKey("nhanVien.maNhanVien"),
        nullable=False
    )

    ngayXuat = db.Column(db.DateTime, nullable=False)
    lyDo = db.Column(db.String(255))
    ghiChu = db.Column(db.Text)

    chiTiet = db.relationship(
        "ChiTietXuatKho",
        backref="xuatKhoRef",
        lazy=True
    )


# ============================================================
# 12. CHI TIẾT XUẤT KHO
# ============================================================
class ChiTietXuatKho(db.Model):
    __tablename__ = "chiTietXuatKho"

    maPhieuXuat = db.Column(
        db.String(10),
        db.ForeignKey("xuatKho.maPhieuXuat"),
        primary_key=True
    )

    maSanPham = db.Column(
        db.String(8),
        db.ForeignKey("sanPham.maSanPham"),
        primary_key=True
    )

    soLuong = db.Column(db.Integer, nullable=False)

    sanPham = db.relationship(
        "SanPham",
        back_populates="chiTietXuatKhos"
    )

# ============================================================
# 13. ĐƠN HÀNG
# ============================================================
class DonHang(db.Model):
    __tablename__ = "donHang"

    maDonHang = db.Column(db.String(12), primary_key=True)

    maKhachHang = db.Column(
        db.String(8),
        db.ForeignKey("khachHang.maKhachHang"),
        nullable=False
    )
    maNhanVien = db.Column(
        db.String(8),
        db.ForeignKey("nhanVien.maNhanVien"),
        nullable=True
    )

    ngayDat = db.Column(db.DateTime, nullable=False)
    tongTien = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    trangThai = db.Column(db.String(30), nullable=False, default="ChoXacNhan")
    diaChiGiao = db.Column(db.String(255))
    ghiChu = db.Column(db.Text)

    phuongThucThanhToan = db.Column(
        db.String(30),
        nullable=False
    )

    trangThaiThanhToan = db.Column(
        db.String(30),
        nullable=False,
        default="ChuaThanhToan"
    )

    ngayThanhToan = db.Column(
        db.DateTime
    )

    chiTietDonHangs = db.relationship(
        "ChiTietDonHang",
        back_populates="donHang",
        lazy=True
    )

# ============================================================
# 14. CHI TIẾT ĐƠN HÀNG
# ============================================================
class ChiTietDonHang(db.Model):
    __tablename__ = "chiTietDonHang"

    maDonHang = db.Column(
        db.String(12),
        db.ForeignKey("donHang.maDonHang"),
        primary_key=True
    )

    maSanPham = db.Column(
        db.String(8),
        db.ForeignKey("sanPham.maSanPham"),
        primary_key=True
    )

    soLuong = db.Column(db.Integer, nullable=False)
    donGia = db.Column(db.Numeric(12, 2), nullable=False)
    thanhTien = db.Column(db.Numeric(14, 2), nullable=False)

    sanPham = db.relationship(
        "SanPham",
        back_populates="chiTietDonHangs"
    )
    donHang = db.relationship(
        "DonHang",
        back_populates="chiTietDonHangs"
    )


# ============================================================
# 15. LỊCH SỬ HÀNH VI KHÁCH HÀNG
# ============================================================
class HanhVi(db.Model):
    __tablename__ = "hanhVi"

    maHanhVi = db.Column(
        db.String(10),
        primary_key=True
    )

    userId = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    maSanPham = db.Column(
        db.String(8),
        db.ForeignKey("sanPham.maSanPham"),
        nullable=False
    )

    loaiHanhVi = db.Column(
        db.String(30),
        nullable=False
    )

    thoiGian = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.now
    )

    user = db.relationship(
        "User",
        backref="hanhVis"
    )

    sanPham = db.relationship(
        "SanPham",
        backref="hanhVis"
    )