# MIZA DataHub - Hệ Thống Truy Xuất Doanh Nghiệp
## Kế Hoạch Triển Khai & Estimate Thời Gian

**Ngày Soạn:** 2026-06-11  
**Phiên Bản:** v1.0  
**Trạng Thái:** Proposal

---

## 📋 MỤC LỤC
1. [Tổng Quan](#tổng-quan)
2. [Kiến Trúc Hệ Thống](#kiến-trúc-hệ-thống)
3. [Chi Tiết Công Nghệ](#chi-tiết-công-nghệ)
4. [Kế Hoạch Triển Khai](#kế-hoạch-triển-khai)
5. [Estimate Thời Gian & Công Việc](#estimate-thời-gian--công-việc)
6. [Nhân Lực & Vai Trò](#nhân-lực--vai-trò)

---

## 🎯 TỔNG QUAN

### Mục Đích
MIZA DataHub là một hệ thống truy xuất doanh nghiệp (Enterprise Traceability) toàn diện cho quy trình sản xuất giấy, giúp:
- ✅ Theo dõi nguyên liệu thô → sản phẩm hoàn thiện
- ✅ Quản lý chất lượng với truyền xuất đầy đủ
- ✅ Tối ưu hóa năng lượng và tài nguyên
- ✅ Tính toán OEE theo thời gian thực
- ✅ Phân tích nguyên nhân gốc rễ (Root Cause Analysis)

### Phạm Vi
| Thành Phần | Phạm Vi |
|-----------|---------|
| **Khách Hàng** | 1 khách hàng, 1-5 loại giấy, 1-3 máy sản xuất |
| **Dữ Liệu Lịch Sử** | 12 tháng dữ liệu thích nghi |
| **Cập Nhật Thời Gian Thực** | 1 phút/lần cho metrics |
| **Users** | 5-10 người dùng (QA, Production, Management) |

### Lợi Ích Kinh Tế
- Giảm phế phẩm: ~2-5% (qua RCA)
- Tối ưu năng lượng: ~8-12% (theo dashboard)
- Giảm downtime: ~5-10% (qua maintenance planning)
- Compliance: 100% truy xuất được nguyên liệu

---

## 🏗️ KIẾN TRÚC HỆ THỐNG

### Sơ Đồ Tổng Quát

```
┌─────────────────────────────────────────────────────────────┐
│                    MIZA DataHub                              │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐    │
│  │   PLC/IoT   │  │  Manual Data │  │  3rd Party API  │    │
│  │   Devices   │  │   Input      │  │  (ERP, Quality) │    │
│  └──────┬──────┘  └──────┬───────┘  └────────┬────────┘    │
│         │                │                   │              │
│         └────────────────┼───────────────────┘              │
│                          │                                   │
│                    ┌─────▼─────┐                             │
│                    │   Kafka   │  (Message Queue)            │
│                    └─────┬─────┘                             │
│         ┌──────────────┬─┴──────────────┬─────────────┐     │
│         │              │                │             │     │
│    ┌────▼───┐    ┌────▼───────┐   ┌───▼────┐  ┌────▼──┐   │
│    │PostgreSQL│   │ InfluxDB   │   │ Redis  │  │Cache  │   │
│    │(Business)│   │(Time-Series)│   │(Hot)   │  │(Warm) │   │
│    └────┬───┘    └────┬───────┘   └────────┘  └───────┘   │
│         │              │                                     │
│         └──────────────┼─────────────────────────────────┐  │
│                        │                                 │  │
│                   ┌────▼──────────┐                      │  │
│                   │   FastAPI     │  (Business Logic)    │  │
│                   │  + Traceability│                      │  │
│                   └────┬──────────┘                      │  │
│                        │                                 │  │
│         ┌──────────────┼──────────────────┐             │  │
│         │              │                  │             │  │
│    ┌────▼──────┐  ┌───▼────────┐  ┌─────▼──────┐      │  │
│    │ Grafana   │  │  Frontend  │  │ Mobile App │      │  │
│    │Dashboard  │  │  (React)   │  │ (React-NTV)│      │  │
│    └───────────┘  └────────────┘  └────────────┘      │  │
│                                                         │  │
│  ┌───────────────────────────────────────────────┐    │  │
│  │  DuckDB (Data Warehouse - Historical Analysis) │    │  │
│  └───────────────────────────────────────────────┘    │  │
│                                                         │  │
└─────────────────────────────────────────────────────────┘
```

### Luồng Dữ Liệu Chi Tiết

#### 1️⃣ **Ingestion Layer**
```
PLC/IoT Data (1min intervals)
    ↓
Kafka Topic: "production.events"
    ├→ PLC signals (speed, temp, pressure)
    ├→ Energy metrics (kWh, steam, water)
    └→ Maintenance events
```

#### 2️⃣ **Storage Layer**
- **PostgreSQL**: Entities kinh doanh (không thay đổi thường xuyên)
- **InfluxDB**: Metrics thời gian thực (lưu 30 ngày chi tiết, 1 năm downsampled)
- **Redis**: Cache OEE, quality aggregations (TTL: 1 giờ)
- **DuckDB**: Archive dữ liệu lịch sử cho phân tích

#### 3️⃣ **Processing Layer**
- **FastAPI**: Aggregation, calculation, business logic
- Python Batch Jobs: OEE computation, RCA analysis

#### 4️⃣ **Presentation Layer**
- **Grafana**: Real-time dashboards
- **React Frontend**: Traceability query UI
- **Mobile App**: Mobile notifications

---

## 💻 CHI TIẾT CÔNG NGHỆ

### 1. PostgreSQL - Dữ Liệu Nghiệp Vụ

#### Schema Chính
```sql
-- Khách hàng
CREATE TABLE customers (
    customer_id UUID PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    country VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Loại giấy
CREATE TABLE paper_grades (
    grade_id UUID PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    target_gsm FLOAT,
    target_burst FLOAT,
    target_moisture FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Đơn hàng sản xuất
CREATE TABLE production_orders (
    order_id UUID PRIMARY KEY,
    order_no VARCHAR(100) UNIQUE NOT NULL,
    customer_id UUID NOT NULL REFERENCES customers,
    grade_id UUID NOT NULL REFERENCES paper_grades,
    target_ton FLOAT NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_customer (customer_id),
    INDEX idx_order_no (order_no),
    INDEX idx_start_time (start_time)
);

-- Cuộn giấy lớn (JumboRoll)
CREATE TABLE jumbo_rolls (
    jumbo_id UUID PRIMARY KEY,
    order_id UUID NOT NULL REFERENCES production_orders,
    reel_code VARCHAR(100) UNIQUE NOT NULL,
    gsm_target FLOAT,
    gsm_actual FLOAT,
    deckle_width_mm FLOAT,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration_min FLOAT,
    downtime_min FLOAT,
    avg_machine_speed FLOAT,
    total_weight_kg FLOAT,
    created_at TIMESTAMP DEFAULT NOW(),
    PARTITION BY RANGE (YEAR(start_time)) (
        PARTITION p_2025 VALUES LESS THAN (2026),
        PARTITION p_2026 VALUES LESS THAN (2027),
        PARTITION p_2027 VALUES LESS THAN (2028)
    )
);

-- Cuộn giấy thành phẩm (FinishedRoll)
CREATE TABLE finished_rolls (
    roll_id UUID PRIMARY KEY,
    jumbo_id UUID NOT NULL REFERENCES jumbo_rolls,
    roll_code VARCHAR(100) UNIQUE NOT NULL,
    width_mm FLOAT,
    length_m FLOAT,
    weight_kg FLOAT,
    quality_grade VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_jumbo_id (jumbo_id)
);

-- Kết quả chất lượng
CREATE TABLE quality_results (
    result_id UUID PRIMARY KEY,
    roll_id UUID NOT NULL REFERENCES finished_rolls,
    gsm FLOAT,
    burst_strength FLOAT,
    smoothness FLOAT,
    cobb FLOAT,
    moisture FLOAT,
    color_l FLOAT,
    color_a FLOAT,
    color_b FLOAT,
    is_pass BOOLEAN,
    tested_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_roll_id (roll_id),
    INDEX idx_tested_at (tested_at)
);

-- Khiếm khuyết chất lượng
CREATE TABLE quality_defects (
    defect_id UUID PRIMARY KEY,
    result_id UUID REFERENCES quality_results,
    code VARCHAR(50),
    name VARCHAR(200),
    severity VARCHAR(50),
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Thiết bị
CREATE TABLE equipment (
    equipment_id UUID PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    area VARCHAR(100),
    type VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Bảo trì
CREATE TABLE maintenance_records (
    maintenance_id UUID PRIMARY KEY,
    equipment_id UUID NOT NULL REFERENCES equipment,
    work_order VARCHAR(100),
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    type VARCHAR(100),
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_equipment_id (equipment_id),
    INDEX idx_start_time (start_time)
);

-- Tính toán OEE
CREATE TABLE oee_records (
    oee_id UUID PRIMARY KEY,
    jumbo_id UUID NOT NULL REFERENCES jumbo_rolls,
    equipment_id UUID NOT NULL REFERENCES equipment,
    availability FLOAT,
    performance FLOAT,
    quality FLOAT,
    oee FLOAT,
    calculated_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_equipment_id (equipment_id),
    INDEX idx_calculated_at (calculated_at)
);

-- Tiêu thụ bột giấy
CREATE TABLE pulp_consumption (
    pulp_id UUID PRIMARY KEY,
    jumbo_id UUID NOT NULL REFERENCES jumbo_rolls,
    long_fiber_kg FLOAT,
    short_fiber_kg FLOAT,
    middle_fiber_kg FLOAT,
    ukp_fiber_kg FLOAT,
    broke_kg FLOAT,
    total_fiber_kg FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### Cấu Hình & Best Practices
- **Backup**: Daily incremental, weekly full
- **Replication**: Master-Slave (disaster recovery)
- **Monitoring**: Slow query log, connection pooling (PgBouncer)
- **Performance**: Connection pool size = 20-50

---

### 2. InfluxDB - Time-Series Data

#### Cấu Hình
```yaml
# influxdb-config.yml
databases:
  - miza_production
  
retention_policies:
  - name: "15days_1min"
    duration: "15d"
    replication: 1
    default: true
  - name: "1year_1hour"
    duration: "365d"
    replication: 1
  - name: "5years_1day"
    duration: "1825d"
    replication: 1
```

#### Measurement Schema
```
measurement: plc_signals
tags:
  - equipment_id (indexed)
  - production_order
  - paper_grade
  - area
fields:
  - machine_speed (float, RPM)
  - temperature (float, °C)
  - pressure (float, bar)
  - humidity (float, %)
timestamp: (unix nanoseconds)

measurement: energy_consumption
tags:
  - equipment_id
  - production_order
fields:
  - electricity_kwh (float)
  - steam_ton (float)
  - water_m3 (float)
  - compressed_air_nm3 (float)
timestamp: (unix nanoseconds)

measurement: production_events
tags:
  - equipment_id
  - event_type (startup, shutdown, alarm, maintenance)
  - severity (info, warning, critical)
fields:
  - duration_min (float)
  - root_cause (string)
timestamp: (unix nanoseconds)
```

#### Queries Tiêu Biểu
```sql
-- Năng lượng trung bình theo giờ
SELECT MEAN(electricity_kwh), MEAN(steam_ton) 
FROM energy_consumption 
WHERE time > now() - 7d 
GROUP BY time(1h), equipment_id

-- Downtime events
SELECT * FROM production_events 
WHERE severity = 'critical' 
  AND time > now() - 30d
  AND equipment_id = 'eq-001'
```

#### Cấu Hình & Best Practices
- **Write Consistency**: Quorum (3 nodes nếu cluster)
- **Compression**: Enabled (giảm 70-80% dung lượng)
- **Shard Duration**: 7 ngày
- **Data Directory**: SSD (minimum 500GB)

---

### 3. FastAPI - Business Logic

#### Cấu Trúc Project
```
fastapi-app/
├── main.py                 # Entry point
├── requirements.txt
├── .env                   # Config
├── app/
│   ├── __init__.py
│   ├── api/
│   │   ├── v1/
│   │   │   ├── traceability.py    # Truy xuất nguồn gốc
│   │   │   ├── quality.py          # Chất lượng
│   │   │   ├── oee.py              # OEE calculation
│   │   │   ├── energy.py           # Năng lượng
│   │   │   └── maintenance.py      # Bảo trì
│   │   └── health.py               # Health check
│   ├── db/
│   │   ├── postgres.py             # PostgreSQL connection
│   │   ├── influxdb.py             # InfluxDB client
│   │   └── redis_cache.py          # Redis cache
│   ├── models/
│   │   ├── traceability.py
│   │   ├── quality.py
│   │   └── oee.py
│   ├── services/
│   │   ├── traceability_service.py
│   │   ├── oee_service.py
│   │   ├── rca_service.py
│   │   └── energy_service.py
│   ├── utils/
│   │   ├── logger.py
│   │   └── helpers.py
│   └── middleware/
│       ├── auth.py
│       └── logging.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── conftest.py
└── docker/
    └── Dockerfile
```

#### API Endpoints

| Endpoint | Method | Mô Tả | Response Time |
|----------|--------|-------|-----------------|
| `/api/v1/traceability/{jumbo_id}` | GET | Lấy toàn bộ truy xuất | <500ms |
| `/api/v1/quality/defects` | GET | Danh sách khiếm khuyết | <1s |
| `/api/v1/quality/rca?defect_id=` | POST | RCA analysis | <2s |
| `/api/v1/oee/{equipment_id}` | GET | OEE metrics | <500ms |
| `/api/v1/energy/consumption` | GET | Năng lượng tiêu thụ | <1s |
| `/api/v1/maintenance/schedule` | GET | Lịch bảo trì | <500ms |
| `/api/v1/production-orders` | GET | Danh sách đơn hàng | <1s |

#### Sample Endpoint Code
```python
# app/api/v1/traceability.py
from fastapi import APIRouter, Query, HTTPException
from app.services.traceability_service import TraceabilityService

router = APIRouter()

@router.get("/traceability/{jumbo_id}")
async def get_traceability(jumbo_id: str):
    """
    Lấy toàn bộ thông tin truy xuất của một cuộn giấy lớn
    Trả về: Customer → Order → JumboRoll → FinishedRolls → Quality
    """
    service = TraceabilityService()
    
    # 1. Lấy từ cache trước
    cached = await service.get_from_cache(jumbo_id)
    if cached:
        return cached
    
    # 2. Query từ PostgreSQL
    jumbo_data = await service.get_jumbo_roll(jumbo_id)
    if not jumbo_data:
        raise HTTPException(status_code=404, detail="Jumbo roll not found")
    
    # 3. Gather related data
    traceability = {
        "jumbo_roll": jumbo_data,
        "production_order": await service.get_order(jumbo_data.order_id),
        "customer": await service.get_customer(jumbo_data.order_id),
        "paper_grade": await service.get_paper_grade(jumbo_data.order_id),
        "finished_rolls": await service.get_finished_rolls(jumbo_id),
        "quality_results": await service.get_quality_results(jumbo_id),
        "pulp_consumption": await service.get_pulp_consumption(jumbo_id),
        "energy_consumption": await service.get_energy_consumption(jumbo_id),
        "oee_record": await service.get_oee_record(jumbo_id),
        "production_events": await service.get_production_events(jumbo_id)
    }
    
    # 4. Cache kết quả (30 phút)
    await service.cache_result(jumbo_id, traceability, ttl=1800)
    
    return traceability
```

#### Cấu Hình & Best Practices
- **Workers**: 4-8 (uvicorn)
- **Timeout**: 30 giây
- **Rate Limiting**: 100 requests/min per user
- **Authentication**: JWT tokens
- **Logging**: Structured logs (JSON format)

---

### 4. Grafana - Dashboards

#### Dashboard 1: OEE Dashboard
```
┌─────────────────────────────────────────┐
│  OEE - Overall Equipment Effectiveness  │
├─────────────────────────────────────────┤
│                                          │
│  ┌─────��──────┐  ┌────────────┐        │
│  │ Availability│  │ Performance│        │
│  │    92.5%   │  │    88.3%   │        │
│  └────────────┘  └────────────┘        │
│                                          │
│  ┌────────────┐  ┌────────────┐        │
│  │  Quality   │  │    OEE     │        │
│  │   94.2%    │  │   76.8%    │        │
│  └────────────┘  └────────────┘        │
│                                          │
│  OEE Trend (24h)                        │
│  ████████████████░░░░░░░░ 76.8%         │
│                                          │
│  Equipment Breakdown:                   │
│  ├─ Machine A: 78.5%                   │
│  ├─ Machine B: 75.2%                   │
│  └─ Machine C: 76.8%                   │
│                                          │
└─────────────────────────────────────────┘
```

#### Dashboard 2: Energy Dashboard
```
┌─────────────────────────────────────────┐
│    Energy & Resource Consumption        │
├─────────────────────────────────────────┤
│                                          │
│  Total Energy (24h): 2,847 kWh          │
│  Cost: $284.70                          │
│                                          │
│  Breakdown:                             │
│  • Electricity: 1,920 kWh (67.4%)       │
│  • Steam: 34.5 ton (45.8%)              │
│  • Water: 127.3 m³ (35.2%)              │
│  • Compressed Air: 89.2 Nm³ (12.1%)     │
│                                          │
│  Trend Graph (7 days)                   │
│  [Line chart showing daily consumption] │
│                                          │
│  Efficiency vs Production Volume        │
│  [Scatter plot: X=production ton, Y=kWh]│
│                                          │
└─────────────────────────────────────────┘
```

#### Dashboard 3: Quality Dashboard
```
┌─────────────────────────────────────────┐
│       Quality Performance (24h)         │
├─────────────────────────────────────────┤
│                                          │
│  Pass Rate: 94.2%                       │
│  Defect Rate: 5.8%                      │
│                                          │
│  Top Defects:                           │
│  1. Moisture: 2.1% (45 rolls)           │
│  2. Color: 1.5% (32 rolls)              │
│  3. Burst: 1.2% (26 rolls)              │
│  4. Others: 1.0% (22 rolls)             │
│                                          │
│  Quality by Paper Grade:                │
│  ├─ Grade A: 96.5% pass                 │
│  ├─ Grade B: 93.2% pass                 │
│  └─ Grade C: 91.8% pass                 │
│                                          │
│  Defect Trend (30 days)                 │
│  [Bar chart: daily defect rate]         │
│                                          │
└─────────────────────────────────────────┘
```

#### Dashboard 4: Maintenance Dashboard
```
┌─────────────────────────────────────────┐
│    Maintenance & Asset Performance      │
├─────────────────────────────────────────┤
│                                          │
│  Scheduled: 2 tasks (next 7 days)       │
│  Overdue: 0                             │
│  MTBF (Mean Time Between Failures):     │
│  ├─ Machine A: 720 hours (30 days)      │
│  ├─ Machine B: 650 hours (27 days)      │
│  └─ Machine C: 780 hours (32.5 days)    │
│                                          │
│  Maintenance History (90 days)          │
│  [Timeline: maintenance events]         │
│                                          │
│  Equipment Status:                      │
│  ├─ Machine A: ✅ Normal (100%)         │
│  ├─ Machine B: ⚠️ Aging (85%)           │
│  └─ Machine C: ✅ Normal (98%)          │
│                                          │
│  Downtime Analysis:                     │
│  [Pie chart: downtime by cause]         │
│                                          │
└──────────────────��──────────────────────┘
```

#### Cấu Hình Grafana
- **Data Sources**: PostgreSQL, InfluxDB
- **Refresh Interval**: 1 phút (real-time)
- **Alert Rules**: OEE < 70%, defect rate > 8%, energy spike > 20%
- **Notifications**: Email, Slack, Teams

---

### 5. Redis - Caching

#### Cache Strategy
```
Cache Key Pattern:
├── oee:{equipment_id}:{date} → OEE values (TTL: 1h)
├── quality:{roll_id}:defects → Quality defects (TTL: 30m)
├── energy:{equipment_id}:{hour} → Energy metrics (TTL: 2h)
├── traceability:{jumbo_id} → Full traceability (TTL: 30m)
└── rca:{defect_id}:analysis → RCA results (TTL: 24h)

Hit Rate Target: >85%
```

#### Redis Configuration
```conf
# redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

---

## 📅 KẾ HOẠCH TRIỂN KHAI

### Giai Đoạn 1: Chuẩn Bị (Week 1-2)

| Task | Mô Tả | Công Việc | Người Phụ Trách |
|------|-------|----------|-----------------|
| **1.1** | Cài đặt infrastructure | Docker, Kubernetes, networking | DevOps |
| **1.2** | Thiết kế schema PostgreSQL | DDL, indexes, partitions | DB Admin |
| **1.3** | Cấu hình InfluxDB | Retention, measurements, tags | DevOps |
| **1.4** | Setup Grafana & Redis | Installation, config files | DevOps |
| **1.5** | Viết tài liệu API | OpenAPI specs | Backend Lead |
| **1.6** | Team training | Architecture, tools, processes | Tech Lead |

### Giai Đoạn 2: Backend Development (Week 3-6)

| Task | Mô Tả | Công Việc | Người Phụ Trách |
|------|-------|----------|-----------------|
| **2.1** | FastAPI project setup | Poetry, dependencies, structure | Backend Lead |
| **2.2** | Database models & migrations | SQLAlchemy, Alembic | Backend Dev 1 |
| **2.3** | PostgreSQL CRUD operations | Customer, Order, Equipment, etc. | Backend Dev 1 |
| **2.4** | InfluxDB client & queries | Write/read operations | Backend Dev 2 |
| **2.5** | Core API endpoints (Traceability) | GET endpoints, caching | Backend Dev 1 |
| **2.6** | Quality & RCA endpoints | Quality analysis, RCA logic | Backend Dev 2 |
| **2.7** | OEE calculation service | OEE formula, aggregation | Backend Dev 2 |
| **2.8** | Energy & Maintenance endpoints | Energy tracking, maintenance | Backend Dev 1 |
| **2.9** | Authentication & authorization | JWT, role-based access | Backend Dev 2 |
| **2.10** | Unit tests (80% coverage) | Test suite | Backend Dev 1+2 |
| **2.11** | API documentation | Swagger/OpenAPI | Backend Lead |
| **2.12** | Performance optimization | Query optimization, caching tuning | Backend Lead |

### Giai Đoạn 3: Data Integration (Week 5-7)

| Task | Mô Tả | Công Việc | Người Phụ Trách |
|------|-------|----------|-----------------|
| **3.1** | Kafka consumer setup | PLC data ingestion | Data Engineer |
| **3.2** | Data transformation pipelines | ETL jobs for PostgreSQL | Data Engineer |
| **3.3** | InfluxDB write pipeline | Time-series data ingestion | Data Engineer |
| **3.4** | Data validation & cleansing | Quality checks | Data Engineer |
| **3.5** | Batch ETL jobs | Scheduled aggregations | Data Engineer |
| **3.6** | Data migration from legacy | Historical data import | Data Engineer |

### Giai Đoạn 4: Frontend & Visualization (Week 6-8)

| Task | Mô Tả | Công Việc | Người Phụ Trách |
|------|-------|----------|-----------------|
| **4.1** | Grafana dashboards setup | OEE, Energy, Quality, Maintenance | Data Analyst |
| **4.2** | Alert rules configuration | Critical alerts, notifications | Data Analyst |
| **4.3** | React frontend project | TypeScript, routing, state mgmt | Frontend Lead |
| **4.4** | Traceability query UI | Components, forms, visualization | Frontend Dev 1 |
| **4.5** | Quality analysis UI | Defect tracking, RCA display | Frontend Dev 2 |
| **4.6** | Dashboard components | Metrics, charts, real-time updates | Frontend Dev 1 |
| **4.7** | Authentication UI | Login, session management | Frontend Dev 2 |
| **4.8** | Mobile app setup | React Native scaffold | Mobile Dev |
| **4.9** | Integration tests | E2E testing | QA |

### Giai Đoạn 5: Testing & QA (Week 9-10)

| Task | Mô Tả | Công Việc | Người Phụ Trách |
|------|-------|----------|-----------------|
| **5.1** | Integration testing | API + DB + Cache integration | QA Engineer |
| **5.2** | Performance testing | Load testing, stress testing | QA Engineer |
| **5.3** | Security testing | Penetration testing, input validation | Security Team |
| **5.4** | UAT preparation | Test cases, data setup | QA Lead |
| **5.5** | Production readiness check | Monitoring, alerts, backup | DevOps |
| **5.6** | Documentation | User guides, troubleshooting | Tech Writer |

### Giai Đoạn 6: UAT & Launch (Week 11-13)

| Task | Mô Tả | Công Việc | Người Phụ Trách |
|------|-------|----------|-----------------|
| **6.1** | Client UAT execution | User acceptance testing | Client + QA |
| **6.2** | Bug fixes & refinement | UAT issue resolution | Backend + Frontend |
| **6.3** | Production deployment | Infrastructure setup, migration | DevOps |
| **6.4** | Staff training | End-user training | Training Team |
| **6.5** | Go-live support | Live monitoring, support | Support Team |
| **6.6** | Post-launch optimization | Monitoring, tuning, optimization | Tech Lead |

---

## ⏱️ ESTIMATE THỜI GIAN & CÔNG VIỆC

### Tóm Tắt Effort

| Giai Đoạn | Duration | Team Size | Total Person-Days |
|-----------|----------|-----------|-------------------|
| Phase 1: Prep | 2 weeks | 4 people | 40 |
| Phase 2: Backend | 4 weeks | 3 people | 60 |
| Phase 3: Data Integration | 3 weeks | 1 person | 15 |
| Phase 4: Frontend & UI | 3 weeks | 4 people | 60 |
| Phase 5: Testing | 2 weeks | 2 people | 20 |
| Phase 6: UAT & Launch | 3 weeks | 5 people | 75 |
| **TOTAL** | **13 weeks** | **Avg 3-4** | **270 days** |

### Chi Tiết Effort theo Task

#### Phase 1: Preparation & Setup (40 person-days)
```
1.1 Infrastructure Setup              4 days   (DevOps)
1.2 PostgreSQL Schema Design         3 days   (DB Admin)
1.3 InfluxDB Configuration           2 days   (DevOps)
1.4 Grafana & Redis Setup            3 days   (DevOps)
1.5 API Documentation                2 days   (Backend Lead)
1.6 Team Training                    2 days   (Tech Lead)
────────────────────────────────────────────
Total: 16 days (effective, parallel work: 40 days)
```

#### Phase 2: Backend Development (60 person-days)
```
2.1 FastAPI Project Setup             2 days   (Backend Lead)
2.2 Database Models & Migrations      5 days   (Backend Dev 1)
2.3 PostgreSQL CRUD Operations        8 days   (Backend Dev 1)
2.4 InfluxDB Client Development       6 days   (Backend Dev 2)
2.5 Traceability API Endpoints        10 days  (Backend Dev 1)
2.6 Quality & RCA Endpoints           10 days  (Backend Dev 2)
2.7 OEE Calculation Service           8 days   (Backend Dev 2)
2.8 Energy & Maintenance Endpoints    6 days   (Backend Dev 1)
2.9 Authentication & Authorization    6 days   (Backend Dev 2)
2.10 Unit Tests                       8 days   (Backend Dev 1+2)
2.11 API Documentation                3 days   (Backend Lead)
2.12 Performance Optimization         4 days   (Backend Lead)
────────────────────────────────────────────
Total: 76 days (effective: ~60 days with 3 developers)
```

#### Phase 3: Data Integration (15 person-days)
```
3.1 Kafka Consumer Setup              3 days   (Data Engineer)
3.2 ETL Pipelines (PostgreSQL)        5 days   (Data Engineer)
3.3 InfluxDB Write Pipeline           4 days   (Data Engineer)
3.4 Data Validation & Cleansing       2 days   (Data Engineer)
3.5 Batch ETL Jobs                    3 days   (Data Engineer)
3.6 Historical Data Migration         3 days   (Data Engineer)
────────────────────────────────────────────
Total: 20 days (effective: 15 days with 1 FTE)
```

#### Phase 4: Frontend & Visualization (60 person-days)
```
4.1 Grafana Dashboards               4 days   (Data Analyst)
4.2 Alert Rules Configuration        2 days   (Data Analyst)
4.3 React Frontend Setup             2 days   (Frontend Lead)
4.4 Traceability Query UI            12 days  (Frontend Dev 1)
4.5 Quality Analysis UI              10 days  (Frontend Dev 2)
4.6 Dashboard Components             12 days  (Frontend Dev 1)
4.7 Authentication UI                8 days   (Frontend Dev 2)
4.8 Mobile App Setup                 5 days   (Mobile Dev)
4.9 Integration Tests                5 days   (QA)
────────────────────────────────────────────
Total: 60 days
```

#### Phase 5: Testing & QA (20 person-days)
```
5.1 Integration Testing              6 days   (QA Engineer)
5.2 Performance Testing              4 days   (QA Engineer)
5.3 Security Testing                 2 days   (Security Team)
5.4 UAT Preparation                  4 days   (QA Lead)
5.5 Production Readiness Check       2 days   (DevOps)
5.6 Documentation                    2 days   (Tech Writer)
────────────────────────────────────────────
Total: 20 days
```

#### Phase 6: UAT & Launch (75 person-days)
```
6.1 Client UAT Execution            10 days  (Client + QA)
6.2 Bug Fixes & Refinement          15 days  (Dev Team)
6.3 Production Deployment            3 days  (DevOps)
6.4 Staff Training                   5 days  (Training Team)
6.5 Go-live Support                  2 days  (Support Team)
6.6 Post-launch Optimization         5 days  (Tech Lead)
────────────────────────────────────────────
Total: 40 days (effective: 75 with parallel UAT)
```

### Timeline Visualization

```
Week   1   2   3   4   5   6   7   8   9  10  11  12  13
Phase  |--|---|---|---|---|---|---|---|---|---|---|---|
  1    ▓▓
  2       ▓▓▓▓▓▓▓▓
  3        ▓▓▓▓▓▓▓
  4          ▓▓▓▓▓▓▓▓▓
  5              ▓▓▓▓▓▓
  6                 ▓▓▓▓▓▓▓

Legend: ▓ = Phase active
```

### Critical Path
```
Infrastructure → PostgreSQL → FastAPI Backend → Integration → Frontend → Testing → UAT → Go-Live

Duration: 13 weeks (with parallel work on some phases)
Buffer: 1-2 weeks recommended for unexpected issues
```

---

## 👥 NHÂN LỰC & VAI TRÒ

### Cơ Cấu Nhân Sự

| Vị Trí | Số Lượng | Responsibilities |
|--------|----------|------------------|
| **Tech Lead** | 1 | Architecture, decisions, performance tuning |
| **Backend Lead** | 1 | FastAPI setup, code review, optimization |
| **Backend Developer** | 2 | API development, database, business logic |
| **Frontend Lead** | 1 | React setup, UI/UX, component architecture |
| **Frontend Developer** | 2 | UI components, forms, charts |
| **Mobile Developer** | 1 | React Native app development |
| **Data Engineer** | 1 | ETL pipelines, data integration, Kafka |
| **Data Analyst** | 1 | Grafana dashboards, analysis, queries |
| **DevOps Engineer** | 1 | Infrastructure, deployment, monitoring |
| **DB Administrator** | 1 | PostgreSQL, InfluxDB, backup, performance |
| **QA Lead** | 1 | Test strategy, UAT management |
| **QA Engineer** | 1 | Test execution, bug reporting |
| **Security Team** | 1 | Security review, penetration testing |
| **Tech Writer** | 1 | Documentation, user guides |
| **Training Lead** | 1 | User training, support materials |
| **Product Owner** | 1 | Requirements, prioritization, stakeholder mgmt |
| **Scrum Master** | 1 | Process management, sprint planning |
| **Client Representative** | 1-2 | UAT participation, feedback |
| **Total** | **19-20** | |

### RACI Matrix

| Task | Tech Lead | Backend Lead | Data Engineer | DevOps | QA Lead |
|------|-----------|--------------|---------------|--------|---------|
| Architecture Design | **R/A** | C | C | C | - |
| Backend Development | C | **R/A** | - | - | - |
| Data Integration | C | - | **R/A** | C | - |
| Deployment | C | - | - | **R/A** | C |
| Testing & QA | C | C | C | C | **R/A** |
| UAT Coordination | C | - | - | - | **R/A** |

### Độc Lập Công Việc (Dependencies)

```
Infrastructure Setup ──┐
                       ├──→ Backend Development ──┐
PostgreSQL Schema ────┤                          ├──→ Integration Testing ──┐
                       └──→ Data Pipeline ────────┘                         ├──→ UAT ──→ Go-Live
InfluxDB Setup ────────┐                                                    │
                       ├──→ Frontend Development ─────────────────────────┘
Grafana Setup ────────┘
```

---

## 💼 RISKS & MITIGATION

### Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| **Data Quality Issues** | High | High | Data validation, cleansing, monitoring |
| **Performance Issues** | Medium | High | Load testing, query optimization, caching |
| **Integration Delays** | Medium | Medium | Early integration testing, phased rollout |
| **Skill Gap** | Medium | Medium | Training, knowledge sharing, consultation |
| **Scope Creep** | High | Medium | Strict change control, phased approach |
| **Legacy Data Migration** | Medium | High | Data profiling, mapping, pilot migration |
| **Infrastructure Failures** | Low | High | Redundancy, backup, disaster recovery plan |

---

## 📊 SUCCESS METRICS

### Phase Completion Criteria

| Phase | Success Criteria | Target |
|-------|-----------------|--------|
| **1** | All infrastructure deployed & tested | 100% |
| **2** | All APIs developed & 80% test coverage | 80%+ |
| **3** | Historical data migrated & validated | 100% |
| **4** | UI completed & responsive | 100% |
| **5** | 0 critical bugs, <10 medium bugs | Pass |
| **6** | Client approved & production deployed | Pass |

### Business Metrics

| Metric | Current | Target | Timeline |
|--------|---------|--------|----------|
| **Defect Reduction** | ~8% | ~3-5% | 3 months |
| **Energy Optimization** | Baseline | -8-12% | 3-6 months |
| **Downtime Reduction** | Baseline | -5-10% | 3-6 months |
| **Compliance Score** | ~70% | 100% | Immediate |
| **User Adoption Rate** | 0% | >80% | 1 month |

---

## 📝 APPROVAL & SIGN-OFF

### Stakeholders

| Role | Name | Signature | Date |
|------|------|-----------|------|
| CEO/Executive | _____________ | __________ | _____ |
| Client Representative | _____________ | __________ | _____ |
| Tech Lead | _____________ | __________ | _____ |
| Project Manager | _____________ | __________ | _____ |
| Finance Lead | _____________ | __________ | _____ |

---

## 📞 CONTACT & SUPPORT

**Project Manager:** [Name] - [Email] - [Phone]  
**Tech Lead:** [Name] - [Email] - [Phone]  
**Client Success Manager:** [Name] - [Email] - [Phone]

---

## 📎 APPENDIX

### A. Technology Stack Summary

| Layer | Technology | Version | Notes |
|-------|-----------|---------|-------|
| **Database** | PostgreSQL | 14.x | Primary business data |
| **Time-Series DB** | InfluxDB | 2.x | Metrics & events |
| **Cache** | Redis | 7.x | Session & query cache |
| **API** | FastAPI | 0.104+ | Python async framework |
| **Message Queue** | Kafka | 3.x | Data streaming |
| **Visualization** | Grafana | 10.x | Real-time dashboards |
| **Frontend** | React 18 | 18.x | TypeScript |
| **Mobile** | React Native | 0.72+ | Cross-platform |
| **Containerization** | Docker | 24.x | Container runtime |
| **Orchestration** | Kubernetes | 1.27+ | Container orchestration |

### B. Infrastructure Requirements

#### Development Environment
- 4 vCPU, 8GB RAM, 100GB SSD per developer machine

#### Staging Environment
- PostgreSQL: 8 vCPU, 16GB RAM, 500GB SSD
- InfluxDB: 8 vCPU, 32GB RAM, 1TB SSD
- Redis: 4 vCPU, 8GB RAM, 100GB SSD
- FastAPI: 4 vCPU, 8GB RAM (2 replicas)
- Grafana: 2 vCPU, 4GB RAM

#### Production Environment
- PostgreSQL: 16 vCPU, 64GB RAM, 2TB SSD (HA setup)
- InfluxDB: 16 vCPU, 64GB RAM, 5TB SSD (cluster)
- Redis: 8 vCPU, 32GB RAM, 500GB SSD (Sentinel)
- FastAPI: 8 vCPU, 16GB RAM (4-6 replicas)
- Grafana: 4 vCPU, 8GB RAM (2 replicas)
- Kafka: 12 vCPU, 32GB RAM, 1TB SSD (3 brokers)

### C. Cost Estimation

| Component | Unit Cost | Quantity | Annual Cost |
|-----------|-----------|----------|-------------|
| **Cloud Infrastructure** | $/hour | Varies | $45,000-60,000 |
| **On-Premise Storage** | $500/TB | 10TB | $5,000 |
| **Software Licenses** | - | - | $3,000 (Grafana, etc.) |
| **Personnel** (13 weeks) | $150/hour | 19 people | ~$180,000 |
| **Training & Support** | - | - | $10,000 |
| **Total Implementation** | - | - | **~$245,000** |
| **Annual Maintenance** | - | - | **~$80,000** |

### D. Glossary

- **OEE**: Overall Equipment Effectiveness (Availability × Performance × Quality)
- **RCA**: Root Cause Analysis
- **ETL**: Extract, Transform, Load
- **MTBF**: Mean Time Between Failures
- **KPI**: Key Performance Indicator
- **SLA**: Service Level Agreement
- **UAT**: User Acceptance Testing
- **HA**: High Availability
- **ACID**: Atomicity, Consistency, Isolation, Durability

---

**Document Version:** 1.0  
**Last Updated:** 2026-06-11  
**Next Review:** 2026-07-11
