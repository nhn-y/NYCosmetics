# NYCosmetics

Hệ thống bán mỹ phẩm trực tuyến có chức năng gợi ý sản phẩm.

## Giới thiệu

NYCosmetics là hệ thống bán mỹ phẩm trực tuyến được xây dựng bằng Flask
và MySQL. Hệ thống hỗ trợ khách hàng tìm kiếm, xem thông tin, thêm sản phẩm
vào giỏ hàng, đặt hàng và theo dõi lịch sử mua hàng.

Hệ thống sử dụng kỹ thuật khai phá dữ liệu để gợi ý các sản phẩm thường
được mua cùng nhau dựa trên dữ liệu giao dịch.

## Chức năng chính

### Khách hàng

- Đăng ký và đăng nhập
- Xem danh sách sản phẩm
- Tìm kiếm sản phẩm
- Lọc sản phẩm theo danh mục và thương hiệu
- Xem chi tiết sản phẩm
- Thêm sản phẩm vào giỏ hàng
- Đặt hàng
- Theo dõi lịch sử mua hàng
- Xem sản phẩm được gợi ý

### Nhân viên / Quản trị viên

- Quản lý sản phẩm
- Quản lý đơn hàng
- Quản lý tài khoản
- Tạo đơn hàng
- Theo dõi số lượng tồn kho
- Xem báo cáo

### Khai phá dữ liệu

- Phân tích dữ liệu giao dịch
- Market Basket Analysis
- Thuật toán Apriori
- Sinh luật kết hợp
- Gợi ý sản phẩm thường được mua cùng

## Công nghệ sử dụng

- Python 3.11
- Flask
- MySQL
- SQLAlchemy
- pandas
- scikit-learn
- mlxtend
- HTML/CSS/JavaScript
- Bootstrap

## Hướng dẫn cài đặt
Bước 1: Sao chép mã nguồn dự án về máy tính. 
Trong MySQL Workbench:
Bước 2: Tạo cơ sở dữ liệu cho hệ thống bằng lệnh:
		CREATE DATABASE nycosmeticsdb 
Bước 3: Import file SQL 
		File → Open SQL Script → Chọn file nycosmeticsdb.sql → Execute 
Trong Pycharm: 
Bước 4: Mở Command Prompt. Tạo môi trường ảo bằng lệnh:
    python -m venv .venv
Bước 5: Cài đặt các thư viện bằng lệnh:
    pip install -r requirements.txt 
Bước 6: Chạy hệ thống bằng cách run file index.py hoặc dùng lệnh:
	python -m nycosmetics.index
