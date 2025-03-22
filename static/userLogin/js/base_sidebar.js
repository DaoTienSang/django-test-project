document.addEventListener('DOMContentLoaded', function() {
    // 1. Xử lý việc chuyển đổi active menu items
    const menuItems = document.querySelectorAll('.sidebar .menu-item');
    
    menuItems.forEach(item => {
        item.addEventListener('click', function() {
            // Loại bỏ class active khỏi tất cả menu items
            menuItems.forEach(menuItem => {
                menuItem.classList.remove('active');
            });
            
            // Thêm class active vào menu item hiện tại
            this.classList.add('active');
        });
    });
    
    // 2. Tự động đánh dấu menu item dựa trên URL hiện tại
    const currentPath = window.location.pathname;
    
    menuItems.forEach(item => {
        const link = item.querySelector('a');
        if (link && link.getAttribute('href') !== '#') {
            const href = link.getAttribute('href');
            // Kiểm tra nếu href khớp với path hiện tại hoặc là một phần của nó
            if (currentPath === href || currentPath.startsWith(href) && href !== '/') {
                // Xóa active khỏi tất cả items
                menuItems.forEach(el => el.classList.remove('active'));
                // Thêm active cho item hiện tại
                item.classList.add('active');
            }
        }
    });
    
    // 3. Toggle sidebar trên màn hình nhỏ (nếu cần)
    // Tạo button toggle nếu chưa có
    if (!document.querySelector('.sidebar-toggle')) {
        const toggleBtn = document.createElement('div');
        toggleBtn.className = 'sidebar-toggle';
        toggleBtn.innerHTML = '☰';
        document.body.appendChild(toggleBtn);
        
        toggleBtn.addEventListener('click', function() {
            const sidebar = document.querySelector('.sidebar');
            sidebar.classList.toggle('show');
        });
    }
    
    // 4. Hiệu ứng ripple khi click
    menuItems.forEach(item => {
        item.addEventListener('click', function(e) {
            const link = this.querySelector('a');
            
            // Tạo hiệu ứng sóng (ripple)
            const ripple = document.createElement('span');
            ripple.classList.add('ripple');
            
            const rect = link.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            
            ripple.style.width = ripple.style.height = size + 'px';
            ripple.style.left = (e.clientX - rect.left - size/2) + 'px';
            ripple.style.top = (e.clientY - rect.top - size/2) + 'px';
            
            link.appendChild(ripple);
            
            // Xóa ripple sau khi animation hoàn thành
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });
    
    // 5. Xử lý dropdown menu
    const userDetail = document.querySelector('.user-detail');
    if (userDetail) {
        userDetail.addEventListener('click', function(e) {
            const detailAction = this.querySelector('.detail-action');
            detailAction.style.display = detailAction.style.display === 'block' ? 'none' : 'block';
            e.stopPropagation();
        });
        
        // Đóng dropdown khi click ra ngoài
        document.addEventListener('click', function() {
            const detailAction = document.querySelector('.detail-action');
            if (detailAction) {
                detailAction.style.display = 'none';
            }
        });
    }
});

document.addEventListener("DOMContentLoaded", function() {
    // Lặp qua tất cả các thông báo
    document.querySelectorAll(".notification").forEach(function(notification) {
        // Ẩn thông báo sau 5 giây
        setTimeout(function() {
            notification.classList.add("hidden"); // Thêm class hidden để mờ dần
        }, 5000); // 5000ms = 5 giây
    });
});