import datetime
import math
import random
import re
import cloudinary
import cloudinary.uploader
from datetime import datetime
from flask import render_template, session, request, jsonify, redirect, url_for, current_app, flash
from flask_login import current_user, login_user, logout_user, login_required
from flask_mail import Message, Mail
from werkzeug.security import generate_password_hash
from nycosmetics import app, db, dao, login
from nycosmetics.dao import restore_order_stock, get_allowed_order_statuses, upload_product_image
from nycosmetics.models import DonHang, ChiTietDonHang, UserRole, User, NhanVien, Admin, SanPham
from nycosmetics.data_mining.recommendation_service import get_recommendations

mail = Mail()
otp_storage = {}


def register_routes(app):
    global mail
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'nhuy06022005@gmail.com'
    app.config['MAIL_PASSWORD'] = 'dzfn wfqh jqbf zscn'
    app.config['MAIL_DEFAULT_SENDER'] = 'nhuy06022005@gmail.com'
    app.config["BANK_ID"] = "970422" #MB Bank
    app.config["BANK_ACCOUNT"] = "0362966599"
    app.config["BANK_ACCOUNT_NAME"] = "NGUYEN HUYNH NHU Y"
    mail.init_app(app)

    # mail = Mail(app)

    # TRANG CHỦ
    @app.route("/")
    def index():
        page = request.args.get("page", 1, type=int)
        cate_id = request.args.get("category_id")
        brand_id = request.args.get("brand_id")
        kw = request.args.get("kw")

        categories = dao.load_categories()
        brands = dao.load_brands()

        page_size = 8

        products = dao.load_products(
            kw=kw,
            cate_id=cate_id,
            brand_id=brand_id,
            page=page,
            page_size=page_size
        )

        total_products = dao.count_product(
            cate_id=cate_id,
            brand_id=brand_id,
            kw=kw
        )

        total_pages = math.ceil(total_products / page_size)

        cart = session.get("cart", {})
        total_quantity = sum(
            int(item["quantity"])
            for item in cart.values()
        )

        return render_template(
            "customer/customer.html",
            categories=categories,
            brands=brands,
            products=products,
            pages=total_pages,
            current_page=page,
            total_products=total_products,
            total_quantity=total_quantity
        )

    @app.route("/product/<string:product_name>")
    def product_detail(product_name):
        product = dao.get_product_by_name(product_name)

        if not product:
            return "Không tìm thấy sản phẩm!", 404

        recommended_products = get_recommendations(
            ma_san_pham=product.maSanPham,
            user_id=current_user.id if current_user.is_authenticated else None,
            limit=4
        )

        user_id = (current_user.id
            if current_user.is_authenticated
            else None
        )

        # Ghi nhận hành vi XEM
        if user_id is not None:
            dao.add_behavior(current_user.id, product.maSanPham,"XEM")

        return render_template(
            "customer/product_detail.html",
            product=product,
            recommended_products=recommended_products
        )

    # LOGIN
    @app.route("/login", methods=['GET', 'POST'])
    def user_login():
        if current_user.is_authenticated:
            return redirect('/admin' if int(current_user.userRole) in [1, 2] else '/')
        err_msg = None
        if request.method == 'POST':
            user = dao.auth_user(request.form.get("role"), request.form.get("username"), request.form.get("password"))
            if user:
                login_user(user)
                return redirect('/admin' if int(user.userRole) in [1, 2] else '/')
            err_msg = "Sai tài khoản hoặc mật khẩu!"
        return render_template("login.html", err_msg=err_msg)

    @app.route("/register", methods=['get', 'post'])
    def register():
        err_msg = None
        current_date = datetime.now().strftime("%Y-%m-%d")

        if request.method.__eq__("POST"):
            name = request.form.get("name")
            username = request.form.get("username")
            password = request.form.get("password")
            confirm = request.form.get("confirm")
            email = request.form.get("email")
            dienThoai = request.form.get("dienThoai")
            gioiTinh = request.form.get("gioiTinh")
            ngaySinh = request.form.get("ngaySinh")
            diaChi = request.form.get("diaChi")
            avatar = request.files.get("avatar")

            password_pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"

            ngaySinhDate = None
            if ngaySinh:
                try:
                    ngaySinhDate = datetime.strptime(ngaySinh, "%Y-%m-%d").date()
                except ValueError:
                    ngaySinhDate = None

            if not name or not name.strip():
                err_msg = "Họ tên không được để trống!"
            elif not username or not username.strip():
                err_msg = "Tên tài khoản không được để trống!"
            elif not email or not email.strip():
                err_msg = "Email không được để trống!"
            elif not dienThoai or not dienThoai.strip():
                err_msg = "Số điện thoại không được để trống!"
            elif not diaChi or not diaChi.strip():
                err_msg = "Địa chỉ không được để trống!"
            elif " " in username:
                err_msg = "Tên tài khoản không được chứa khoảng trắng!"
            elif not re.match("^[A-Za-z0-9]+$", username):
                err_msg = "Tên tài khoản không được chứa ký tự đặc biệt!"
            elif dao.check_username_exists(username):
                err_msg = "Tên đăng nhập này đã tồn tại! Vui lòng chọn tên khác."
            elif dao.check_phone_exists(dienThoai):
                err_msg = "Số điện thoại này đã tồn tại! Vui lòng chọn số điện thoại khác."
            elif not re.match(password_pattern, password):
                err_msg = ("Mật khẩu phải có ít nhất 8 ký tự. Gồm chữ hoa, chữ thường, số, ký tự đặc biệt.")
            elif not password.__eq__(confirm):
                err_msg = "Mật khẩu không khớp!"
            elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                err_msg = "Định dạng email không hợp lệ!"
            elif dao.check_email_exists(email):
                err_msg = "Email này đã được sử dụng!"
            elif dienThoai and not re.match(r"^0\d{9,10}$", dienThoai):
                err_msg = "Số điện thoại không hợp lệ!"
            elif ngaySinh and ngaySinhDate is None:
                err_msg = "Ngày sinh không hợp lệ!"
            else:
                path_file = None
                if avatar:
                    try:
                        res = cloudinary.uploader.upload(avatar)
                        path_file = res["secure_url"]
                    except Exception as e:
                        print("Lỗi upload avatar:", e)
                        err_msg = ("Không thể tải ảnh đại diện!")
                if not err_msg:
                    try:
                        dao.add_user(name=name, username=username, password=password, email=email, dienThoai=dienThoai,
                                     avatar=path_file, gioiTinh=gioiTinh, ngaySinh=ngaySinhDate, diaChi=diaChi)
                        return redirect('/login')

                    except Exception as e:
                        print("Lỗi đăng ký:", e)
                        db.session.rollback()
                        err_msg = "Hệ thống đang có lỗi! Vui lòng quay lại sau!"
        return render_template("register.html", err_msg=err_msg, current_date=current_date)

    @app.route('/logout')
    def user_logout():
        logout_user()
        return redirect('/')

    @app.route('/api/send-otp', methods=['POST'])
    def send_otp():
        data = request.json
        username = data.get('username')
        email = data.get('email')

        # 1. Kiểm tra thông tin khớp trong DB
        user = dao.get_user(username, email)

        if not user:
            return jsonify({
                "success": False,
                "message": "Thông tin không khớp! Kiểm tra lại Username hoặc Email"
            })

        try:
            # 2. Tạo mã OTP ngẫu nhiên 6 số
            otp_code = str(random.randint(100000, 999999))

            # 3. Lưu vào bộ nhớ tạm để kiểm tra sau này (dùng email làm key)
            otp_storage[email] = otp_code

            # Lấy đối tượng mail từ current_app
            mail = current_app.extensions.get('mail')

            if not mail:
                # Nếu vẫn không thấy, tự tạo mock object
                from flask_mail import Mail
                mail = Mail(current_app)

            # 4. Soạn thảo và gửi Email
            msg = Message(
                subject='[NYCosmetics] Mã xác thực OTP đặt lại mật khẩu',
                recipients=[email],
                body=f"Chào {user.name},\n\nMã OTP để đặt lại mật khẩu của bạn là: {otp_code}\n\nMã này sẽ hết hạn khi bạn đóng trình duyệt. Vui lòng không chia sẻ mã này cho ai."
            )
            mail.send(msg)

            return jsonify({"success": True, "message": "OTP đã được gửi! Bạn kiểm tra hòm thư nhé."})

        except Exception as e:
            print(f"Lỗi gửi mail: {str(e)}")
            return jsonify({"success": False, "message": "Lỗi hệ thống khi gửi mail. Thử lại sau nhé!"})

    # Api xác nhận OTP và đổi mật khẩu
    @app.route('/api/verify-reset', methods=['POST'])
    def verify_reset():
        data = request.get_json()
        email = data.get('email')
        otp_input = data.get('otp')
        new_password = data.get('new_password')
        password_pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"

        # 1. Kiểm tra OTP
        # Nếu email không có trong kho hoặc OTP sai
        if email not in otp_storage or otp_storage[email] != otp_input:
            return jsonify({'success': False, 'message': 'Mã OTP không đúng hoặc đã hết hạn!'})
        if not re.match(password_pattern, new_password):
            return jsonify({
                "success": False,
                "message": "Mật khẩu phải có ít nhất 8 ký tự, gồm chữ hoa, chữ thường, số và ký tự đặc biệt."
            })

        # 2. Gọi DAO cập nhật mật khẩu mới
        if dao.update_password(email, new_password):
            # 3. Xóa OTP sau khi dùng xong để bảo mật
            del otp_storage[email]
            return jsonify({'success': True, 'message': 'Đổi mật khẩu thành công! Hãy đăng nhập lại.'})
        else:
            return jsonify({'success': False, 'message': 'Lỗi hệ thống khi cập nhật mật khẩu.'})

    @app.route("/cart")
    @login_required
    def cart():
        cart = session.get("cart", {})

        total_quantity = sum(
            item["quantity"]
            for item in cart.values()
        )

        total_price = sum(
            item["price"] * item["quantity"]
            for item in cart.values()
        )

        return render_template(
            "customer/cart.html",
            cart=cart,
            total_quantity=total_quantity,
            total_price=total_price
        )

    @app.route("/api/cart", methods=["POST"])
    def add_to_cart():
        if not current_user.is_authenticated:
            return jsonify({
                "status": 401,
                "message": "Vui lòng đăng nhập để thêm sản phẩm vào giỏ hàng!"
            }), 401

        data = request.json

        maSanPham = data.get("maSanPham")
        tenSanPham = data.get("tenSanPham")
        giaBan = data.get("giaBan")
        hinhAnh = data.get("hinhAnh")
        maDanhMuc = data.get("maDanhMuc")

        if not maSanPham:
            return jsonify({
                "status": 400,
                "message": "Không tìm thấy sản phẩm!"
            }), 400

        cart = session.get("cart", {})

        if maSanPham in cart:
            cart[maSanPham]["quantity"] += 1
        else:
            cart[maSanPham] = {
                "id": maSanPham,
                "name": tenSanPham,
                "price": float(giaBan),
                "image": hinhAnh,
                "category_id": maDanhMuc,
                "quantity": 1
            }

        session["cart"] = cart
        session.modified = True

        total_quantity = sum(
            item["quantity"]
            for item in cart.values()
        )

        total_price = sum(
            item["price"] * item["quantity"]
            for item in cart.values()
        )

        dao.add_behavior(current_user.id, maSanPham,"THEM_GIO_HANG")

        return jsonify({
            "status": 200,
            "message": "Đã thêm sản phẩm vào giỏ hàng!",
            "total_quantity": total_quantity,
            "total_price": total_price
        })

    @app.route("/api/cart/<ma_san_pham>", methods=["DELETE"])
    def delete_cart(ma_san_pham):
        cart = session.get("cart", {})

        if ma_san_pham in cart:
            del cart[ma_san_pham]
            session["cart"] = cart

        return {"success": True}

    @app.route("/api/checkout", methods=["POST"])
    @login_required
    def checkout():
        data = request.get_json()
        name = data.get("name")
        phone = data.get("phone")
        address = data.get("address")
        payment_method = data.get("payment_method")
        cart = session.get("cart", {})

        if not cart:
            return jsonify({
                "status": 400,
                "message": "Giỏ hàng đang trống!"
            })

        if payment_method not in [
            "ShipCOD",
            "ThanhToanTaiCuaHang",
            "ChuyenKhoan"
        ]:
            return jsonify({
                "status": 400,
                "message": "Phương thức thanh toán không hợp lệ!"
            })

        try:
            ma_don_hang = dao.generate_order_code()
            tong_tien = 0

            for item in cart.values():
                tong_tien += (float(item["price"]) * int(item["quantity"]))

            # TẠO ĐƠN HÀNG
            don_hang = DonHang(
                maDonHang=ma_don_hang,
                maKhachHang=current_user.maKhachHang,
                ngayDat=datetime.now(),
                tongTien=tong_tien,
                trangThai="ChoXacNhan",
                diaChiGiao=address,
                phuongThucThanhToan=payment_method,
                trangThaiThanhToan="ChuaThanhToan"
            )
            db.session.add(don_hang)

            # CHI TIẾT ĐƠN HÀNG
            for item in cart.values():
                chi_tiet = ChiTietDonHang(
                    maDonHang=ma_don_hang,
                    maSanPham=item["id"],
                    soLuong=item["quantity"],
                    donGia=item["price"],
                    thanhTien=(
                            float(item["price"])
                            * int(item["quantity"])
                    )
                )
                db.session.add(chi_tiet)
            db.session.commit()

            # XÓA GIỎ HÀNG
            session.pop("cart", None)

            # TRẢ KẾT QUẢ
            if payment_method == "ChuyenKhoan":
                return jsonify({
                    "status": 200,
                    "message": "Đặt hàng thành công!",
                    "maDonHang": ma_don_hang,
                    "redirect": url_for(
                        "payment",
                        ma_don_hang=ma_don_hang
                    )
                })

            return jsonify({
                "status": 200,
                "message": "Đặt hàng thành công!",
                "maDonHang": ma_don_hang,
                "redirect": url_for("index")
            })

        except Exception as e:
            print("Lỗi hệ thống:", e)
            db.session.rollback()
            return jsonify({
                "status": 500,
                "message": "Không thể tạo đơn hàng!"
            })

    @app.route("/payment/<ma_don_hang>")
    @login_required
    def payment(ma_don_hang):
        don_hang = dao.get_order_by_id(ma_don_hang)

        if not don_hang:
            return redirect(url_for("index"))

        if don_hang.phuongThucThanhToan != "ChuyenKhoan":
            return redirect(url_for("index"))

        bank_id = app.config["BANK_ID"]
        bank_account = app.config["BANK_ACCOUNT"]
        bank_account_name = app.config["BANK_ACCOUNT_NAME"]

        noi_dung = f"Thanh toan don hang {don_hang.maDonHang} NYCosmetics"

        qr_url = (
            f"https://img.vietqr.io/image/"
            f"{bank_id}-{bank_account}-compact2.png"
            f"?amount={int(don_hang.tongTien)}"
            f"&addInfo={noi_dung}"
            f"&accountName={bank_account_name}"
        )

        return render_template(
            "customer/payment.html",
            don_hang=don_hang,
            qr_url=qr_url,
            noi_dung=noi_dung
        )

    @app.route(
        "/api/orders/<ma_don_hang>/cancel",
        methods=["POST"]
    )
    @login_required
    def cancel_order(ma_don_hang):

        order = DonHang.query.filter(
            DonHang.maDonHang == ma_don_hang,
            DonHang.maKhachHang == current_user.maKhachHang
        ).first()

        if not order:
            return {
                "success": False,
                "message": "Không tìm thấy đơn hàng!"
            }, 404

        if order.trangThai not in (
                "ChoXacNhan",
                "DaXacNhan"
        ):
            return {
                "success": False,
                "message": "Đơn hàng không thể hủy!"
            }, 400

        order.trangThai = "DaHuy"

        db.session.commit()

        return {
            "success": True,
            "message": "Đã hủy đơn hàng thành công!"
        }


    @app.route("/lich-su-mua-hang")
    @login_required
    def purchase_history():

        orders = DonHang.query.filter(
            DonHang.maKhachHang == current_user.maKhachHang
        ).order_by(
            DonHang.ngayDat.desc()
        ).all()

        return render_template(
            "customer/lich_su_mua_hang.html",
            orders=orders
        )

    @app.route("/chi-tiet-don-hang/<ma_don_hang>")
    @login_required
    def order_detail(ma_don_hang):

        order = DonHang.query.filter(
            DonHang.maDonHang == ma_don_hang,
            DonHang.maKhachHang == current_user.maKhachHang
        ).first()

        if not order:
            flash(
                "Không tìm thấy đơn hàng!",
                "danger"
            )
            return redirect(
                url_for("purchase_history")
            )

        return render_template(
            "customer/chi_tiet_don.html",
            order=order
        )
