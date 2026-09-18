function addStaffToCart(
    id,
    name,
    price,
    image,
    category_id
) {

    fetch(
        "/api/admin/cart",
        {
            method: "POST",

            headers: {
                "Content-Type":
                    "application/json"
            },

            body: JSON.stringify({
                id: id,
                name: name,
                price: price,
                image: image,
                category_id: category_id
            })
        }
    )

    .then(response => {
        console.log("HTTP status:", response.status);
        return response.json();
    })

    .then(data => {

        if (data.status === 200) {
            alert(data.message);

            let counters =
                document.getElementsByClassName(
                    "cart-counter"
                );

            for (
                let i = 0;
                i < counters.length;
                i++
            ) {

                counters[i].innerText =
                    data.total_quantity;

            }

        } else {

            alert(data.message);

        }

    })

    .catch(err => {

        console.error(
            "Lỗi:",
            err
        );

        alert(
            "Không thể thêm sản phẩm!"
        );

    });
}

function findCustomer() {
    const phone = document.getElementById("customer-phone").value.trim();

    if (!phone) {
        alert("Vui lòng nhập số điện thoại!");
        return;
    }

    fetch(`/api/admin/find-customer?phone=${encodeURIComponent(phone)}`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 200) {
                document.getElementById("customer-info").innerHTML = `
                    <strong>Khách hàng:</strong> ${data.customer.name}<br>
                    <strong>Mã khách hàng:</strong> ${data.customer.maKhachHang}<br>
                    <strong>Số điện thoại:</strong> ${data.customer.dienThoai}
                `;
            } else {
                alert(data.message);
            }
        })
        .catch(error => {
            console.error("Lỗi:", error);
            alert("Có lỗi xảy ra khi tìm khách hàng!");
        });
}

function updateStaffCart(
    productId,
    input
) {

    let quantity =
        parseInt(input.value);


    if (
        isNaN(quantity)
        || quantity < 1
    ) {

        quantity = 1;

        input.value = 1;

    }


    fetch(
        "/admin/api/cart/update",
        {
            method: "POST",

            headers: {
                "Content-Type":
                    "application/json"
            },

            body: JSON.stringify({

                id: productId,

                quantity: quantity

            })

        }
    )

    .then(res => res.json())

    .then(data => {

        if (data.success) {

            location.reload();

        } else {

            alert(
                data.message
                || "Không thể cập nhật giỏ hàng!"
            );

        }

    })

    .catch(error => {

        console.error(
            "Lỗi cập nhật giỏ hàng:",
            error
        );

        alert(
            "Có lỗi xảy ra khi cập nhật giỏ hàng!"
        );

    });

}

function deleteStaffCart(
    productId
) {

    if (
        !confirm(
            "Bạn có chắc muốn xóa sản phẩm này khỏi đơn hàng?"
        )
    ) {

        return;

    }


    fetch(
        "/admin/api/cart/delete",
        {
            method: "POST",

            headers: {
                "Content-Type":
                    "application/json"
            },

            body: JSON.stringify({

                id: productId

            })

        }
    )

    .then(res => res.json())

    .then(data => {

        if (data.success) {

            location.reload();

        } else {

            alert(
                data.message
                || "Không thể xóa sản phẩm!"
            );

        }

    })

    .catch(error => {

        console.error(
            "Lỗi xóa sản phẩm:",
            error
        );

        alert(
            "Có lỗi xảy ra khi xóa sản phẩm!"
        );

    });

}

function exportStaffInvoice() {
    window.location.href = "/admin/xuat-hoa-don";
}