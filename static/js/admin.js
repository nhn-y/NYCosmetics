function updatePendingOrders() {
    fetch("{{ url_for('pending_orders') }}")
        .then(response => {
            if (!response.ok) {
                throw new Error("Không thể lấy số đơn chưa xác nhận");
            }

            return response.json();
        })
        .then(data => {
            const badge = document.getElementById("pending-order-badge");

            if (!badge) {
                return;
            }

            const count = data.count || 0;

            badge.textContent = count;
            badge.style.display = "inline-flex";
        })
        .catch(error => {
            console.error("Lỗi cập nhật số đơn:", error);
        });
}

// Cập nhật ngay khi mở trang
updatePendingOrders();

// Tự động kiểm tra mỗi 5 giây
setInterval(updatePendingOrders, 5000);
