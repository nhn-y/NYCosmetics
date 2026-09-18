function updatePendingOrders() {
    fetch(pendingOrdersUrl)
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

/* ===================== */
/* DOANH THU 7 NGÀY */
/* ===================== */

function createRevenueChart(revenueData) {

    const revenueLabels =
        revenueData.map(
            item => item.date
        );


    const revenueValues =
        revenueData.map(
            item => item.revenue
        );


    new Chart(
        document.getElementById(
            'revenueChart'
        ),
        {
            type: 'line',

            data: {

                labels: revenueLabels,

                datasets: [

                    {
                        label: 'Doanh thu',

                        data: revenueValues,

                        borderWidth: 2,

                        tension: 0.3,

                        fill: true

                    }

                ]

            },

            options: {

                responsive: true,

                maintainAspectRatio: false,

                plugins: {

                    legend: {
                        display: false
                    }

                },

                scales: {

                    y: {

                        beginAtZero: true,

                        ticks: {

                            callback: function(value) {

                                return value.toLocaleString(
                                    'vi-VN'
                                ) + ' đ';

                            }

                        }

                    }

                }

            }

        }
    );
}


/* ===================== */
/* DANH MỤC BÁN CHẠY */
/* ===================== */

function createCategoryChart(categoryData) {

    const categoryLabels =
        categoryData.map(
            item => item.name
        );


    const categoryValues =
        categoryData.map(
            item => item.quantity
        );


    new Chart(
        document.getElementById(
            'categoryChart'
        ),
        {
            type: 'doughnut',

            data: {

                labels: categoryLabels,

                datasets: [

                    {
                        data: categoryValues
                    }

                ]

            },

            options: {

                responsive: true,

                maintainAspectRatio: false,

                plugins: {

                    legend: {

                        position: 'bottom'

                    }

                }

            }

        }
    );
}


/* ===================== */
/* KHỞI TẠO BIỂU ĐỒ */
/* ===================== */

document.addEventListener(
    'DOMContentLoaded',
    function() {

        createRevenueChart(
            dashboardData.revenue7Days
        );


        createCategoryChart(
            dashboardData.categoryStatistics
        );

    }
);