#=============================================
# ADMIN
    @app.route("/admin")
    @login_required
    def admin():
        if int(current_user.userRole) not in [1, 2]:
            return "Bạn không có quyền truy cập", 403

        # Thống kê tổng quan
        statistics = dao.get_dashboard_statistics()

        # Tính phần trăm tăng giảm
        revenue_growth = dao.calculate_growth(
            statistics["revenue_today"],
            statistics["revenue_yesterday"]
        )

        orders_growth = dao.calculate_growth(
            statistics["orders_today"],
            statistics["orders_yesterday"]
        )

        customers_growth = dao.calculate_growth(
            statistics["customers_today"],
            statistics["customers_yesterday"]
        )

        # Doanh thu 7 ngày
        revenue_7_days = dao.get_revenue_last_7_days()

        # Danh mục bán chạy
        category_statistics = dao.get_category_statistics()

        # Top sản phẩm
        top_products = dao.get_top_products()

        # Đơn hàng mới nhất
        recent_orders = DonHang.query.order_by(
            DonHang.ngayDat.desc()
        ).limit(5).all()

        return render_template(
            "admin/admin.html",
            statistics=statistics,
            revenue_growth=revenue_growth,
            orders_growth=orders_growth,
            customers_growth=customers_growth,
            revenue_7_days=revenue_7_days,
            category_statistics=category_statistics,
            top_products=top_products,
            recent_orders=recent_orders
        )

    @app.route("/admin/tai-khoan")
    @login_required
    def account_management():
        if current_user.userRole != UserRole.ADMIN:
            flash(
                "Bạn không có quyền truy cập!",
                "danger"
            )

            return redirect(
                url_for("admin")
            )

        page = request.args.get(
            "page",
            1,
            type=int
        )

        q = request.args.get(
            "q",
            ""
        ).strip()

        role = request.args.get(
            "role",
            ""
        ).strip()

        page_size = 5

        pagination = dao.load_accounts(
            q=q,
            role=role,
            page=page,
            page_size=page_size
        )

        users = pagination.items

        total_users = pagination.total

        total_pages = pagination.pages

        return render_template(
            "admin/quan_ly_tai_khoan.html",
            users=users,
            q=q,

            current_role=role,

            current_page=page,

            total_users=total_users,

            total_pages=total_pages
        )

    @app.route(
        "/admin/tai-khoan/them",
        methods=["GET", "POST"]
    )
    @login_required
    def them_tai_khoan():

        if current_user.userRole != UserRole.ADMIN:
            flash(
                "Bạn không có quyền thực hiện chức năng này!",
                "danger"
            )

            return redirect(
                url_for("account_management")
            )

        if request.method == "POST":

            name = request.form.get(
                "name",
                ""
            ).strip()

            username = request.form.get(
                "username",
                ""
            ).strip()

            password = request.form.get(
                "password",
                ""
            )

            email = request.form.get(
                "email",
                ""
            ).strip()

            dien_thoai = request.form.get(
                "dienThoai",
                ""
            ).strip()

            role = request.form.get(
                "role",
                ""
            ).strip()

            # =========================
            # KIỂM TRA DỮ LIỆU
            # =========================

            if not name:
                flash(
                    "Vui lòng nhập họ tên!",
                    "danger"
                )

                return redirect(
                    url_for("them_tai_khoan")
                )

            if not username:
                flash(
                    "Vui lòng nhập username!",
                    "danger"
                )

                return redirect(
                    url_for("them_tai_khoan")
                )

            if not password:
                flash(
                    "Vui lòng nhập mật khẩu!",
                    "danger"
                )

                return redirect(
                    url_for("them_tai_khoan")
                )

            if role not in [
                "admin",
                "nhanVien"
            ]:
                flash(
                    "Loại tài khoản không hợp lệ!",
                    "danger"
                )

                return redirect(
                    url_for("them_tai_khoan")
                )

            # =========================
            # KIỂM TRA TRÙNG
            # =========================

            if User.query.filter_by(
                    username=username
            ).first():
                flash(
                    "Username đã tồn tại!",
                    "danger"
                )

                return redirect(
                    url_for("them_tai_khoan")
                )

            if email:

                if User.query.filter_by(
                        email=email
                ).first():
                    flash(
                        "Email đã tồn tại!",
                        "danger"
                    )

                    return redirect(
                        url_for("them_tai_khoan")
                    )

            if dien_thoai:

                if User.query.filter_by(
                        dienThoai=dien_thoai
                ).first():
                    flash(
                        "Số điện thoại đã tồn tại!",
                        "danger"
                    )

                    return redirect(
                        url_for("them_tai_khoan")
                    )

            # =========================
            # MẬT KHẨU
            # =========================

            password_hash = generate_password_hash(
                password
            )

            try:

                # =========================
                # TẠO ADMIN
                # =========================

                if role == "admin":

                    user = Admin(

                        name=name,

                        username=username,

                        password=password_hash,

                        userRole=UserRole.ADMIN,

                        avatar=None,

                        email=email or None,

                        dienThoai=dien_thoai or None,

                        type="admin",

                        maAdmin=dao.generate_admin_code()

                    )


                # =========================
                # TẠO NHÂN VIÊN
                # =========================

                else:

                    user = NhanVien(

                        name=name,

                        username=username,

                        password=password_hash,

                        userRole=UserRole.NHAN_VIEN,

                        avatar=None,

                        email=email or None,

                        dienThoai=dien_thoai or None,

                        type="nhanVien",

                        maNhanVien=dao.generate_employee_code(),

                        trangThai=True

                    )

                db.session.add(user)

                db.session.commit()

                flash(
                    "Thêm tài khoản thành công!",
                    "success"
                )

                return redirect(
                    url_for(
                        "account_management"
                    )
                )


            except Exception as e:

                db.session.rollback()

                print(
                    "Lỗi thêm tài khoản:",
                    e
                )

                flash(
                    "Không thể thêm tài khoản!",
                    "danger"
                )

                return redirect(
                    url_for("them_tai_khoan")
                )

        return render_template(
            "admin/them_tai_khoan.html"
        )

    @app.route(
        "/admin/tai-khoan/sua/<int:user_id>",
        methods=["GET", "POST"]
    )
    @login_required
    def sua_tai_khoan(user_id):

        if current_user.userRole != UserRole.ADMIN:
            flash(
                "Bạn không có quyền thực hiện chức năng này!",
                "danger"
            )

            return redirect(
                url_for("account_management")
            )

        user = dao.get_account_by_id(
            user_id
        )

        if not user:
            flash(
                "Không tìm thấy tài khoản!",
                "danger"
            )

            return redirect(
                url_for("account_management")
            )

        if request.method == "POST":

            name = request.form.get(
                "name",
                ""
            ).strip()

            username = request.form.get(
                "username",
                ""
            ).strip()

            email = request.form.get(
                "email",
                ""
            ).strip()

            dien_thoai = request.form.get(
                "dienThoai",
                ""
            ).strip()

            password = request.form.get(
                "password",
                ""
            )

            # =========================
            # KIỂM TRA
            # =========================

            if not name:
                flash(
                    "Vui lòng nhập họ tên!",
                    "danger"
                )

                return redirect(
                    url_for(
                        "sua_tai_khoan",
                        user_id=user_id
                    )
                )

            if not username:
                flash(
                    "Vui lòng nhập username!",
                    "danger"
                )

                return redirect(
                    url_for(
                        "sua_tai_khoan",
                        user_id=user_id
                    )
                )

            # =========================
            # KIỂM TRA USERNAME TRÙNG
            # =========================

            username_exists = User.query.filter(
                User.username == username,
                User.id != user_id
            ).first()

            if username_exists:
                flash(
                    "Username đã được sử dụng!",
                    "danger"
                )

                return redirect(
                    url_for(
                        "sua_tai_khoan",
                        user_id=user_id
                    )
                )

            # =========================
            # KIỂM TRA EMAIL
            # =========================

            if email:

                email_exists = User.query.filter(
                    User.email == email,
                    User.id != user_id
                ).first()

                if email_exists:
                    flash(
                        "Email đã được sử dụng!",
                        "danger"
                    )

                    return redirect(
                        url_for(
                            "sua_tai_khoan",
                            user_id=user_id
                        )
                    )

            # =========================
            # KIỂM TRA SĐT
            # =========================

            if dien_thoai:

                phone_exists = User.query.filter(
                    User.dienThoai == dien_thoai,
                    User.id != user_id
                ).first()

                if phone_exists:
                    flash(
                        "Số điện thoại đã được sử dụng!",
                        "danger"
                    )

                    return redirect(
                        url_for(
                            "sua_tai_khoan",
                            user_id=user_id
                        )
                    )

            try:

                user.name = name

                user.username = username

                user.email = (
                    email
                    if email
                    else None
                )

                user.dienThoai = (
                    dien_thoai
                    if dien_thoai
                    else None
                )

                # =========================
                # ĐỔI MẬT KHẨU
                # =========================

                if password:
                    user.password = (
                        generate_password_hash(
                            password
                        )
                    )

                if user.type == "nhanVien":
                    trang_thai = request.form.get(
                        "trangThai"
                    )

                    user.trangThai = (
                            trang_thai == "1"
                    )

                db.session.commit()

                flash(
                    "Cập nhật tài khoản thành công!",
                    "success"
                )

                return redirect(
                    url_for(
                        "account_management"
                    )
                )


            except Exception as e:

                db.session.rollback()

                print(
                    "Lỗi sửa tài khoản:",
                    e
                )

                flash(
                    "Không thể cập nhật tài khoản!",
                    "danger"
                )

        return render_template(
            "admin/sua_tai_khoan.html",
            user=user
        )
