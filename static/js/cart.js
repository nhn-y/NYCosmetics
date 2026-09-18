
// --- 1. THÊM SẢN PHẨM ---
function addToCart(id, name, price, image,category_id) {
    fetch('/api/cart', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            "id": id,
            "name": name,
            "price": price,
            "image": image,
            "category_id": category_id
        })
    })
    .then(res => res.json())
    .then(data => {
       let d = document.getElementsByClassName("cart-counter")
       for ( let i =0 ; i< d.length;i++ )
            d[i].innerText = data.total_quantity

    })
    .catch(err => {
        console.error("Lỗi:", err);
        alert(" Có lỗi xảy ra khi thêm vào giỏ hàng!");
    });

}
function updateCart(productId,obj){
    fetch(`/api/cart/${productId}`, {
        method: 'put',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            "quantity": obj.value
        })
    })
    .then(res => res.json()).then(data => {
       let d = document.getElementsByClassName("cart-counter")
       for ( let i =0 ; i< d.length;i++ )
            d[i].innerText = data.total_quantity

       let d2 = document.getElementsByClassName("cart-price")
       for ( let i =0 ; i< d2.length;i++ )
            d2[i].innerText = data.total_price.toLocaleString('en-US') + "VNĐ"

        let d3 = document.getElementsByClassName("cart-new-price");
        for (let i = 0; i < d3.length; i++) {
            // Nếu có voucher, giá trị này sẽ là số đã giảm.
            // Nếu chưa có, nó sẽ bằng total_price.
            let finalPrice = data.new_price || data.total_price;
            d3[i].innerText = finalPrice.toLocaleString('en-US') + " VNĐ";
        }

        // Gọi lại voucher để tính lại số tiền giảm (%) nếu cần
        const currentVoucher = document.getElementById('applied-voucher-code')?.value;
        if (currentVoucher) {
            applyVoucher(currentVoucher, false);
        }

    })


}
function deleteCart(productId){
    if(confirm("Bạn có chắc chắn muốn xóa không?") == true){
         fetch(`/api/cart/${productId}`, {
            method: 'delete',
            headers: { 'Content-Type': 'application/json' },
        })
        .then(res => res.json()).then(data => {
           let d = document.getElementsByClassName("cart-counter")
           for ( let i =0 ; i< d.length;i++ )
                d[i].innerText = data.total_quantity

           let d2 = document.getElementsByClassName("cart-price")
           for ( let i =0 ; i< d2.length;i++ )
                d2[i].innerText = data.total_price.toLocaleString('en-US') + " VNĐ"
            let d3 = document.getElementsByClassName("cart-new-price");
            for (let i = 0; i < d3.length; i++) {
                // Nếu có voucher, giá trị này sẽ là số đã giảm.
                // Nếu chưa có, nó sẽ bằng total_price.
                let finalPrice = data.new_price || data.total_price;
                d3[i].innerText = finalPrice.toLocaleString('en-US') + " VNĐ";
            }

            let c = document.getElementById(`cart${productId}`)
            c.style.display = "none"
        }).catch(err => console.error("Lỗi:", err))
    }
}
function applyVoucher(voucherId, showFeedback = true) {
    if (!voucherId || voucherId === "undefined") return;

    // CHÉP MÃ VÀO Ô ẨN để updateCart dùng được
    const hiddenInput = document.getElementById('applied-voucher-code');
    if (hiddenInput) hiddenInput.value = voucherId;

    fetch(`/api/apply-voucher/${voucherId}`, { // Đảm bảo Route này khớp với Backend
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 'voucher_id': voucherId })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 200) {
            // Cập nhật Giảm giá (Dấu phẩy)
            const discountEl = document.getElementById('discount-val');
            if (discountEl) {
                discountEl.innerText = "-" + data.discount_amount.toLocaleString('en-US') + "đ";
            }

            // Cập nhật Tổng thanh toán sau giảm (cart-new-price)
            document.querySelectorAll('.cart-new-price').forEach(el => {
                el.innerText = data.new_price.toLocaleString('en-US') + " VNĐ";
            });

            if (showFeedback) {
                alert("Áp dụng mã thành công!");
                const modal = bootstrap.Modal.getInstance(document.getElementById('discountModal'));
                if (modal) modal.hide();
            }
            const voucherContainer = document.getElementById('applied-vouchers-success');
            if (voucherContainer && data.applied_vouchers) {
                let html = "";
                // data.applied_vouchers là dictionary { 'SHIPPING': {...}, 'PROMOTION': {...} }
                for (const [kind, v] of Object.entries(data.applied_vouchers)) {
                    html += `
                        <div class="badge bg-light text-primary border me-2 p-2">
                            <i class="fa-solid fa-check-circle"></i> ${v.MaGG} (${kind})
                        </div>
                    `;
                }
                voucherContainer.innerHTML = html;
            }
        }else {
                if (showFeedback) {
                alert("Thông báo: " + data.message);

                /// đóng modal
                const modalEl = document.getElementById('discountModal');
                const modal = bootstrap.Modal.getInstance(modalEl);
                if (modal) modal.hide();
            }
        }
    }).catch(err => {
             console.error("Lỗi kết nối API:", err);
     });
}
function deleteApplyVoucher(){
    if(confirm("Bạn có chắc chắn muốn xóa không?") == true){
         fetch('/api/apply-voucher/', {
            method: 'delete',
            headers: { 'Content-Type': 'application/json' },
        })
        .then(res => res.json()).then(data => {
            if (data.status === 200) {
                // 1. Xóa sạch các badge (nhãn mã) trên giao diện
                const container = document.getElementById('applied-vouchers-success');
                if (container) container.innerHTML = "";

                // 2. Đưa con số Giảm giá về 0đ
                const discountEl = document.getElementById('discount-val');
                if (discountEl) discountEl.innerText = "0đ";

                // 3. Cập nhật Tổng thanh toán về bằng Tổng tiền gốc
                document.querySelectorAll('.cart-new-price').forEach(el => {
                    el.innerText = data.total_price.toLocaleString('en-US') + " VNĐ";
                });

                // 4. Xóa luôn giá trị trong ô ẩn
                const hiddenInput = document.getElementById('applied-voucher-code');
                if (hiddenInput) hiddenInput.value = "";
            }
        })
        .catch(err => console.error("Lỗi:", err));
    }
}

