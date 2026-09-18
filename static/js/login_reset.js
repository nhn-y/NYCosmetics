async function startForgotPassword() {
    // BƯỚC 1: HIỆN POPUP NHẬP USERNAME & EMAIL
    const { value: userInfo } = await Swal.fire({
        title: 'Quên mật khẩu?',
        html: `
            <p style="font-size: 14px; color: #666; margin-bottom: 10px;">
                Nhập chính xác thông tin để nhận mã OTP:
            </p>
            <input id="swal-username" class="swal2-input" placeholder="Tên đăng nhập (Username)">
            <input id="swal-email" type="email" class="swal2-input" placeholder="Email đăng ký">
        `,
        focusConfirm: false,
        showCancelButton: true,
        confirmButtonText: 'Gửi mã OTP',
        confirmButtonColor: '#6CD25B',
        showLoaderOnConfirm: true,
        preConfirm: () => {
            const username = document.getElementById('swal-username').value.trim();
            const email = document.getElementById('swal-email').value.trim();

            if (!username || !email) {
                Swal.showValidationMessage('Vui lòng nhập đủ Username và Email nhé!');
                return false;
            }

            // Gọi API gửi OTP và kiểm tra dữ liệu
            return fetch('/api/send-otp', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    username: username,
                    email: email
                })
            })
            .then(response => response.json())
            .then(data => {
                if (!data.success) {
                    throw new Error(data.message); // Backend sẽ báo nếu email không khớp username
                }
                return { username, email }; // Trả về để dùng cho bước sau
            })
            .catch(error => {
                Swal.showValidationMessage(`${error.message}`);
            });
        }
    });

    // BƯỚC 2: NẾU THÔNG TIN KHỚP & GỬI MAIL THÀNH CÔNG
    if (userInfo) {
        const { value: isSuccess } = await Swal.fire({
            title: 'Đặt lại mật khẩu',
            html: `
                <p style="font-size: 14px; color: #666; margin-bottom: 10px;">
                    Mã OTP đã gửi tới <b>${userInfo.email}</b>
                </p>
                <input id="swal-otp" class="swal2-input" placeholder="Nhập mã OTP 6 số">
                <input id="swal-pass" type="password" class="swal2-input" placeholder="Mật khẩu mới">
            `,
            focusConfirm: false,
            confirmButtonText: 'Xác nhận đổi',
            confirmButtonColor: '#8e24aa',
            showCancelButton: true,
            preConfirm: () => {
                const otp = document.getElementById('swal-otp').value.trim();
                const newPass = document.getElementById('swal-pass').value.trim();

                if (!otp || !newPass) {
                    Swal.showValidationMessage('Vui lòng nhập đủ OTP và Mật khẩu mới');
                    return false;
                }

                return fetch('/api/verify-reset', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        username: userInfo.username, // Gửi username để server biết đổi cho ai
                        email: userInfo.email,
                        otp: otp,
                        new_password: newPass
                    })
                })
                .then(res => res.json())
                .then(data => {
                    if (!data.success) throw new Error(data.message);
                    return true;
                })
                .catch(error => {
                    Swal.showValidationMessage(`${error.message}`);
                });
            }
        });

        // BƯỚC 3: THÀNH CÔNG
        if (isSuccess) {
            Swal.fire({
                icon: 'success',
                title: 'Thành công!',
                text: 'Mật khẩu đã được thay đổi. Đăng nhập ngay!',
                confirmButtonColor: '#6CD25B'
            });
        }
    }
}