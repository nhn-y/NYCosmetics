function addToCart(maSanPham, tenSanPham, giaBan, hinhAnh, maDanhMuc) {
    fetch('/api/cart', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            "maSanPham": maSanPham,
            "tenSanPham": tenSanPham,
            "giaBan": giaBan,
            "hinhAnh": hinhAnh,
            "maDanhMuc": maDanhMuc
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 401) {
            alert(data.message);
            window.location.href = "/login";
            return;
        }

        if (data.status === 200) {
            let counters = document.getElementsByClassName("cart-counter");

            for (let i = 0; i < counters.length; i++) {
                counters[i].innerText = data.total_quantity;
            }

            alert("Đã thêm sản phẩm vào giỏ hàng!");
        }
    })
    .catch(err => {
        console.error("Lỗi:", err);
        alert(" Có lỗi xảy ra khi thêm vào giỏ hàng!");
    });
}

function updateCart(maSanPham, obj) {
    fetch(`/api/cart/${maSanPham}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            "quantity": obj.value
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success === false) {
            alert(data.message);
            return;
        }
        // Cập nhật số lượng trong giỏ hàng
        const counters = document.getElementsByClassName("cart-counter");

        for (let i = 0; i < counters.length; i++) {
            counters[i].innerText = data.total_quantity;
        }

        // Cập nhật tổng tiền
        const prices = document.getElementsByClassName("cart-price");

        for (let i = 0; i < prices.length; i++) {
            prices[i].innerText = Number(data.total_price).toLocaleString('vi-VN') + " VNĐ";
        }
    })
    .catch(err => {
        console.error(
            "Lỗi cập nhật giỏ hàng:",
            err
        );
    });
}

function deleteCart(maSanPham) {
    if(confirm("Bạn có chắc chắn muốn xóa không?") == true){
        fetch(`/api/cart/${maSanPham}`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
        })
        .then(res => res.json())
        .then(data => {
            if (data.success === false) {
                alert(data.message);
                return;
            }

            const counters = document.getElementsByClassName("cart-counter");

            for (let i = 0; i < counters.length; i++) {
                counters[i].innerText = data.total_quantity;
            }

            const prices = document.getElementsByClassName("cart-price");

            for (let i = 0; i < prices.length; i++) {
                prices[i].innerText = Number(data.total_price).toLocaleString('vi-VN') + " VNĐ";
            }

            // Xóa sản phẩm khỏi giao diện
            const cartItem = document.getElementById (`cart${maSanPham}`);

            if (cartItem) {
                cartItem.style.display = "none";
            }
        })

        .catch(err => {
            console.error(
               "Lỗi cập nhật giỏ hàng:",
               err
            );
        });
    }
}

function processCheckout() {
    const name = document.getElementById("receiver-name").value.trim();
    const phone = document.getElementById("receiver-phone").value.trim();
    const address = document.getElementById("receiver-address").value.trim();
    const paymentMethod = document.getElementById("payment-method").value;

    const nameRegex =/^[a-zA-ZÀ-ỹ\s]{1,50}$/;
    if (!nameRegex.test(name)) {alert("Tên người nhận không hợp lệ."); return; }
    if (!/^(03|05|07|08|09)\d{8}$/.test(phone)) { alert("Số điện thoại không đúng định dạng VN."); return; }
    if (address.length < 10) { alert("Vui lòng nhập địa chỉ cụ thể hơn (tối thiểu 10 ký tự)."); return; }

    if (confirm("Bạn có chắc chắn muốn đặt hàng không?")) {
        fetch('/api/checkout', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: name,
                phone: phone,
                address: address,
                payment_method: paymentMethod
            })
        })
        .then(res => res.json())
        .then(data => {
            if (data.status === 200) {
                alert(data.message);
                if (data.redirect) {
                    window.location.href = data.redirect;
                }
                else {
                    window.location.href = "/";
                }
            }
            else {
                //Hiện thông báo nếu Backend báo lỗi
                alert(data.message);
            }
        })
        .catch(err => {
            console.error("Lỗi hệ thống:", err);
            alert("Có lỗi xảy ra trong quá trình thanh toán.");
        });
    }
}
