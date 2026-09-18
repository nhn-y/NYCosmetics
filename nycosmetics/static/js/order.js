function cancelOrder(maDonHang) {

    const confirmCancel = confirm(
        "Bạn có chắc chắn muốn hủy đơn hàng này?"
    );

    if (!confirmCancel) {
        return;
    }


    fetch(
        `/api/orders/${maDonHang}/cancel`,
        {
            method: "POST"
        }
    )
    .then(response => {

        return response.json().then(data => ({
            ok: response.ok,
            data: data
        }));

    })
    .then(result => {

        if (!result.ok) {

            alert(result.data.message);

            return;
        }


        if (result.data.success) {

            alert(
                "Đã hủy đơn hàng thành công!"
            );

            location.reload();

        }

    })
    .catch(error => {

        console.error(error);

        alert(
            "Có lỗi xảy ra khi hủy đơn hàng!"
        );

    });
}

function updatePaymentStatus(statusSelect) {
    const row = statusSelect.closest("tr");

    if (!row) {
        return;
    }

    const paymentSelect =
        row.querySelector(
            'select[name="trangThaiThanhToan"]'
        );

    if (!paymentSelect) {
        return;
    }

    if (statusSelect.value === "DaGiao") {
        paymentSelect.value = "DaThanhToan";
    }
}