# TẠO ĐƠN HÀNG
    @app.route("/admin/gio-hang")
    @login_required
    def staff_cart():
        cart = session.get(
            "staff_cart",
            {}
        )

        total_quantity = sum(
            int(item["quantity"])
            for item in cart.values()
        )

        total_price = sum(
            float(item["price"])
            * int(item["quantity"])
            for item in cart.values()
        )

        return render_template(
            "admin/gio_hang_nhan_vien.html",

            cart=cart,

            total_quantity=total_quantity,

            total_price=total_price
        )

    @app.route("/admin/tao-don-hang")
    @login_required
    def create_staff_order():
        page = request.args.get("page", 1, type=int)
        cate_id = request.args.get('category_id')
        brand_id = request.args.get('brand_id')
        kw = request.args.get('kw')

        categories = dao.load_categories()
        brands = dao.load_brands()

        page_size = 8

        products = dao.load_products(
            kw=kw,
            cate_id=cate_id,
            brand_id=brand_id,
            page=page,
            page_size=page_size
        )

        total_products = dao.count_product(
            cate_id=cate_id,
            brand_id=brand_id,
            kw=kw
        )

        total_pages = math.ceil(total_products / page_size)

        staff_cart = session.get('staff_cart', {})

        total_quantity = sum(
            int(item['quantity'])
            for item in staff_cart.values()
        )

        return render_template(
            'admin/tao_don_hang.html',
            categories=categories,
            brands=brands,
            products=products,
            pages=total_pages,
            current_page=page,
            total_quantity=total_quantity
        )

    @app.route("/admin/chi-tiet-san-pham/<ma_san_pham>")
    @login_required
    def admin_product_detail(ma_san_pham):
        product = dao.get_product_by_id(ma_san_pham)

        if not product:
            flash("Không tìm thấy sản phẩm!", "danger")
            return redirect(url_for("create_staff_order"))

        recommended_products = get_recommendations(
            ma_san_pham=product.maSanPham,
            user_id=current_user.id if current_user.is_authenticated else None,
            limit=4
        )

        # Ghi nhận hành vi XEM
        dao.add_behavior(current_user.id, product.maSanPham, "XEM")

        return render_template(
            "admin/product_detail_admin.html",
            product=product,
            recommended_products=recommended_products
        )

    @app.route("/api/admin/cart", methods=["POST"])
    @login_required
    def add_staff_cart():

        data = request.get_json()

        product_id = data.get("id")

        if not product_id:
            return jsonify({
                "status": 400,
                "message": "Không xác định được sản phẩm!"
            }), 400

        product = SanPham.query.get(product_id)

        if not product:
            return jsonify({
                "status": 404,
                "message": "Không tìm thấy sản phẩm!"
            }), 404

        if product.soLuong <= 0:
            return jsonify({
                "status": 400,
                "message": "Sản phẩm đã hết hàng!"
            }), 400

        cart = session.get("staff_cart", {})

        product_id = str(product_id)

        if product_id in cart:

            # Không cho thêm vượt quá tồn kho
            if cart[product_id]["quantity"] >= product.soLuong:
                return jsonify({
                    "status": 400,
                    "message": "Số lượng sản phẩm trong đơn đã đạt tồn kho!"
                }), 400

            cart[product_id]["quantity"] += 1

        else:

            cart[product_id] = {
                "id": product_id,
                "name": product.tenSanPham,
                "price": float(product.giaBan),
                "image": product.hinhAnh,
                "category_id": product.maDanhMuc,
                "quantity": 1
            }

        session["staff_cart"] = cart
        session.modified = True

        total_quantity = sum(
            item["quantity"]
            for item in cart.values()
        )
        # Ghi nhận hành vi THEM_GIO_HANG
        dao.add_behavior(current_user.id, product.maSanPham,"THEM_GIO_HANG")

        return jsonify({
            "status": 200,
            "message": "Đã thêm sản phẩm vào đơn!",
            "total_quantity": total_quantity
        })

    @app.route("/admin/api/cart/update", methods=["POST"])
    @login_required
    def update_staff_cart():

        data = request.get_json()

        product_id = str(data.get("id"))
        quantity = int(data.get("quantity", 1))

        staff_cart = session.get("staff_cart", {})

        if product_id not in staff_cart:
            return jsonify({
                "success": False,
                "message": "Sản phẩm không tồn tại trong giỏ hàng!"
            }), 404

        if quantity < 1:
            return jsonify({
                "success": False,
                "message": "Số lượng không hợp lệ!"
            }), 400

        staff_cart[product_id]["quantity"] = quantity

        session["staff_cart"] = staff_cart
        session.modified = True

        return jsonify({
            "success": True
        })

    @app.route("/admin/api/cart/delete", methods=["POST"])
    @login_required
    def delete_staff_cart():

        data = request.get_json()

        product_id = str(data.get("id"))

        staff_cart = session.get("staff_cart", {})

        if product_id in staff_cart:
            del staff_cart[product_id]

        session["staff_cart"] = staff_cart
        session.modified = True

        return jsonify({
            "success": True
        })

    @app.route("/api/admin/find-customer")
    @login_required
    def find_staff_customer():
        phone = request.args.get("phone")

        if not phone:
            return jsonify({

                "status": 400,

                "message":
                    "Vui lòng nhập số điện thoại!"

            })

        customer = dao.get_customer_by_phone(
            phone
        )

        if not customer:
            return jsonify({

                "status": 404,

                "message":
                    "Không tìm thấy khách hàng!"

            })

        session[
            "staff_customer_id"
        ] = customer.maKhachHang

        session.modified = True

        return jsonify({

            "status": 200,

            "customer": {

                "maKhachHang":
                    customer.maKhachHang,

                "name":
                    customer.name,

                "dienThoai":
                    customer.dienThoai

            }

        })

    from urllib.parse import quote

    @app.route("/admin/thanh-toan-qr")
    @login_required
    def staff_payment_qr():
        cart = session.get("staff_cart", {})

        if not cart:
            return redirect(url_for("create_staff_order"))

        total_price = sum(
            float(item["price"])
            * int(item["quantity"])
            for item in cart.values()
        )

        bank_id = app.config["BANK_ID"]
        bank_account = app.config["BANK_ACCOUNT"]
        bank_account_name = app.config["BANK_ACCOUNT_NAME"]

        noi_dung = "Thanh toan don hang NYCosmetics"

        qr_url = (
            f"https://img.vietqr.io/image/"
            f"{bank_id}-{bank_account}-compact2.png"
            f"?amount={int(total_price)}"
            f"&addInfo={quote(noi_dung)}"
            f"&accountName={quote(bank_account_name)}"
        )

        return render_template(
            "admin/qr_thanh_toan.html",
            total_price=total_price,
            qr_url=qr_url,
            noi_dung=noi_dung
        )

    @app.route("/admin/xuat-hoa-don")
    @login_required
    def export_staff_invoice():
        if current_user.userRole not in (UserRole.NHAN_VIEN, UserRole.ADMIN):
            flash(
                "Bạn không có quyền thực hiện chức năng này!",
                "danger"
            )
            return redirect(url_for("admin"))

        # LẤY GIỎ HÀNG NHÂN VIÊN
        cart = session.get("staff_cart", {})

        if not cart:
            flash(
                "Giỏ hàng đang trống!",
                "warning"
            )
            return redirect(
                url_for("create_staff_order")
            )

        # LẤY KHÁCH HÀNG THEO SDT

        ma_khach_hang = session.get(
            "staff_customer_id"
        )

        if not ma_khach_hang:
            flash(
                "Vui lòng tìm và chọn khách hàng trước!",
                "warning"
            )

            return redirect(
                url_for("staff_cart")
            )

        # LẤY KHÁCH HÀNG
        customer = dao.get_customer_by_code(
            ma_khach_hang
        )

        if not customer:
            flash(
                "Không tìm thấy khách hàng!",
                "danger"
            )

            return redirect(
                url_for("staff_cart")
            )

        try:
            # TẠO MÃ ĐƠN HÀNG
            ma_don_hang = (dao.generate_order_code())

            # TÍNH TỔNG TIỀN
            tong_tien = 0
            for item in cart.values():
                tong_tien += (
                        float(item["price"])
                        *
                        int(item["quantity"])
                )

            # KIỂM TRA TỒN KHO
            for item in cart.values():
                product = dao.get_product_by_id(item["id"])

                if not product:
                    raise Exception(
                        f"Không tìm thấy sản phẩm "
                        f"{item['id']}!"
                    )

                so_luong = int(item["quantity"])

                if product.soLuong < so_luong:
                    raise Exception(
                        f"Sản phẩm "
                        f"{product.tenSanPham} "
                        f"không đủ tồn kho!"
                    )

            # THỜI GIAN TẠO HÓA ĐƠN
            ngay_tao_hoa_don = datetime.now()

            # TẠO ĐƠN HÀNG
            don_hang = DonHang(
                maDonHang=ma_don_hang,
                maKhachHang=customer.maKhachHang,
                ngayDat=ngay_tao_hoa_don,
                tongTien=tong_tien,
                trangThai="HoanThanh",
                diaChiGiao=customer.diaChi,
                phuongThucThanhToan="ThanhToanTaiCuaHang",
                trangThaiThanhToan="DaThanhToan"
            )

            db.session.add(don_hang)

            # CHI TIẾT ĐƠN HÀNG
            for item in cart.values():
                so_luong = int(item["quantity"])
                don_gia = float(item["price"])
                thanh_tien = (don_gia * so_luong)
                chi_tiet = ChiTietDonHang(
                    maDonHang=ma_don_hang,
                    maSanPham=item["id"],
                    soLuong=so_luong,
                    donGia=don_gia,
                    thanhTien=thanh_tien
                )

                db.session.add(chi_tiet)

            # TRỪ TỒN KHO
            for item in cart.values():
                product = dao.get_product_by_id(item["id"])
                so_luong = int(item["quantity"])
                product.soLuong -= so_luong

            # LƯU DATABASE
            db.session.commit()

            # XÓA SESSION
            session.pop("staff_cart", None)
            session.pop("staff_customer_id", None)
            session.modified = True

            # HIỂN THỊ HÓA ĐƠN
            return render_template(
                "admin/invoice.html",
                don_hang=don_hang,
                customer=customer,
                employee=current_user,
                cart=cart,
                total_price=tong_tien,
                ngay_tao_hoa_don=ngay_tao_hoa_don
            )
        except Exception as e:
            db.session.rollback()
            print("Lỗi xuất hóa đơn:", e)

            flash(
                "Không thể xuất hóa đơn!",
                "danger"
            )

            return redirect(url_for("staff_cart"))

    #   QL ĐƠN HÀNG
    @app.route("/admin/don-hang")
    @login_required
    def order_management():
        if current_user.userRole not in (
                UserRole.ADMIN,
                UserRole.NHAN_VIEN
        ):
            flash(
                "Bạn không có quyền truy cập!",
                "danger"
            )
            return redirect(
                url_for("admin")
            )

        page = request.args.get(
            "page",
            1,
            type=int
        )

        status = request.args.get(
            "status",
            "TatCa"
        )

        q = request.args.get(
            "q",
            ""
        ).strip()

        page_size = 5

        orders = dao.load_orders(
            status=status,
            page=page,
            page_size=page_size,
            q=q
        )

        for order in orders:
            order.allowed_statuses = (
                get_allowed_order_statuses(
                    order.trangThai
                )
            )

        total_orders = dao.count_orders(
            status=status,
            q=q
        )

        total_pages = math.ceil(
            total_orders / page_size
        )

        return render_template(
            "admin/quan_ly_don_hang.html",
            orders=orders,
            current_page=page,
            total_pages=total_pages,
            total_orders=total_orders,
            current_status=status,
            q=q
        )

    @app.route("/api/admin/pending-orders")
    @login_required
    def pending_orders():
        count = dao.count_pending_orders()

        return {
            "count": count
        }

    @app.route("/admin/don-hang/<ma_don_hang>/cap-nhat", methods=["POST"])
    @login_required
    def update_order_status(ma_don_hang):
        if current_user.userRole not in (
            UserRole.NHAN_VIEN,
            UserRole.ADMIN
        ):
            flash(
                "Bạn không có quyền thực hiện chức năng này!",
                "danger"
            )
            return redirect(
                url_for("order_management")
            )

        don_hang = DonHang.query.filter(
            DonHang.maDonHang == ma_don_hang
        ).first()

        if not don_hang:
            flash(
                "Không tìm thấy đơn hàng!",
                "danger"
            )
            return redirect(
                url_for("order_management")
            )

        trang_thai_moi = request.form.get(
            "trangThai"
        )

        thanh_toan_moi = request.form.get(
            "trangThaiThanhToan"
        )

        if trang_thai_moi == "DaGiao":
            thanh_toan_moi = "DaThanhToan"

        # =====================================
        # TRẠNG THÁI HIỆN TẠI
        # =====================================

        trang_thai_cu = don_hang.trangThai

        # =====================================
        # QUY TẮC CHUYỂN TRẠNG THÁI
        # =====================================

        quy_tac_trang_thai = {

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

        trang_thai_duoc_phep = quy_tac_trang_thai.get(trang_thai_cu, [])

        if trang_thai_moi not in trang_thai_duoc_phep:

            flash(
                "Không thể chuyển trạng thái "
                "đơn hàng theo quy trình!",
                "danger"
            )

            return redirect(
                url_for("order_management")
            )

        # =====================================
        # KIỂM TRA THANH TOÁN
        # =====================================

        if thanh_toan_moi not in [
            "ChuaThanhToan",
            "DaThanhToan"
        ]:

            flash(
                "Trạng thái thanh toán không hợp lệ!",
                "danger"
            )

            return redirect(
                url_for("order_management")
            )

        # Đã giao / đã hủy thì không sửa thanh toán
        if (
            trang_thai_cu in [
                # "DaGiao",
                "DaHuy"
            ]
            and thanh_toan_moi
            != don_hang.trangThaiThanhToan
        ):

            flash(
                "Không thể thay đổi trạng thái thanh toán của đơn hàng này!",
                "danger"
            )

            return redirect(
                url_for("order_management")
            )

        try:

            # =====================================
            # HỦY ĐƠN → HOÀN TỒN KHO
            # =====================================

            if (
                trang_thai_moi == "DaHuy"
                and trang_thai_cu != "DaHuy"
            ):

                restore_order_stock(don_hang)

            # =====================================
            # CẬP NHẬT TRẠNG THÁI
            # =====================================

            don_hang.trangThai = trang_thai_moi

            # =====================================
            # CẬP NHẬT THANH TOÁN
            # =====================================

            don_hang.trangThaiThanhToan = (
                thanh_toan_moi
            )

            if thanh_toan_moi == "DaThanhToan":

                if not don_hang.ngayThanhToan:
                    don_hang.ngayThanhToan = (
                        datetime.now()
                    )

            else:

                don_hang.ngayThanhToan = None

            db.session.commit()

            flash(
                "Cập nhật đơn hàng thành công!",
                "success"
            )

        except Exception as e:

            db.session.rollback()

            print(
                "Lỗi cập nhật đơn hàng:",
                e
            )

            flash(
                "Không thể cập nhật đơn hàng!",
                "danger"
            )

        return redirect(
            url_for("order_management")
        )
    # Xem chi tiết DH
    @app.route("/admin/don-hang/<ma_don_hang>", methods=["GET"])
    @login_required
    def admin_order_detail(ma_don_hang):
        if current_user.userRole not in (
                UserRole.NHAN_VIEN,
                UserRole.ADMIN
        ):
            flash(
                "Bạn không có quyền xem đơn hàng!",
                "danger"
            )
            return redirect(
                url_for("order_management")
            )

        don_hang = DonHang.query.filter(
            DonHang.maDonHang == ma_don_hang
        ).first()

        if not don_hang:
            flash(
                "Không tìm thấy đơn hàng!",
                "danger"
            )
            return redirect(
                url_for("order_management")
            )

        chi_tiet = ChiTietDonHang.query.filter(
            ChiTietDonHang.maDonHang == ma_don_hang
        ).all()

        return render_template(
            "admin/chi_tiet_don_hang.html",
            don_hang=don_hang,
            chi_tiet=chi_tiet
        )
# QUẢN LÝ SẢN PHẨM
    @app.route("/admin/san-pham")
    @login_required
    def product_management():
        if current_user.userRole not in (
            UserRole.ADMIN,
            UserRole.NHAN_VIEN
        ):
            flash(
                "Bạn không có quyền truy cập!",
                "danger"
            )
            return redirect(url_for("admin"))

        page = request.args.get(
            "page",
            1,
            type=int
        )

        cate_id = request.args.get(
            "category_id"
        )

        brand_id = request.args.get(
            "brand_id"
        )

        kw = request.args.get("kw", "").strip()

        stock_status = request.args.get("stock_status", "TatCa")

        if stock_status not in ["TatCa", "DuoiTonToiThieu"]:
            stock_status = "TatCa"

        categories = dao.load_categories()
        brands = dao.load_brands()

        products = dao.load_products(
            kw=kw,
            cate_id=cate_id,
            brand_id=brand_id,
            page=page,
            page_size=8,
            stock_status=stock_status
        )

        total_products = dao.count_product(
            cate_id=cate_id,
            brand_id=brand_id,
            kw=kw,
            stock_status=stock_status
        )

        page_size = 8

        total_pages = math.ceil(
            total_products / page_size
        )

        return render_template(
            "admin/quan_ly_san_pham.html",
            products=products,
            categories=categories,
            brands=brands,
            total_pages=total_pages,
            total_products=total_products,
            current_page=page,
            current_category=cate_id,
            current_brand=brand_id,
            kw=kw,
            stock_status=stock_status
        )

    @app.context_processor
    def low_stock_product():

        low_stock_count = SanPham.query.filter(
            SanPham.soLuong <= SanPham.tonToiThieu
        ).count()

        return {"low_stock_count": low_stock_count}

    @app.route("/admin/san-pham/them",methods=["GET", "POST"])
    @login_required
    def add_product():

        if current_user.userRole not in (
                UserRole.ADMIN,
                UserRole.NHAN_VIEN
        ):
            flash(
                "Bạn không có quyền thực hiện chức năng này!",
                "danger"
            )
            return redirect(
                url_for("product_management")
            )

        categories = dao.load_categories()
        brands = dao.load_brands()

        if request.method == "POST":

            ten_san_pham = request.form.get(
                "tenSanPham",
                ""
            ).strip()

            ma_danh_muc = request.form.get(
                "maDanhMuc"
            )

            ma_thuong_hieu = request.form.get(
                "maThuongHieu"
            )

            gia_ban = request.form.get(
                "giaBan"
            )

            gia_nhap = request.form.get(
                "giaNhap"
            )

            so_luong = request.form.get(
                "soLuong",
                0
            )

            ton_toi_thieu = request.form.get(
                "tonToiThieu",
                0
            )

            mo_ta = request.form.get(
                "moTa"
            )

            thanh_phan = request.form.get(
                "thanhPhan"
            )

            cong_dung = request.form.get(
                "congDung"
            )

            # FILE ẢNH
            image_file = request.files.get(
                "hinhAnh"
            )

            if not ten_san_pham:
                flash(
                    "Vui lòng nhập tên sản phẩm!",
                    "danger"
                )

                return render_template(
                    "admin/them_san_pham.html",
                    categories=categories,
                    brands=brands
                )

            try:

                # Sinh mã sản phẩm
                ma_san_pham = dao.generate_product_code()

                # Upload ảnh lên Cloudinary
                image_url = None

                if image_file and image_file.filename:
                    image_url = upload_product_image(
                        image_file,
                        ma_san_pham
                    )

                product = SanPham(
                    maSanPham=ma_san_pham,
                    tenSanPham=ten_san_pham,
                    maDanhMuc=ma_danh_muc,
                    maThuongHieu=ma_thuong_hieu,
                    giaBan=float(gia_ban),
                    giaNhap=float(gia_nhap),
                    soLuong=int(so_luong),
                    hinhAnh=image_url,
                    moTa=mo_ta,
                    thanhPhan=thanh_phan,
                    congDung=cong_dung,
                    trangThai=True,
                    tonToiThieu=int(ton_toi_thieu)
                )

                db.session.add(product)

                db.session.commit()

                flash(
                    "Thêm sản phẩm thành công!",
                    "success"
                )

                return redirect(
                    url_for("product_management")
                )

            except Exception as e:

                db.session.rollback()

                print(
                    "Lỗi thêm sản phẩm:",
                    e
                )

                flash(
                    f"Không thể thêm sản phẩm: {e}",
                    "danger"
                )

        return render_template(
            "admin/them_san_pham.html",
            categories=categories,
            brands=brands
        )

    @app.route(
        "/admin/san-pham/sua/<ma_san_pham>",
        methods=["GET", "POST"]
    )
    @login_required
    def edit_product(ma_san_pham):

        if current_user.userRole not in (
                UserRole.ADMIN,
                UserRole.NHAN_VIEN
        ):
            flash(
                "Bạn không có quyền thực hiện chức năng này!",
                "danger"
            )
            return redirect(
                url_for("product_management")
            )

        product = dao.get_product_by_id(
            ma_san_pham
        )

        if not product:
            flash(
                "Không tìm thấy sản phẩm!",
                "danger"
            )
            return redirect(
                url_for("product_management")
            )

        categories = dao.load_categories()
        brands = dao.load_brands()

        if request.method == "POST":

            try:

                product.tenSanPham = request.form.get(
                    "tenSanPham"
                )

                product.maDanhMuc = request.form.get(
                    "maDanhMuc"
                )

                product.maThuongHieu = request.form.get(
                    "maThuongHieu"
                )

                product.giaBan = float(
                    request.form.get("giaBan")
                )

                product.giaNhap = float(
                    request.form.get("giaNhap")
                )

                product.soLuong = int(
                    request.form.get("soLuong")
                )

                product.tonToiThieu = int(
                    request.form.get("tonToiThieu")
                )

                product.moTa = request.form.get(
                    "moTa"
                )

                product.thanhPhan = request.form.get(
                    "thanhPhan"
                )

                product.congDung = request.form.get(
                    "congDung"
                )

                product.trangThai = (
                        request.form.get(
                            "trangThai"
                        ) == "1"
                )

                # ==========================
                # UPLOAD ẢNH MỚI
                # ==========================

                image_file = request.files.get(
                    "hinhAnh"
                )

                if image_file and image_file.filename:
                    image_url = upload_product_image(
                        image_file,
                        product.maSanPham
                    )

                    product.hinhAnh = image_url

                db.session.commit()

                flash(
                    "Cập nhật sản phẩm thành công!",
                    "success"
                )

                return redirect(
                    url_for("product_management")
                )

            except Exception as e:

                db.session.rollback()

                print(
                    "Lỗi cập nhật sản phẩm:",
                    e
                )

                flash(
                    f"Không thể cập nhật sản phẩm: {e}",
                    "danger"
                )

        return render_template(
            "admin/sua_san_pham.html",
            product=product,
            categories=categories,
            brands=brands
        )

    @app.route(
        "/admin/san-pham/xoa/<ma_san_pham>",
        methods=["POST"]
    )
    @login_required
    def delete_product(ma_san_pham):

        if current_user.userRole not in (
                UserRole.ADMIN,
                UserRole.NHAN_VIEN
        ):
            flash(
                "Bạn không có quyền thực hiện chức năng này!",
                "danger"
            )
            return redirect(
                url_for("product_management")
            )

        product = dao.get_product_by_id(
            ma_san_pham
        )

        if not product:
            flash(
                "Không tìm thấy sản phẩm!",
                "danger"
            )
            return redirect(
                url_for("product_management")
            )

        try:
            product.trangThai = False

            db.session.commit()

            flash(
                "Đã ngừng bán sản phẩm!",
                "success"
            )

        except Exception as e:
            db.session.rollback()

            print(
                "Lỗi xóa sản phẩm:",
                e
            )

            flash(
                "Không thể xóa sản phẩm!",
                "danger"
            )

        return redirect(
            url_for("product_management")
        )

@login.user_loader
def get_user(user_id):
    return dao.get_user_by_userid(int(user_id))


if __name__ == "__main__":
    register_routes(app=app)

    app.run(debug=True)
