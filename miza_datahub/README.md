## Miza DataHub Library

[![codecov](https://codecov.io/gh/chanelcolgate/miza-datahub/branch/develop/graph/badge.svg)](https://codecov.io/gh/chanelcolgate/miza-datahub)
### How to install
- Cài pip
```bash
pip install --upgrade pip setuptools wheel
```
- Cách khác
```bash
python -m ensurepip --upgrade
```
- Cách cài đặt và chạy
```
pyproject-build
python -m pip install -e .
```
- Cách test
```
python -m pip install pytest
python -m pytest
python -m pip install mypy
python -m mypy
python -m pip install tox
tox -e typecheck 
tox -e lint
tox -e py311 --recreate
```

## Use Alembic
1. Tạo revision Alembic

```
uv venv
source .venv/bin/activate
uv sync
cd miza_datahub
alembic init alembic
alembic revision -m "create daily production reports and downtime events hypertable"
```

2. Dán nội dung file migration vào `alembic/version/<revision>.py`

3. Chạy migration:
```
alembic upgrade head
```

Để biết chắc chắn rằng cơ sở dữ liệu (PostgreSQL) đã được liên kết thành công với Alembic hay chưa trước khi bạn chạy file migration trên, bạn có thể kiểm tra qua **3 cách** sau đây:

### 1. Kiểm tra biến kết nối trong file cấu hình (`alembic.ini` hoặc `env.py`)

Alembic biết phải đẩy dữ liệu vào database nào thông qua chuỗi kết nối (`sqlalchemy.url`).

* Mở file **`alembic.ini`** và tìm dòng:
```ini
sqlalchemy.url = postgresql+psycopg2://username:password@localhost:5432/miza_db

```


* Hoặc nếu dự án của bạn cấu hình lấy URL từ biến môi trường (`.env`) trong file `alembic/env.py`, hãy kiểm tra đoạn code gán `config.set_main_option('sqlalchemy.url', ...)` xem đã trỏ đúng đến database PostgreSQL của bạn chưa.

---

### 2. Dùng lệnh kiểm tra trạng thái của Alembic (`current` & `history`)

Trước khi chạy lệnh `upgrade head`, bạn có thể kiểm tra xem Alembic đã "nhìn thấy" kết nối tới database hay chưa bằng lệnh:

```bash
alembic current

```

* **Nếu đã liên kết thành công:** Nó sẽ in ra phiên bản (revision) hiện tại đang có trên database (hoặc báo `None` nếu database chưa chạy migration nào nhưng kết nối thành công).
* **Nếu chưa liên kết được (lỗi kết nối):** Nó sẽ văng ra lỗi `OperationalError` (ví dụ: `could not translate host name` hoặc `Connection refused`), chứng tỏ chuỗi kết nối hoặc thông tin tài khoản/mật khẩu/port bị sai.

Bạn cũng có thể xem lịch sử các migration bằng lệnh:

```bash
alembic history

```

---

### 3. Kiểm tra trực tiếp bằng công cụ quản lý Database (DBeaver, pgAdmin, hoặc psql)

Cách trực quan nhất để xác nhận việc liên kết và thực thi script migration thành công là kiểm tra trực tiếp trong PostgreSQL:

1. Mở công cụ quản lý database và kết nối vào database của bạn (ví dụ `miza_db`).
2. Kiểm tra xem có xuất hiện bảng lịch sử **`alembic_version`** hay không. Bảng này do Alembic tự động tạo ra để lưu mã revision hiện tại của database.
3. Kiểm tra các bảng đã được tạo đúng cấu trúc:
* **`equipment`**, **`paper_grades`**, **`crews`**, **`crew_schedules`**
* **`daily_production_reports`**
* **`downtime_events`** (Kiểm tra bảng đã được chuyển thành TimescaleDB Hypertable chưa bằng câu lệnh SQL: `SELECT * FROM timescaledb_information.hypertables;`).

### Production day and shifts

- Ngày sản xuất bắt đầu lúc `07:00` theo múi giờ `Asia/Ho_Chi_Minh`.
- Ca 1: `07:00-19:00`; Ca 2: `19:00-07:00` ngày hôm sau.
- `shift_no` là value object (`1` hoặc `2`); không còn bảng `production_shifts`.
- `daily_production_reports` unique theo `(report_date, shift_no, equipment_id)`.
- `downtime_events` tham chiếu `equipment_id`, không có `report_id`.

Dùng `miza_datahub.services.shift_calendar` thay vì hard-code `06:00` hoặc `6h`.