// --- 4. THANH TOÁN ---
function processCheckout() {


    const name = document.getElementById("receiver-name").value.trim();
    const phone = document.getElementById("receiver-phone").value.trim();
    const address = document.getElementById("receiver-address").value.trim();
    const paymentMethod = document.getElementById("payment-method").value;

    // 3. Validation (Regex của Yến rất tốt rồi!)
    const nameRegex = /^[a-zA-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚĂĐĨŨƠàáâãèéêìíòóôõùúăđĩũơƯĂẠẢẤẦẨẪẬẮẰẲẴẶẸẺẼỀỀỂưăạảấầẩẫậắằẳẵặẹẻẽềềểỄỆỈỊỌỎỐỒỔỖỘỚỜỞỠỢỤỦỨỪỬỮỰYỲỴÝỶỸửữựyỳỵýỷỹ\s]{2,50}$/;
    if (!nameRegex.test(name)) { alert("Tên người nhận không hợp lệ (2-50 ký tự)."); return; }
    if (!/^(03|05|07|08|09)\d{8}$/.test(phone)) { alert("Số điện thoại không đúng định dạng VN."); return; }
    if (address.length < 10) { alert("Vui lòng nhập địa chỉ cụ thể hơn (tối thiểu 10 ký tự)."); return; }

    // 4. Gửi Request
    if (confirm("Xác nhận đặt hàng?")) {
        // Có thể vô hiệu hóa nút bấm ở đây để tránh nhấn 2 lần
        // e.target.disabled = true;

        fetch('/api/checkout', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name,
                phone,
                address,
                "payment_method": paymentMethod
            })
        })
        .then(res => res.json())
        .then(data => {
            if (data.status === 200) {
                alert(data.message);
                window.location.href = "/";
            } else {
                // QUAN TRỌNG: Hiện thông báo nếu Backend báo lỗi
                alert(data.message);
            }
        })
        .catch(err => {
            console.error("Lỗi hệ thống:", err);
            alert("Có lỗi xảy ra trong quá trình thanh toán.");
        });
    }
}


function parseDate(str) {
    const p = str.split('/');
    return new Date(p[2], p[1] - 1, p[0]);
}

// Thêm tham số voucherId vào hàm
