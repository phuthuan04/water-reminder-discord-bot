# 💧 Stay Hydrated! — Tài liệu dự án

**Loại dự án:** Discord Bot nhắc uống nước, theo dõi thói quen, thống kê dữ liệu
**Ngôn ngữ:** Python 3.11
**Trạng thái:** Đang vận hành (Production)
**Nền tảng deploy:** Railway
**Cập nhật lần cuối:** 30/07/2026

---

## Mục lục

1. [Tổng quan](#1-tổng-quan)
2. [Kiến trúc hệ thống](#2-kiến-trúc-hệ-thống)
3. [Tech stack](#3-tech-stack)
4. [Cấu trúc thư mục](#4-cấu-trúc-thư-mục)
5. [Database schema](#5-database-schema)
6. [Danh sách Slash Commands](#6-danh-sách-slash-commands)
7. [Biến môi trường](#7-biến-môi-trường)
8. [Hướng dẫn cài đặt & chạy local](#8-hướng-dẫn-cài-đặt--chạy-local)
9. [Hướng dẫn deploy lên Railway](#9-hướng-dẫn-deploy-lên-railway)
10. [Vận hành & bảo trì](#10-vận-hành--bảo-trì)
11. [Xử lý sự cố thường gặp](#11-xử-lý-sự-cố-thường-gặp)
12. [Lịch sử phát triển (Changelog)](#12-lịch-sử-phát-triển-changelog)
13. [Hướng phát triển tiếp theo](#13-hướng-phát-triển-tiếp-theo)

---

## 1. Tổng quan

**Stay Hydrated!** là 1 Discord bot giúp nhắc nhở người dùng uống nước đều đặn trong ngày, đồng thời theo dõi thói quen qua thời gian bằng streak (chuỗi ngày liên tục) và biểu đồ thống kê.

### Tính năng chính

- Gửi tin nhắn nhắc nhở uống nước theo lịch cố định trong ngày (có thể tùy chỉnh giờ)
- Bộ tin nhắn đa dạng, chọn ngẫu nhiên để tránh nhàm chán, kèm câu hỏi thăm sức khỏe xen kẽ
- Nút bấm tương tác trực tiếp (✅ Đã uống / ⏳ Chưa uống) ngay dưới tin nhắn
- Tự động nhắc lại nếu sau 1 khoảng thời gian vẫn chưa ghi nhận uống nước
- Theo dõi streak — chuỗi ngày uống nước liên tục
- Vẽ biểu đồ thống kê 7 ngày gần nhất
- Xuất toàn bộ dữ liệu thô ra file CSV
- Hỗ trợ nhiều người dùng cùng lúc (mô hình đăng ký `/dangky`), phù hợp dùng chung giữa các cặp đôi/nhóm nhỏ
- Tự động đăng hướng dẫn sử dụng và thông báo cập nhật vào kênh Discord

### Đối tượng sử dụng

Ban đầu thiết kế cho 1 người dùng cá nhân, sau đó mở rộng cho nhiều người dùng chung 1 server (ví dụ: cặp đôi cùng nhắc nhau uống nước).

---

## 2. Kiến trúc hệ thống

```
┌──────────────────────┐
│   Discord Gateway      │  ← Người dùng tương tác qua slash command + nút bấm
└───────────┬───────────┘
            │
┌───────────▼───────────┐
│   bot.py (discord.py)  │  ← Xử lý command, event, giao diện nút bấm
└───────────┬───────────┘
            │
     ┌──────┴──────┐
     │              │
┌────▼────┐   ┌─────▼──────┐
│Scheduler │   │ database.py │  ← SQLAlchemy ORM, thao tác SQLite
│APScheduler│  └─────┬──────┘
└──────────┘         │
              ┌───────▼────────┐
              │ SQLite (volume)│  ← Lưu trên Railway Volume, bền vững qua các lần deploy
              └────────────────┘
```

Bot được deploy dưới dạng **worker process** (không mở HTTP port), duy trì kết nối liên tục (persistent connection) tới Discord Gateway 24/7.

---

## 3. Tech stack

| Thành phần | Công nghệ | Lý do lựa chọn |
|---|---|---|
| Ngôn ngữ | Python 3.11 | Quen thuộc với dev, hệ sinh thái Discord bot mạnh |
| Bot framework | `discord.py` | Chuẩn, hỗ trợ đầy đủ slash command + UI component (nút bấm) |
| Scheduler | `APScheduler` (AsyncIOScheduler) | Đặt lịch nhắc nhở theo cron, hỗ trợ timezone tường minh |
| Database | SQLite + `SQLAlchemy` ORM | Nhẹ, không cần server riêng, đủ dùng cho quy mô nhỏ (vài chục người dùng) |
| Vẽ biểu đồ | `matplotlib` | Xuất ảnh PNG gửi trực tiếp qua Discord |
| Xuất dữ liệu | `csv` (built-in) | Không cần thêm dependency, tương thích Excel |
| Config | `python-dotenv` | Quản lý biến môi trường/bí mật tách biệt code |
| Hosting | Railway | Hỗ trợ worker process 24/7 + Volume lưu trữ bền vững, free tier đủ dùng |
| CI/CD | GitHub → Railway auto-deploy | Push code lên GitHub, Railway tự build & deploy lại |

---

## 4. Cấu trúc thư mục

```
water-reminder-bot/
├── bot.py                # Entry point - khởi tạo bot, xử lý command & scheduler
├── database.py            # Model dữ liệu (SQLAlchemy) + các hàm CRUD
├── messages.py             # Kho tin nhắn (nhắc nhở, khen, hỏi thăm, nhắc lại)
├── requirements.txt         # Danh sách thư viện Python
├── .env.example             # Mẫu file cấu hình biến môi trường
├── .env                     # Cấu hình thật (KHÔNG commit lên Git)
├── .gitignore                # Loại trừ .env, venv/, __pycache__/, *.db
├── Procfile                   # Khai báo lệnh chạy cho Railway
├── README.md                   # Hướng dẫn setup nhanh
└── DOCUMENTATION.md              # Tài liệu này
```

---

## 5. Database schema

Engine: SQLite, đường dẫn cấu hình qua biến `DATABASE_PATH` (mặc định `water_reminder.db`, production trỏ vào Railway Volume).

### Bảng `users`

| Cột | Kiểu | Mô tả |
|---|---|---|
| `id` | String (PK) | Discord user ID |
| `display_name` | String, nullable | Tên hiển thị Discord tại thời điểm đăng ký |
| `is_active` | Integer | `1` = đang nhận nhắc nhở, `0` = đã `/huy` |

### Bảng `water_logs`

| Cột | Kiểu | Mô tả |
|---|---|---|
| `id` | Integer (PK, autoincrement) | |
| `user_id` | String | Discord user ID |
| `timestamp` | DateTime | Thời điểm ghi nhận, lưu dạng **UTC** |

### Bảng `mood_checkins`

| Cột | Kiểu | Mô tả |
|---|---|---|
| `id` | Integer (PK, autoincrement) | |
| `user_id` | String | Discord user ID |
| `timestamp` | DateTime | Lưu dạng UTC |
| `note` | String, nullable | Ghi chú (tính năng dự phòng, hiện chưa có command sử dụng) |

### Quy ước quan trọng về thời gian

- **Toàn bộ timestamp lưu trong DB đều là giờ UTC** (`datetime.utcnow()`), không phụ thuộc múi giờ server.
- Mọi phép tính liên quan đến "ngày hôm nay" (streak, thống kê theo ngày, `/homnay`) đều quy đổi UTC → giờ Việt Nam (UTC+7) bằng hàm nội bộ `_vn_now()` / `_vn_today()` trong `database.py`, **không** dùng `datetime.now()` hay `date.today()` trực tiếp vì các hàm này phụ thuộc múi giờ hệ điều hành của server.

---

## 6. Danh sách Slash Commands

| Lệnh | Ai dùng được | Mô tả |
|---|---|---|
| `/dangky` | Mọi người | Đăng ký nhận nhắc nhở uống nước — **bắt buộc làm trước tiên** |
| `/huy` | Mọi người | Ngừng nhận nhắc nhở (lịch sử vẫn giữ nguyên) |
| `/uong` | Mọi người | Ghi nhận thủ công 1 lần uống nước |
| `/homnay` | Mọi người | Xem số lần uống nước hôm nay + streak hiện tại |
| `/streak` | Mọi người | Xem chuỗi ngày uống nước liên tục |
| `/thongke` | Mọi người | Vẽ biểu đồ uống nước 7 ngày gần nhất |
| `/xuatdata` | Mọi người | Xuất toàn bộ dữ liệu thô ra 2 file CSV (`water_logs.csv`, `users.csv`) |
| `/test` | Mọi người | [Debug] Gửi thử tin nhắn nhắc nhở ngay lập tức |
| `/huongdan` | Mọi người | Đăng hướng dẫn sử dụng bot vào kênh hiện tại |
| `/thongbao` | **Chỉ Admin server** | Đăng thông báo cập nhật mới, tự tag toàn bộ người đã đăng ký |

### Tương tác qua nút bấm

Mỗi tin nhắn nhắc nhở kèm 2 nút:
- **✅ Đã uống** — ghi log, phản hồi riêng (ephemeral) kèm số lần hôm nay + streak
- **⏳ Chưa uống** — phản hồi riêng, không ghi log

Chỉ người đã `/dangky` mới bấm được nút (kiểm tra qua `is_user_registered`).

---

## 7. Biến môi trường

Khai báo trong `.env` (local) hoặc tab **Variables** trên Railway (production).

| Biến | Bắt buộc | Mặc định | Mô tả |
|---|---|---|---|
| `DISCORD_TOKEN` | ✅ | — | Token bot, lấy từ Discord Developer Portal |
| `CHANNEL_ID` | ✅ | — | ID kênh Discord nơi bot gửi nhắc nhở |
| `REMINDER_TIMES` | ❌ | `08:00,12:00,15:00,20:00` | Các mốc giờ nhắc nhở trong ngày, cách nhau bởi dấu phẩy |
| `REMINDER_FOLLOWUP_MINUTES` | ❌ | `30` | Số phút chờ trước khi nhắc lại nếu chưa uống |
| `TIMEZONE` | ❌ | `Asia/Ho_Chi_Minh` | Timezone dùng cho scheduler (APScheduler) |
| `DATABASE_PATH` | ❌ | `water_reminder.db` | Đường dẫn file database. Production trỏ vào Volume, VD `/data/water_reminder.db` |

---

## 8. Hướng dẫn cài đặt & chạy local

```bash
# 1. Clone hoặc tải project về
cd water-reminder-bot

# 2. Tạo môi trường ảo
python -m venv venv
venv\Scripts\Activate.ps1        # Windows PowerShell
# hoặc: source venv/bin/activate  # macOS/Linux

# 3. Cài thư viện
pip install -r requirements.txt

# 4. Tạo file cấu hình
copy .env.example .env           # Windows
# hoặc: cp .env.example .env      # macOS/Linux
# Sau đó điền DISCORD_TOKEN và CHANNEL_ID vào .env

# 5. Chạy bot
python bot.py
```

Xem chi tiết từng bước (kể cả cách lấy Token, mời bot vào server) trong `README.md`.

---

## 9. Hướng dẫn deploy lên Railway

1. Đẩy code lên GitHub repository (private khuyến nghị)
2. Railway → **New Project** → **Deploy from GitHub repo** → chọn repo
3. Railway tự nhận diện Python qua `requirements.txt` + `Procfile`
4. Vào tab **Variables** → khai báo đầy đủ biến môi trường (mục 7), trừ `DATABASE_PATH` sẽ set sau khi tạo Volume
5. Tạo **Volume**: `Ctrl+K` → tìm "volume" → tạo mới → **Mount Path** = `/data`
6. Thêm biến `DATABASE_PATH=/data/water_reminder.db`
7. Railway tự động build & deploy. Theo dõi tab **Deployments** tới khi trạng thái **Active**

### Cơ chế CI/CD

Mỗi lần `git push` lên nhánh `main`, Railway tự động nhận webhook từ GitHub, build lại image, và deploy bản mới — không cần thao tác thủ công nào thêm trên Railway.

---

## 10. Vận hành & bảo trì

### Cách cập nhật code

```bash
# Sửa code local, test kỹ trước khi push
python bot.py   # test local

git add .
git commit -m "Mô tả thay đổi"
git push
```

Railway tự động build lại. Theo dõi tab **Deployments** → **View Logs** để xác nhận không lỗi, dòng cuối phải là `Bot đã sẵn sàng: ...`.

### Cách xem dữ liệu thô (production)

**Cách 1 — nhanh nhất, qua Discord:**
```
/xuatdata
```
Bot gửi trực tiếp 2 file CSV, mở bằng Excel hoặc Google Sheets.

**Cách 2 — qua Railway CLI (cho debug sâu):**
```bash
railway login
railway link
railway volume files download /water_reminder.db ./backup.db
```
Sau đó mở bằng **DB Browser for SQLite** để xem dạng bảng.

### Cách thông báo cập nhật cho người dùng

Sau khi deploy xong bản mới, admin server chạy:
```
/thongbao Đã thêm tính năng streak và nhắc lại tự động!
```
Bot tự động đăng thông báo formatted, tag toàn bộ người đã `/dangky`.

### Cách đăng lại hướng dẫn sử dụng

Trong kênh `#huong-dan` (hoặc bất kỳ kênh nào), chạy:
```
/huongdan
```

---

## 11. Xử lý sự cố thường gặp

| Triệu chứng | Nguyên nhân thường gặp | Cách xử lý |
|---|---|---|
| `RuntimeError: Chưa cấu hình DISCORD_TOKEN` | Thiếu biến môi trường trên Railway | Vào tab Variables, thêm đủ `DISCORD_TOKEN`, `CHANNEL_ID` |
| Bot không phản hồi slash command | Slash command chưa sync, hoặc bot đang crash loop | Xem log tab Deployments; đợi vài phút để Discord đồng bộ command |
| Dữ liệu mất sau khi deploy | Chưa gắn Volume, hoặc `DATABASE_PATH` chưa trỏ đúng | Kiểm tra Volume đã mount `/data`, biến `DATABASE_PATH=/data/water_reminder.db` |
| Log/dữ liệu bị lệch giờ | Server chạy ở múi giờ khác VN (thường là UTC) | Đã xử lý ở code (mục 5) — mọi phép tính ngày/giờ đều tự quy đổi qua `_vn_now()`, không phụ thuộc múi giờ server |
| `git` không nhận lệnh trong PowerShell | Chưa cài Git, hoặc cài xong chưa mở lại terminal | Cài Git for Windows, đóng terminal cũ, mở terminal mới |
| `railway volume files download` báo lỗi SSH | Chưa có SSH key đăng ký với Railway | `ssh-keygen -t ed25519` → `railway ssh keys add` |
| Slash command bị đếm sai số lượng khi sync | File `bot.py`/`database.py` bị dán trùng lặp nội dung khi copy thủ công | Xóa sạch nội dung file, dán lại 1 lần duy nhất, kiểm tra bằng cách đếm số `@bot.tree.command` trong file |

---

## 12. Lịch sử phát triển (Changelog)

### v1.0 — MVP
- Nhắc nhở theo giờ cố định, nút ✅/⏳
- Lưu log SQLite, 1 người dùng cố định (`TARGET_USER_ID`)

### v1.1 — Multi-user
- Chuyển sang mô hình đăng ký `/dangky` / `/huy`, hỗ trợ nhiều người dùng chung 1 kênh

### v1.2 — Deploy production
- Deploy lên Railway, gắn Volume lưu trữ bền vững
- Thêm `DATABASE_PATH` để hỗ trợ đường dẫn tùy chỉnh theo môi trường

### v1.3 — Streak & nhắc lại
- Thêm `get_streak()` — tính chuỗi ngày liên tục uống nước
- Thêm cơ chế tự động nhắc lại (`REMINDER_FOLLOWUP_MINUTES`) nếu chưa uống sau khoảng thời gian quy định
- Thêm lệnh `/streak`

### v1.4 — Xuất dữ liệu
- Thêm lệnh `/xuatdata`, xuất CSV trực tiếp qua Discord, không cần Railway CLI

### v1.5 — Sửa lỗi múi giờ
- Toàn bộ phép tính ngày/giờ (streak, thống kê, log hiển thị, lịch nhắc lại) chuyển sang tính dựa trên UTC + 7h, không phụ thuộc múi giờ hệ thống server

### v1.6 — Vận hành & tài liệu
- Thêm `/huongdan`, `/thongbao`
- Bổ sung tài liệu kỹ thuật đầy đủ (file này)

---

## 13. Hướng phát triển tiếp theo

Các ý tưởng đã được đề xuất, chưa triển khai:

- **Mục tiêu số ly/ngày**: cho phép người dùng tự đặt mục tiêu, xem % hoàn thành
- **Mood check-in đầy đủ**: bảng `mood_checkins` đã có sẵn schema nhưng chưa có command sử dụng
- **Bảng xếp hạng (leaderboard)**: so sánh streak giữa các người dùng trong server, tạo động lực
- **Nhắc nhở thông minh hơn**: học thói quen người dùng để điều chỉnh giờ nhắc tối ưu

---

*Tài liệu này nên được cập nhật song song mỗi khi có thay đổi lớn về code hoặc kiến trúc, để luôn phản ánh đúng trạng thái thực tế của dự án.*
