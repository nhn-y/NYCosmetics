import pandas as pd
from nycosmetics.models import HanhVi, SanPham
from nycosmetics import app

# 1. LẤY DỮ LIỆU HÀNH VI XEM + THÊM GIỎ HÀNG

def load_behavior_dataframe():

    hanh_vis = HanhVi.query.filter(
        HanhVi.loaiHanhVi.in_([
            "XEM",
            "THEM_GIO_HANG"
        ])
    ).order_by(
        HanhVi.thoiGian.asc()
    ).all()

    data = []

    for hv in hanh_vis:
        data.append({
            "maHanhVi": hv.maHanhVi,
            "userId": hv.userId,
            "maSanPham": hv.maSanPham,
            "loaiHanhVi": hv.loaiHanhVi,
            "thoiGian": hv.thoiGian
        })

    return pd.DataFrame(data)


# =========================================================
# 2. LẤY HÀNH VI CỦA MỘT USER
# =========================================================

def get_user_behavior_dataframe(user_id):

    df = load_behavior_dataframe()

    if df.empty:
        return pd.DataFrame()

    df = df[
        df["userId"] == user_id
    ]

    return df


# =========================================================
# 3. TÍNH ĐIỂM QUAN TÂM SẢN PHẨM
# =========================================================

def calculate_product_interest(user_id):

    df = get_user_behavior_dataframe(user_id)

    if df.empty:
        return pd.DataFrame()

    # Trọng số hành vi
    weights = {
        "XEM": 1,
        "THEM_GIO_HANG": 3
    }

    df["diem"] = df["loaiHanhVi"].map(weights)

    result = (
        df.groupby("maSanPham")
        .agg(
            soLanXem=(
                "loaiHanhVi",
                lambda x: (x == "XEM").sum()
            ),

            soLanThemGio=(
                "loaiHanhVi",
                lambda x: (x == "THEM_GIO_HANG").sum()
            ),

            diemQuanTam=(
                "diem",
                "sum"
            )
        )
        .reset_index()
    )

    result = result.sort_values(
        "diemQuanTam",
        ascending=False
    )

    return result


# =========================================================
# 4. LẤY DANH SÁCH SẢN PHẨM USER QUAN TÂM
# =========================================================

def get_interested_products(user_id, limit=4):

    df = calculate_product_interest(user_id)

    if df.empty:
        return []

    product_ids = df[
        "maSanPham"
    ].head(limit).tolist()

    products = SanPham.query.filter(
        SanPham.maSanPham.in_(product_ids),
        SanPham.trangThai == True
    ).all()

    product_map = {
        product.maSanPham: product
        for product in products
    }

    result = []

    for product_id in product_ids:

        if product_id in product_map:
            result.append(
                product_map[product_id]
            )

    return result

if __name__ == "__main__":
    with app.app_context():

        df = load_behavior_dataframe()

        # print("KIỂM TRA DỮ LIỆU HÀNH VI")
        #
        # if df.empty:
        #     print("Không có dữ liệu hành vi.")
        #
        # else:
        #     print("Tổng số hành vi:", len(df))
        #     print("Số lượng theo loại:")
        #     print(df["loaiHanhVi"].value_counts())
        #     print("5 dòng đầu:")
        #     print(df.head())

        user_id = 3

        result = calculate_product_interest(user_id)

        print("ĐIỂM QUAN TÂM CỦA USER")
        print(result)

