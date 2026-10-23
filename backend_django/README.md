# CoffeeFlow Backend (Django + Django REST Framework)

Backend thay thế xây dựng bằng **Django** và **Django REST Framework (DRF)** cho hệ thống CoffeeFlow POS.
Backend này tương thích hoàn toàn 100% với:
- **Cơ sở dữ liệu (PostgreSQL)**: Sử dụng chung schema và database `coffeeflow` với FastAPI backend hiện tại.
- **Frontend (React + Vite + TypeScript)**: Cung cấp đầy đủ các API endpoint tại `http://localhost:8000/api/v1` với chuẩn xác thực JWT và CORS.

---

## 1. Cấu trúc thư mục

```
backend_django/
├── coffeeflow/             # Cấu hình dự án Django
│   ├── settings.py         # Cấu hình DB, CORS, JWT, DRF
│   ├── urls.py             # Root URL routing (/api/v1/ và /health)
│   ├── wsgi.py
│   └── asgi.py
├── api/                    # Ứng dụng nghiệp vụ chính
│   ├── models.py           # Model ORM map 1:1 với schema DB (users, categories, products, orders,...)
│   ├── serializers.py      # Serializer DRF
│   ├── authentication.py   # JWT Authentication & Role-based Permissions (Manager/Cashier)
│   ├── views.py            # API Views (Auth, Menu, Orders, POS Checkout, Inventory, Dashboard)
│   ├── urls.py             # Routing chi tiết /api/v1/...
│   ├── tests.py            # Automated Unit & Integration Tests
│   └── management/
│       └── commands/
│           └── seed_data.py # Command khởi tạo tài khoản & dữ liệu mẫu
├── Dockerfile              # Dockerfile cho Django
├── requirements.txt        # Thư viện phụ thuộc
├── manage.py
├── .env.example
└── .env
```

---

## 2. Các tính năng & Endpoints chính (/api/v1)

### 2.1. Xác thực (Authentication):
- `POST /api/v1/auth/login`: Đăng nhập bằng `username` và `password`, trả về JWT `access_token`, `role`, `full_name`.
- `GET /api/v1/auth/me`: Lấy thông tin tài khoản hiện tại.

### 2.2. Danh mục & Sản phẩm (Menu):
- `GET /api/v1/categories`: Danh sách danh mục món.
- `POST /api/v1/categories`: Thêm danh mục (Manager).
- `PUT /api/v1/categories/<id>`: Cập nhật danh mục (Manager).
- `GET /api/v1/products`: Danh sách sản phẩm kèm định lượng nguyên liệu (recipes), hỗ trợ filter `category_id`, `is_active`.
- `POST /api/v1/products`: Thêm sản phẩm (Manager).
- `PUT /api/v1/products/<id>`: Cập nhật sản phẩm (Manager).

### 2.3. Quản lý kho & Nguyên liệu (Inventory):
- `GET /api/v1/ingredients` & `GET /api/v1/inventory/ingredients`: Danh sách nguyên liệu tồn kho.
- `POST /api/v1/ingredients`: Thêm nguyên liệu (Manager).
- `PUT /api/v1/ingredients/<id>`: Sửa nguyên liệu (Manager).
- `POST /api/v1/inventory/import` & `POST /api/v1/ingredients/import`: Nhập kho nguyên liệu (Manager), tự động cập nhật số lượng và ghi `stock_movements`.
- `GET /api/v1/inventory/movements`: Lịch sử biến động xuất / nhập kho.

### 2.4. Đơn hàng & POS Checkout (Orders):
- `GET /api/v1/orders`: Danh sách đơn hàng (hỗ trợ filter `status`, phân trang `limit`, `offset`).
- `POST /api/v1/orders`: Tạo đơn hàng mới từ POS, snapshot giá bán, tính `subtotal` và `total_amount`.
- `GET /api/v1/orders/<id>`: Chi tiết đơn hàng kèm danh sách món và thanh toán.
- `POST /api/v1/orders/<id>/checkout`: Thanh toán hóa đơn (hỗ trợ Tiền mặt / Chuyển khoản / Thẻ). Tự động trừ tồn kho nguyên liệu theo định lượng (cơ chế ACID `select_for_update`), ghi log giao dịch `Payment` và hoàn tất đơn hàng (`COMPLETED`).
- `POST /api/v1/orders/<id>/confirm`: Xác nhận đơn hàng.
- `PATCH /api/v1/orders/<id>/status`: Cập nhật trạng thái đơn hàng.

### 2.5. Báo cáo & Quản trị (Management):
- `GET /api/v1/management/dashboard/metrics`: Tổng doanh thu, tổng số đơn hàng, tổng số món đã bán, số bàn đang phục vụ, cảnh báo nguyên liệu sắp hết.
- `GET /api/v1/management/reports/sales`: Báo cáo doanh thu theo ngày / tuần / tháng.
- `GET /api/v1/management/audit-logs`: Nhật ký kiểm toán hệ thống.
- `GET /api/v1/management/employees`: Danh sách nhân viên.
- `GET /api/v1/management/inventory-status`: Tình trạng tồn kho cho trang quản lý.

---

## 3. Hướng dẫn khởi chạy

### Cách 1: Chạy trực tiếp qua Python Virtual Environment

1. **Kích hoạt virtual environment và cài đặt thư viện**:
   ```bash
   cd backend_django
   ..\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

2. **Cấu hình môi trường (`.env`)**:
   File `.env` mặc định đã trỏ tới PostgreSQL:
   ```env
   SECRET_KEY=supersecretkey0123456789abcdefghijklmnopqrstuvwxyz
   DEBUG=True
   ALLOWED_HOSTS=*
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/coffeeflow
   CORS_ALLOW_ALL_ORIGINS=True
   ```

3. **Khởi tạo dữ liệu mẫu (Seeding)**:
   ```bash
   ..\.venv\Scripts\python.exe manage.py seed_data
   ```
   Tài khoản mặc định:
   - Manager: `manager` / mật khẩu `password123`
   - Cashier: `cashier` / mật khẩu `password123`

4. **Chạy server backend Django trên cổng 8000**:
   ```bash
   ..\.venv\Scripts\python.exe manage.py runserver 8000
   ```

5. **Chạy Frontend (React + Vite)**:
   Mở terminal khác:
   ```bash
   cd frontend
   npm run dev
   ```
   Truy cập giao diện tại `http://localhost:5173` hoặc `http://localhost:3000`. Frontend sẽ tự động gọi API tới Django tại `http://localhost:8000/api/v1`.

---

### Cách 2: Chạy toàn bộ hệ thống bằng Docker Compose

Dự án có sẵn file cấu hình `docker-compose.django.yml`:

```bash
docker-compose -f docker-compose.django.yml up --build
```

Lệnh này sẽ khởi chạy tự động:
- `coffeeflow-db`: PostgreSQL 16
- `coffeeflow-backend-django`: Django Backend trên cổng 8000
- `coffeeflow-frontend`: React Frontend trên cổng 3000

---

## 4. Chạy Automated Tests

Để kiểm tra độ toàn vẹn và các nghiệp vụ POS / Auth / Reports:
```bash
cd backend_django
..\.venv\Scripts\python.exe manage.py test api
```
