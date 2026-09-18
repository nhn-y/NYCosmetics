import pandas as pd
from collections import defaultdict
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori, association_rules
from nycosmetics.models import db, DonHang, ChiTietDonHang
from nycosmetics import app

# 1. LẤY GIAO DỊCH

def load_transactions():

    orders = DonHang.query.filter(
        DonHang.trangThai.in_(["ChoXacNhan", "DaXacNhan", "DangGiao", "DaGiao", "HoanThanh", "DaHuy"])
    ).all()

    transactions = []

    for order in orders:

        products = set()

        for detail in order.chiTietDonHangs:

            products.add(
                detail.maSanPham
            )

        if len(products) >= 2:

            transactions.append(
                list(products)
            )

    return transactions

# 2. ONE-HOT ENCODING

def encode_transactions(transactions):

    te = TransactionEncoder()

    encoded_array = te.fit(
        transactions
    ).transform(
        transactions
    )

    df = pd.DataFrame(
        encoded_array,
        columns=te.columns_
    )

    return df

# 3. APRIORI

def run_apriori(df):

    frequent_itemsets = apriori(
        df,
        min_support=0.05,
        use_colnames=True
    )

    return frequent_itemsets

# 4. ASSOCIATION RULES

def generate_rules(
    frequent_itemsets,
    transaction_count
):

    rules = association_rules(
        frequent_itemsets,
        metric="confidence",
        min_threshold=0.3,
        num_itemsets=transaction_count
    )

    return rules

# 5. LỌC RULE

def filter_rules(rules):

    rules = rules[
        (rules["confidence"] >= 0.3)
        &
        (rules["lift"] > 1)
    ]

    rules = rules.sort_values(
        [
            "lift",
            "confidence"
        ],
        ascending=False
    )

    return rules

def get_apriori_rules():

    transactions = load_transactions()

    if not transactions:
        return pd.DataFrame()

    df_transactions = encode_transactions(
        transactions
    )

    if df_transactions.empty:
        return pd.DataFrame()

    frequent_itemsets = run_apriori(
        df_transactions
    )

    if frequent_itemsets.empty:
        return pd.DataFrame()

    rules = generate_rules(
        frequent_itemsets,
        len(df_transactions)
    )

    if rules.empty:
        return pd.DataFrame()

    filtered_rules = filter_rules(
        rules
    )

    return filtered_rules

def get_recommended_product_ids(
    ma_san_pham,
    limit=4
):

    rules = get_apriori_rules()

    if rules.empty:
        return []

    recommended_ids = []

    for _, rule in rules.iterrows():

        antecedents = rule["antecedents"]
        consequents = rule["consequents"]

        # Sản phẩm đang xem phải nằm trong antecedent
        if ma_san_pham not in antecedents:
            continue

        # Lấy sản phẩm ở consequent
        for product_id in consequents:

            if product_id == ma_san_pham:
                continue

            if product_id not in recommended_ids:

                recommended_ids.append(
                    product_id
                )

            if len(recommended_ids) >= limit:
                return recommended_ids

    return recommended_ids

if __name__ == "__main__":
    with app.app_context():

        # Bước 1: lấy giao dịch
        transactions = load_transactions()

        print("Số giao dịch:", len(transactions))
        #
        # for transaction in transactions[:10]:
        #     print(transaction)

        # Bước 2: One-hot Encoding
        df_transactions = encode_transactions(transactions)

        print("Dữ liệu One-hot:")
        print(df_transactions.head(10))

        print("Kích thước:")
        print(df_transactions.shape)

        # Bước 3
        frequent_itemsets = run_apriori(df_transactions)
        print("Các tập sản phẩm phổ biến:")
        print(frequent_itemsets)

        # Bước 4
        rules = generate_rules(frequent_itemsets, len(df_transactions))

        print("ASSOCIATION RULES:")
        print(
            rules[
                [
                    "antecedents",
                    "consequents",
                    "support",
                    "confidence",
                    "lift"
                ]
            ]
        )

        # Bước 5
        filtered_rules = filter_rules(rules)

        print("RULE SAU KHI LỌC:")
        print(
            filtered_rules[
                [
                    "antecedents",
                    "consequents",
                    "support",
                    "confidence",
                    "lift"
                ]
            ]
        )

        # Bước 6
        test_product = "SP000003"

        recommendations = get_recommended_product_ids(
            test_product,
            limit=4
        )

        print("SẢN PHẨM GỢI Ý")
        print("Sản phẩm đang xem:", test_product)
        print("Sản phẩm gợi ý:", recommendations)