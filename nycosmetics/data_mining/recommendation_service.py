from nycosmetics.models import SanPham
from nycosmetics.data_mining.market_basket import get_recommended_product_ids
from nycosmetics.data_mining.behavior_analysis import calculate_product_interest

# 1. LẤY SẢN PHẨM GỢI Ý TỪ APRIORI
def get_apriori_recommendations(
    ma_san_pham,
    limit=4
):

    product_ids = get_recommended_product_ids(
        ma_san_pham,
        limit=limit
    )

    if not product_ids:
        return []

    products = SanPham.query.filter(
        SanPham.maSanPham.in_(product_ids),
        SanPham.trangThai == True
    ).all()

    product_map = {
        product.maSanPham: product
        for product in products
    }

    recommendations = []

    for product_id in product_ids:

        product = product_map.get(
            product_id
        )

        if product:
            recommendations.append(product)

    return recommendations

# 2. LẤY SẢN PHẨM KHÁCH HÀNG QUAN TÂM

def get_behavior_recommendations(
    user_id,
    limit=4
):

    if not user_id:
        return []

    df = calculate_product_interest(
        user_id
    )

    if df.empty:
        return []

    product_ids = (
        df["maSanPham"]
        .head(limit)
        .tolist()
    )

    products = SanPham.query.filter(
        SanPham.maSanPham.in_(product_ids),
        SanPham.trangThai == True
    ).all()

    product_map = {
        product.maSanPham: product
        for product in products
    }

    recommendations = []

    for product_id in product_ids:

        product = product_map.get(
            product_id
        )

        if product:
            recommendations.append(product)

    return recommendations

# 3. LẤY ĐỦ LIMIT SẢN PHẨM GỢI Ý
def get_fallback_recommendations(
    ma_san_pham,
    exclude_ids,
    limit=4
):

    products = SanPham.query.filter(
        SanPham.trangThai == True,
        SanPham.maSanPham != ma_san_pham
    ).all()

    recommendations = []

    for product in products:

        if product.maSanPham in exclude_ids:
            continue

        recommendations.append(product)

        if len(recommendations) >= limit:
            break

    return recommendations

# 4. KẾT HỢP HAI NGUỒN GỢI Ý
def get_recommendations(
    ma_san_pham,
    user_id=None,
    limit=4
):

    recommendations = []

    product_ids = set()

    # Ưu tiên Apriori
    apriori_products = get_apriori_recommendations(
        ma_san_pham,
        limit=limit
    )

    for product in apriori_products:

        if product.maSanPham == ma_san_pham:
            continue

        if product.maSanPham not in product_ids:
            recommendations.append(product)

            product_ids.add(
                product.maSanPham
            )

        if len(recommendations) >= limit:
            return recommendations


    # Bổ sung sản phẩm từ hành vi khách hàng
    remaining = limit - len(recommendations)

    if remaining > 0 and user_id:

        behavior_products = get_behavior_recommendations(
            user_id,
            limit=remaining
        )

        for product in behavior_products:

            if product.maSanPham == ma_san_pham:
                continue

            if product.maSanPham not in product_ids:
                recommendations.append(product)

                product_ids.add(
                    product.maSanPham
                )

            if len(recommendations) >= limit:
                return recommendations

    # Lấy đủ limit sản phẩm gợi ý
    remaining = limit - len(recommendations)

    if remaining > 0:

        fallback_products = get_fallback_recommendations(
            ma_san_pham=ma_san_pham,
            exclude_ids=product_ids,
            limit=remaining
        )

        for product in fallback_products:

            if product.maSanPham not in product_ids:
                recommendations.append(product)

                product_ids.add(
                    product.maSanPham
                )

            if len(recommendations) >= limit:
                break
    return recommendations

if __name__ == "__main__":

    from nycosmetics import app

    with app.app_context():

        test_product = "SP000003"

        test_user = 3

        recommendations = get_recommendations(
            ma_san_pham=test_product,
            user_id=test_user,
            limit=4
        )

        print("KIỂM TRA RECOMMENDATION SERVICE")
        print("User: ", test_user)
        print("Sản phẩm đang xem:", test_product)
        print("Số sản phẩm gợi ý:", len(recommendations))

        for product in recommendations:
            print(product.maSanPham, " - ", product.tenSanPham)