# ☕ CoffeeFlow — Hệ Thống Quản Lý Quán Cà Phê & POS Bán Hàng

> **CoffeeFlow** là hệ thống quản lý quán cà phê toàn diện bao gồm phân hệ bán hàng tại quầy (**Cashier POS**) và phân hệ điều hành quản trị (**Manager Dashboard**). Hệ thống được xây dựng theo kiến trúc hiện đại với **Backend Django REST Framework**, **Frontend React + TypeScript + Vite**, và cơ sở dữ liệu **PostgreSQL**.

---

## 📌 Mục Lục
1. [Tính Năng Chính](#-tính-năng-chính)
2. [Kiến Trúc & Công Nghệ](#-kiến-trúc--công-nghệ)
3. [Tài Khoản Đăng Nhập Mặc Định](#-tài-khoản-đăng-nhập-mặc-định)
4. [Hướng Dẫn Khởi Chạy Nhanh](#-hướng-dẫn-khởi-chạy-nhanh)
   - [Cách 1: Khởi chạy bằng Docker Compose (Khuyên dùng)](#cách-1-khởi-chạy-bằng-docker-compose-khuyên-dùng)
   - [Cách 2: Khởi chạy thủ công từng phần (Local Dev)](#cách-2-khởi-chạy-thủ-công-từng-phần-local-dev)
5. [Cấu Trúc Thư Mục Dự Án](#-cấu-trúc-thư-mục-dự-án)
6. [Tài Liệu API Endpoints (/api/v1)](#-tài-liệu-api-endpoints-apiv1)
7. [Kiểm Thử Tự Động (Quality Gates)](#-kiểm-thử-tự-động-quality-gates)

---

## 🚀 Tính Năng Chính

### 1. Phân Hệ Thu Ngân (Cashier POS — `/pos`)
- **Giao diện chạm thân thiện (Touch-friendly)**: Thiết kế tối ưu cho máy POS cảm ứng và máy tính bảng tại quầy.
- **Tìm kiếm & Phân loại món**: Lọc nhanh theo danh mục (Cà phê phin, Cà phê máy, Trà & Macchiato, Bánh ngọt).
- **Tùy chỉnh đơn hàng**: Chọn số lượng, thêm ghi chú (ít đá, nhiều đường, ngọt vừa).
- **Thanh toán tức thì (Checkout)**: Hỗ trợ thanh toán Tiền mặt (Cash), Chuyển khoản QR (QR Pay), Thẻ ngân hàng (Card). Tự động tính tiền thừa trả khách.
- **Trừ kho nguyên liệu tự động (ACID)**: Áp dụng cơ chế khóa giao dịch `select_for_update` trừ nguyên liệu trong kho theo định lượng (recipe) chuẩn xác, chống thất thoát.

### 2. Phân Hệ Quản Trị (Manager Dashboard)
- **Tổng quan KPI (`/dashboard`)**: Doanh thu trong ngày, số đơn hàng hoàn thành, số lượng ly đã bán, số bàn đang phục vụ, cảnh báo nguyên liệu sắp hết.
- **Báo cáo doanh thu (`/reports`)**: Thống kê doanh thu theo ngày, tuần, tháng với biểu đồ trực quan.
- **Quản lý thực đơn (`/products`)**: Quản lý danh mục món, giá bán, công thức nguyên liệu cho từng món.
- **Quản lý kho nguyên liệu (`/inventory`)**: Theo dõi tồn kho thực tế, nhập kho nguyên liệu mới kèm lưu lịch sử biến động kho (`stock_movements`).
- **Nhật ký kiểm toán (`Audit Logs`)**: Ghi nhận toàn bộ thao tác quan trọng (đăng nhập, tạo đơn, thanh toán, nhập kho).

---

## 🛠️ Kiến Trúc & Công Nghệ

| Thành Phần | Công Nghệ Sử Dụng | Chi Tiết |
| :--- | :--- | :--- |
| **Backend** | Python 3.12+, **Django 6**, **Django REST Framework (DRF)** | `django-cors-headers`, `PyJWT`, `bcrypt`, kiến trúc Model-Serializer-View chuẩn mực |
| **Frontend** | **React 19**, **TypeScript**, **Vite**, **Tailwind CSS** | SPA tốc độ cao, Axios Client với Interceptor tự động xử lý JWT Bearer token |
| **Database** | **PostgreSQL 16** | Quy tắc Zero-Float (lưu trữ tiền tệ dạng số nguyên VND), Transaction Atomic |
| **Container** | **Docker & Docker Compose** | Tự động hóa build, migrate và seed dữ liệu khởi động |

---

## 👤 Tài Khoản Đăng Nhập Mặc Định

Dữ liệu mẫu ban đầu đã được cấu hình sẵn 2 tài khoản:

| Vai trò (Role) | Username | Password | Quyền hạn |
| :--- | :--- | :--- | :--- |
| **Quản lý (MANAGER)** | `manager` | `password123` | Toàn quyền xem Dashboard, Quản lý Menu, Nhập kho, Báo cáo |
| **Thu ngân (CASHIER)** | `cashier` | `password123` | Phân hệ POS bán hàng, tạo đơn hàng và thanh toán |

---

## ⚡ Hướng Dẫn Khởi Chạy Nhanh

### Cách 1: Khởi chạy bằng Docker Compose (Khuyên dùng)

Chỉ với 1 câu lệnh duy nhất, toàn bộ hệ thống gồm Database, Backend Django và Frontend React sẽ tự động khởi động:

```bash
docker-compose -f docker-compose.django.yml up --build
```

Container sẽ tự động chạy `makemigrations`, `migrate` và `seed_data`. Sau khi khởi động thành công:
- **Giao diện Frontend**: Mở trình duyệt tại [http://localhost:3000](http://localhost:3000)
- **Backend API**: Truy cập tại [http://localhost:8000/api/v1](http://localhost:8000/api/v1)
- **Kiểm tra trạng thái**: [http://localhost:8000/health](http://localhost:8000/health)

Để dừng hệ thống:
```bash
docker-compose -f docker-compose.django.yml down
```

---

### Cách 2: Khởi chạy thủ công từng phần (Local Dev)

#### 1. Khởi chạy Database (PostgreSQL)
Nếu sử dụng Docker cho PostgreSQL:
```bash
docker run -d --name coffeeflow-db -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=coffeeflow -p 5432:5432 postgres:16-alpine
```

#### 2. Khởi chạy Backend (Django)
```bash
cd backend_django

# 1. Cài đặt các thư viện cần thiết
pip install -r requirements.txt

# 2. Thực hiện migrate cơ sở dữ liệu
python manage.py migrate

# 3. Khởi tạo tài khoản và thực đơn mẫu
python manage.py seed_data

# 4. Khởi chạy server Django trên cổng 8000
python manage.py runserver 8000
```

#### 3. Khởi chạy Frontend (React + Vite)
Mở một cửa sổ dòng lệnh (terminal) mới:
```bash
cd frontend

# 1. Cài đặt dependencies (nếu chưa có)
npm install

# 2. Chạy Vite dev server
npm run dev
```
Truy cập giao diện tại [http://localhost:5173](http://localhost:5173) hoặc [http://localhost:3000](http://localhost:3000).

---

## 📁 Cấu Trúc Thư Mục Dự Án

```text
Coffeeflow-shop/
├── backend_django/                       # ☕ Phân hệ Backend Django + DRF
│   ├── coffeeflow/                       # Project Settings & Root URLs
│   │   ├── settings.py                   # Cấu hình DB PostgreSQL, CORS, JWT, DRF
│   │   ├── urls.py                       # Root URL routing (/api/v1/ và /health)
│   │   ├── wsgi.py
│   │   └── asgi.py
│   ├── api/                              # App xử lý nghiệp vụ chính
│   │   ├── models.py                     # SQLAlchemy/Django ORM Models (User, Category, Product, Order,...)
│   │   ├── serializers.py                # Serializers cho request/response
│   │   ├── authentication.py             # JWT Authentication Backend & Permission Classes
│   │   ├── views.py                      # REST API Views: POS, Checkout, Stock, Dashboard
│   │   ├── urls.py                       # URLs định tuyến chi tiết /api/v1/...
│   │   ├── tests.py                      # Bộ Unit & Integration Tests tự động
│   │   └── management/commands/
│   │       └── seed_data.py              # Command khởi tạo tài khoản & menu mẫu
│   ├── Dockerfile                        # Dockerfile container Backend
│   ├── requirements.txt                  # Thư viện Python
│   ├── manage.py
│   └── .env                              # Biến môi trường kết nối DB
├── frontend/                             # ⚛️ Phân hệ Frontend (React 19 + TypeScript + Vite)
│   ├── src/
│   │   ├── components/                   # UI dùng chung: Layout, Sidebar, Header
│   │   ├── pages/                        # CashierPOS, Dashboard, ProductsMenu, Inventory, Reports, Login
│   │   ├── services/
│   │   │   └── api.ts                    # Axios Client kèm JWT Interceptor & Error Handler
│   │   ├── types/                        # TypeScript Types đồng bộ 1:1 với Backend Schemas
│   │   ├── App.tsx                       # React Router & Role-Based Guards
│   │   └── main.tsx
│   ├── Dockerfile                        # Dockerfile multi-stage Nginx
│   └── package.json
├── docker-compose.django.yml             # Docker Compose điều phối trọn gói DB + BE + FE
└── README.md                             # Tài liệu hướng dẫn dự án
```

---

## 📡 Tài Liệu API Endpoints (`/api/v1`)

### 1. Xác thực (Authentication)
| Method | Endpoint | Yêu cầu quyền | Mô tả |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/auth/login` | Công khai | Đăng nhập nhận `access_token`, `role`, `full_name` |
| `GET` | `/api/v1/auth/me` | Đã đăng nhập | Xem thông tin tài khoản hiện tại |

### 2. Thực Đơn & Danh Mục (Menu)
| Method | Endpoint | Yêu cầu quyền | Mô tả |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/categories` | Đã đăng nhập | Lấy danh sách danh mục món |
| `POST` | `/api/v1/categories` | MANAGER | Tạo danh mục mới |
| `PUT` | `/api/v1/categories/<id>` | MANAGER | Cập nhật danh mục |
| `GET` | `/api/v1/products` | Đã đăng nhập | Lấy danh sách món (hỗ trợ lọc `category_id`, `is_active`) |
| `POST` | `/api/v1/products` | MANAGER | Thêm món mới kèm công thức nguyên liệu (recipes) |
| `PUT` | `/api/v1/products/<id>` | MANAGER | Cập nhật món và công thức |

### 3. Đơn Hàng & POS Checkout (Orders)
| Method | Endpoint | Yêu cầu quyền | Mô tả |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/orders` | Đã đăng nhập | Lấy danh sách đơn hàng (hỗ trợ lọc `status`, phân trang) |
| `POST` | `/api/v1/orders` | Đã đăng nhập | Tạo đơn hàng mới từ POS |
| `GET` | `/api/v1/orders/<id>` | Đã đăng nhập | Xem chi tiết đơn hàng |
| `POST` | `/api/v1/orders/<id>/checkout` | Đã đăng nhập | Thanh toán đơn hàng, tự động trừ kho nguyên liệu |
| `PATCH` | `/api/v1/orders/<id>/status` | Đã đăng nhập | Cập nhật trạng thái đơn hàng |

### 4. Quản Lý Kho (Inventory)
| Method | Endpoint | Yêu cầu quyền | Mô tả |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/inventory/ingredients` | Đã đăng nhập | Lấy danh sách tồn kho nguyên liệu |
| `POST` | `/api/v1/inventory/import` | MANAGER | Nhập kho nguyên liệu, ghi log biến động |
| `GET` | `/api/v1/inventory/movements` | Đã đăng nhập | Xem lịch sử xuất / nhập kho |

### 5. Quản Trị & Báo Cáo (Management)
| Method | Endpoint | Yêu cầu quyền | Mô tả |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/management/dashboard/metrics`| MANAGER | Lấy số liệu KPI tổng quan cho Dashboard |
| `GET` | `/api/v1/management/reports/sales` | MANAGER | Báo cáo doanh thu theo ngày / tuần / tháng |
| `GET` | `/api/v1/management/audit-logs` | MANAGER | Xem lịch sử kiểm toán thao tác hệ thống |
| `GET` | `/api/v1/management/employees` | MANAGER | Lấy danh sách nhân sự |

---

## 🧪 Kiểm Thử Tự Động (Quality Gates)

### Backend Django Tests
Bộ kiểm thử tự động kiểm tra toàn diện luồng đăng nhập, tạo đơn, trừ kho ACID và bảo mật phân quyền:
```bash
cd backend_django
python manage.py test api
```
*(Kết quả: 5/5 tests passed — OK).*

### Frontend Type-Check & Build
Kiểm tra tính an toàn kiểu dữ liệu TypeScript và build bundle sản xuất:
```bash
cd frontend
npm run build
```
*(Kết quả: 0 lỗi TypeScript, 0 lỗi Vite build).*
