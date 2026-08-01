# 💧 Stay Hydrated! — Tài liệu dự án

**Loại dự án:** Discord Bot nhắc uống nước, theo dõi thói quen, thống kê dữ liệu
**Ngôn ngữ:** Python 3.11
**Trạng thái:** Đang vận hành (Production)
**Nền tảng deploy:** Railway
**Cập nhật lần cuối:** 01/08/2026

---

## Mục lục

1. [Tổng quan](#1-tổng-quan)
2. [Kiến trúc hệ thống](#2-kiến-trúc-hệ-thống)
3. [Tech stack](#3-tech-stack)
4. [Cấu trúc thư mục](#4-cấu-trúc-thư-mục)
5. [Database schema](#5-database-schema)
6. [Danh sách Slash Commands](#6-danh-sách-slash-commands)
7. [Hệ thống phân quyền Admin](#7-hệ-thống-phân-quyền-admin)
8. [Chu kỳ nhắc nhở (Reminder Cycle)](#8-chu-kỳ-nhắc-nhở-reminder-cycle)
9. [Tin nhắn tùy chỉnh (Custom Messages)](#9-tin-nhắn-tùy-chỉnh-custom-messages)
10. [Fun Facts qua Gemini API](#10-fun-facts-qua-gemini-api)
11. [Biến môi trường](#11-biến-môi-trường)
12. [Hướng dẫn cài đặt & chạy local](#12-hướng-dẫn-cài-đặt--chạy-local)
13. [Hướng dẫn deploy lên Railway](#13-hướng-dẫn-deploy-lên-railway)
14. [Vận hành & bảo trì](#14-vận-hành--bảo-trì)
15. [Xử lý sự cố thường gặp](#15-xử-lý-sự-cố-thường-gặp)
16. [Lịch sử phát triển (Changelog)](#16-lịch-sử-phát-triển-changelog)
17. [Hướng phát triển tiếp theo](#17-hướng-phát-triển-tiếp-theo)

---

## 1. Tổng quan

**Stay Hydrated!** là 1 Discord bot giúp nhắc nhở người dùng uống nước đều đặn trong ngày, theo dõi thói quen qua streak, và tạo cảm giác được quan tâm qua tin nhắn đa dạng + fact vui.

### Tính năng chính

- Gửi tin nhắn nhắc nhở theo lịch cố định, kèm câu hỏi thăm sức khỏe xen kẽ
- Nút bấm tương tác (✅ Đã uống / ⏳ Chưa uống)
- **Chu kỳ nhắc lại thông minh** theo 2 nhánh (chưa bấm nút / đã bấm "chưa uống"), tự dừng sau giờ quy định mỗi tối
- Theo dõi streak — chuỗi ngày uống nước liên tục
- Vẽ biểu đồ thống kê 7 ngày gần nhất
- Xuất dữ liệu thô ra CSV qua Discord
- Hỗ trợ nhiều người dùng cùng lúc (`/dangky`)
- **Phân quyền Admin riêng của bot**, độc lập với role Discord, không lộ ra ngoài
- **Tin nhắn tùy chỉnh** — admin có thể thêm tin nhắn của riêng mình, gộp cùng bộ tin nhắn có sẵn
- **Fun facts về uống nước** 4 lần/ngày, sinh động qua Gemini API (có fallback tĩnh)
- Tự động đăng hướng dẫn sử dụng và thông báo cập nhật vào kênh Discord

---

## 2. Kiến trúc hệ thống

```
┌──────────────────────┐
│   Discord Gateway      │
└───────────┬───────────┘
            │
┌───────────▼───────────┐
│   bot.py (discord.py)  │  ← Command, event, view, chu kỳ nhắc
└───────────┬───────────┘
            │
     ┌──────┴──────────────┐
     │                      │
┌────▼─────────┐    ┌───────▼──────┐
│  Scheduler     │    │ database.py   │  ← SQLAlchemy ORM
│  APScheduler    │    └───────┬──────┘
│  (persistent    │            │
│   job store)     │    ┌───────▼────────┐
└────┬─────────────┘    │ SQLite (Volume) │  ← Dùng CHUNG 1 file cho cả
     │                   └────────────────┘     dữ liệu app LẪN lịch nhắc
     │
┌────▼─────────┐
│ Gemini API     │  ← Sinh fact động, fallback về danh sách tĩnh nếu lỗi
│ (tùy chọn)      │
└────────────────┘
```

**Điểm quan trọng**: Scheduler dùng `SQLAlchemyJobStore` trỏ vào **cùng file SQLite** với dữ liệu chính (`DATABASE_PATH`). Nhờ vậy, mọi lịch nhắc đang dở (kể cả chu kỳ nhắc lại) đều **sống sót qua các lần bot restart** (deploy code mới, Railway khởi động lại,...) mà không cần code thêm cơ chế lưu trạng thái riêng.

---

## 3. Tech stack

| Thành phần | Công nghệ | Lý do lựa chọn |
|---|---|---|
| Ngôn ngữ | Python 3.11 | |
| Bot framework | `discord.py` | Hỗ trợ đầy đủ slash command + UI component |
| Scheduler | `APScheduler` (AsyncIOScheduler + SQLAlchemyJobStore) | Cron theo timezone, **persistent job store** để sống sót qua restart |
| Database | SQLite + `SQLAlchemy` ORM | Nhẹ, đủ dùng cho quy mô nhỏ |
| Vẽ biểu đồ | `matplotlib` | |
| Xuất dữ liệu | `csv` (built-in) | |
| Sinh fact động | `google-genai` (Gemini API) | Có gói miễn phí hào phóng ở quy mô nhỏ, fallback tĩnh nếu lỗi |
| Config | `python-dotenv` | |
| Hosting | Railway | Worker process 24/7 + Volume lưu trữ bền vững |
| CI/CD | GitHub → Railway auto-deploy | |

---

## 4. Cấu trúc thư mục

```
water-reminder-bot/
├── bot.py                # Entry point - command, scheduler, chu kỳ nhắc, view
├── database.py            # Model + CRUD (users, water_logs, custom_messages, mood_checkins)
├── messages.py              # Kho tin nhắn (nhắc nhở, khen, hỏi thăm, nhắc lại, fact tĩnh)
├── requirements.txt          # Thư viện Python
├── .env.example                # Mẫu cấu hình
├── .env                         # Cấu hình thật (KHÔNG commit)
├── .gitignore                    # Loại trừ .env, venv/, __pycache__/, *.db
├── Procfile                        # Lệnh chạy cho Railway
├── README.md                        # Hướng dẫn setup nhanh
└── DOCUMENTATION.md                   # Tài liệu này
```

---

## 5. Database schema

Engine: SQLite, đường dẫn qua `DATABASE_PATH`. Dùng chung file với **APScheduler job store** (bảng `apscheduler_jobs` tự động được thư viện tạo, không cần quản lý thủ công).

### `users`
| Cột | Kiểu | Mô tả |
|---|---|---|
| `id` | String (PK) | Discord user ID |
| `display_name` | String, nullable | |
| `is_active` | Integer | 1 = đang nhận nhắc nhở |

### `water_logs`
| Cột | Kiểu | Mô tả |
|---|---|---|
| `id` | Integer (PK) | |
| `user_id` | String | |
| `timestamp` | DateTime | Lưu dạng **UTC** |

### `custom_messages`
| Cột | Kiểu | Mô tả |
|---|---|---|
| `id` | Integer (PK) | Dùng để xóa qua `/xoatinnhan` |
| `category` | String | `reminder` / `health` / `praise` / `nudge` / `followup` |
| `content` | String | Nội dung tin nhắn |
| `added_by` | String, nullable | Discord user ID admin đã thêm |

### `mood_checkins`
| Cột | Kiểu | Mô tả |
|---|---|---|
| `id` | Integer (PK) | |
| `user_id` | String | |
| `timestamp` | DateTime | |
| `note` | String, nullable | Dự phòng, chưa có command sử dụng |

### Quy ước về thời gian

Toàn bộ timestamp lưu **UTC**. Mọi phép tính "hôm nay" (streak, thống kê, log hiển thị, lịch nhắc) đều quy đổi qua hàm nội bộ `_vn_now()`/`_vn_today()` (database.py) và `vn_now()` (bot.py) — dựa trên `datetime.utcnow() + 7 giờ`, **không** dùng `datetime.now()`/`date.today()` trực tiếp vì phụ thuộc múi giờ hệ điều hành server.

---

## 6. Danh sách Slash Commands

| Lệnh | Quyền | Mô tả |
|---|---|---|
| `/dangky` | Mọi người | Đăng ký nhận nhắc nhở — bắt buộc trước tiên |
| `/huy` | Mọi người | Ngừng nhận nhắc nhở |
| `/uong` | Mọi người | Ghi nhận thủ công 1 lần uống nước |
| `/homnay` | Mọi người | Số lần uống hôm nay + streak |
| `/streak` | Mọi người | Chuỗi ngày uống nước liên tục |
| `/thongke` | Mọi người | Biểu đồ 7 ngày gần nhất |
| `/xuatdata` | Mọi người | Xuất CSV (`water_logs.csv`, `users.csv`) |
| `/huongdan` | Mọi người | Đăng hướng dẫn sử dụng vào kênh hiện tại |
| `/test` | Mọi người | [Debug] Gửi thử reminder ngay lập tức |
| `/testfact` | Mọi người | [Debug] Gửi thử 1 fact ngay lập tức |
| `/thongbao` | **Admin** | Đăng thông báo cập nhật, tự tag người đã đăng ký |
| `/themtinnhan` | **Admin** | Thêm tin nhắn tùy chỉnh (chọn loại qua dropdown) |
| `/xemtinnhan` | **Admin** | Xem danh sách tin nhắn (mặc định + tùy chỉnh) theo loại |
| `/xoatinnhan` | **Admin** | Xóa 1 tin nhắn tùy chỉnh theo ID |

### Tương tác qua nút bấm

Mỗi tin nhắn nhắc nhở kèm 2 nút:
- **✅ Đã uống** — log nước, hủy mọi chu kỳ nhắc đang chờ, phản hồi riêng kèm streak
- **⏳ Chưa uống** — chuyển sang chuỗi "kiểm tra đã uống chưa" (xem mục 8)

Chỉ người đã `/dangky` mới bấm được nút.

---

## 7. Hệ thống phân quyền Admin

Bot dùng **danh sách admin riêng** (`ADMIN_USER_IDS`), **không** dùng quyền "Administrator" của Discord server.

**Lý do thiết kế này**: quyền Admin theo role Discord sẽ hiển thị công khai (ai cũng thấy được role/badge trong danh sách thành viên). Với `ADMIN_USER_IDS` khai báo riêng trong biến môi trường, chỉ bot mới biết ai là admin — không lộ ra giao diện Discord, và 1 người có thể **vừa là admin, vừa dùng bot như user thường** (gõ `/dangky`, `/uong`,...) mà không xung đột, vì đây là 2 tầng kiểm tra độc lập.

Kiểm tra qua hàm `is_admin(user_id)` trong `bot.py`, áp dụng cho: `/thongbao`, `/themtinnhan`, `/xemtinnhan`, `/xoatinnhan`.

---

## 8. Chu kỳ nhắc nhở (Reminder Cycle)

### Sơ đồ logic

```
Reminder chính gửi ra (theo REMINDER_TIMES)
        │
        ▼
  [Chưa bấm nút gì cả]
        │
   Sau BUTTON_REMINDER_INTERVAL phút vẫn im lặng?
        │
   Nhắc lại (tối đa BUTTON_REMINDER_MAX lần) ──► vẫn im lặng ──► BỎ QUA
        │
        ▼ (bấm nút bất kỳ lúc nào)
   ┌─────────────────┐
   │ ✅ Đã uống         │──► Hủy chu kỳ, kết thúc
   └─────────────────┘
   ┌─────────────────┐
   │ ⏳ Chưa uống        │──► Gửi ngay lời nhắc uống nước
   └─────────────────┘         │
                          Sau DRINK_CONFIRM_INTERVAL phút, hỏi lại "uống chưa?"
                                │
                         Lặp tối đa DRINK_CONFIRM_MAX lần ──► vẫn chưa ──► BỎ QUA
```

**Giờ im lặng (`QUIET_HOUR`, mặc định 22:30)**: mọi bước gửi tin (reminder chính, cả 2 chuỗi nhắc lại) đều tự kiểm tra giờ hiện tại trước khi gửi — nếu đã qua giờ này thì dừng hẳn, không nhắc thêm trong ngày. Giờ im lặng chỉ áp dụng **trong ngày hôm đó** (từ giờ quy định tới 23:59) — sang ngày mới sẽ không còn bị chặn, để không ảnh hưởng lịch nhắc buổi sáng hôm sau.

### Cơ chế kỹ thuật

Mỗi user chỉ có tối đa **1 job đang chờ tại 1 thời điểm** (ID dạng `cycle_{user_id}`). Khi bấm nút, job cũ bị hủy (`scheduler.remove_job`) và job mới được lên lịch thay thế — đảm bảo không bao giờ có 2 chuỗi nhắc chạy song song cho cùng 1 người.

---

## 9. Tin nhắn tùy chỉnh (Custom Messages)

Mỗi loại tin nhắn (`reminder`, `health`, `praise`, `nudge`, `followup`) có 1 danh sách **có sẵn** (viết cứng trong `messages.py`). Admin có thể **thêm** tin nhắn riêng qua `/themtinnhan` — được lưu vào bảng `custom_messages`, rồi **gộp chung** với danh sách có sẵn mỗi khi bot chọn ngẫu nhiên (hàm `_get_combined()` trong `messages.py`). Tin nhắn có sẵn không bao giờ bị mất hay ghi đè, chỉ được mở rộng thêm.

Chỉ admin mới thêm/xóa được (qua `/themtinnhan`, `/xoatinnhan`), tránh spam tin nhắn rác.

---

## 10. Fun Facts qua Gemini API

4 mốc giờ cố định (`FACTS_TIMES`, mặc định 07:00, 11:30, 15:00, 21:00), gửi 1 fact vui về uống nước vào kênh — **độc lập hoàn toàn** với lịch nhắc uống nước (không kèm nút bấm, không cần phản hồi).

**Cơ chế 2 lớp**:
1. Nếu có cấu hình `GEMINI_API_KEY`, bot gọi Gemini API (model `gemini-3.5-flash`) sinh 1 fact mới mỗi lần
2. Nếu **bất kỳ lỗi gì** xảy ra (chưa cấu hình key, sai key, mất mạng, hết quota,...) — bot tự động fallback về danh sách 8 fact tĩnh trong `messages.py` (`WATER_FACTS`), **không bao giờ** làm bot im lặng hay crash

Lấy API key miễn phí tại: https://aistudio.google.com/app/apikey

---

## 11. Biến môi trường

| Biến | Bắt buộc | Mặc định | Mô tả |
|---|---|---|---|
| `DISCORD_TOKEN` | ✅ | — | Token bot |
| `CHANNEL_ID` | ✅ | — | Kênh gửi nhắc nhở/fact |
| `ADMIN_USER_IDS` | Khuyến nghị | (rỗng) | Danh sách User ID admin, cách nhau dấu phẩy |
| `REMINDER_TIMES` | ❌ | `08:00,12:00,15:00,20:00` | Các mốc giờ nhắc chính |
| `BUTTON_REMINDER_INTERVAL_MINUTES` | ❌ | `15` | Phút giữa các lần nhắc khi chưa bấm nút |
| `BUTTON_REMINDER_MAX` | ❌ | `2` | Số lần nhắc lại tối đa (chuỗi "chưa bấm nút") |
| `DRINK_CONFIRM_INTERVAL_MINUTES` | ❌ | `5` | Phút giữa các lần hỏi lại sau khi bấm "Chưa uống" |
| `DRINK_CONFIRM_MAX` | ❌ | `2` | Số lần hỏi lại tối đa (chuỗi "chưa uống") |
| `QUIET_HOUR` | ❌ | `22:30` | Giờ bắt đầu ngừng nhắc trong ngày |
| `FACTS_TIMES` | ❌ | `07:00,11:30,15:00,21:00` | Các mốc giờ gửi fact |
| `GEMINI_API_KEY` | ❌ | (rỗng) | Để trống thì luôn dùng fact tĩnh |
| `TIMEZONE` | ❌ | `Asia/Ho_Chi_Minh` | Timezone cho scheduler |
| `DATABASE_PATH` | ❌ | `water_reminder.db` | Đường dẫn DB. Production trỏ Volume, VD `/data/water_reminder.db` |

---

## 12. Hướng dẫn cài đặt & chạy local

```bash
cd water-reminder-bot
python -m venv venv
venv\Scripts\Activate.ps1        # Windows PowerShell
pip install -r requirements.txt
copy .env.example .env           # Điền đủ biến bắt buộc
python bot.py
```

Chi tiết từng bước (lấy Token, mời bot vào server) xem `README.md`.

---

## 13. Hướng dẫn deploy lên Railway

1. Đẩy code lên GitHub (private khuyến nghị)
2. Railway → **New Project** → **Deploy from GitHub repo**
3. Tab **Variables** → khai báo đủ biến môi trường (mục 11)
4. Tạo **Volume**: `Ctrl+K` → "volume" → **Mount Path** = `/data`
5. Thêm `DATABASE_PATH=/data/water_reminder.db`
6. Theo dõi tab **Deployments** tới khi **Active**

Mỗi lần `git push` lên `main`, Railway tự động build & deploy lại — không cần thao tác thủ công.

---

## 14. Vận hành & bảo trì

### Cập nhật code
```bash
git add .
git commit -m "Mô tả thay đổi"
git push
```
Theo dõi **View Logs**, xác nhận dòng cuối `Bot đã sẵn sàng: ...` và đúng số lượng slash command đồng bộ (hiện tại: **14**).

### Xem dữ liệu thô (production)
```
/xuatdata
```
hoặc qua Railway CLI: `railway volume files download /water_reminder.db ./backup.db` (cần SSH key: `ssh-keygen -t ed25519` → `railway ssh keys add`)

### Thông báo cập nhật cho người dùng
```
/thongbao <mô tả cập nhật>
```

### Đăng lại hướng dẫn sử dụng
```
/huongdan
```

### ⚠️ Lưu ý khi sửa code liên quan tới scheduler

Vì dùng **persistent job store**, các hàm được lên lịch (`send_water_reminder`, `check_no_response`, `check_drink_confirm`, `send_water_fact`) được APScheduler lưu tham chiếu **theo tên hàm**. Nếu đổi tên các hàm này, job cũ đang lưu trong DB (nếu có) có thể lỗi khi bot load lại lúc restart. Nên tránh đổi tên hàm đã lên lịch, hoặc nếu bắt buộc đổi, chấp nhận mất job đang treo (không ảnh hưởng dữ liệu chính).

---

## 15. Xử lý sự cố thường gặp

| Triệu chứng | Nguyên nhân thường gặp | Cách xử lý |
|---|---|---|
| `RuntimeError: Chưa cấu hình DISCORD_TOKEN` | Thiếu biến môi trường trên Railway | Vào tab Variables, thêm đủ biến bắt buộc |
| Bot không phản hồi slash command | Chưa sync, hoặc Discord client cache cũ | Xem log; thử `Ctrl+R` hoặc restart Discord client |
| Dữ liệu mất sau khi deploy | Chưa gắn Volume, hoặc `DATABASE_PATH` sai | Kiểm tra Volume mount `/data`, biến `DATABASE_PATH` đúng |
| Log/dữ liệu lệch giờ | Server chạy múi giờ khác VN | Đã xử lý qua `_vn_now()`/`vn_now()`, không phụ thuộc server |
| `git` không nhận lệnh | Chưa cài Git, hoặc chưa mở lại terminal | Cài Git for Windows, mở terminal mới |
| `railway volume files download` lỗi SSH | Chưa có SSH key đăng ký | `ssh-keygen -t ed25519` → `railway ssh keys add` |
| Slash command bị đếm sai số lượng | File bị dán trùng lặp khi copy thủ công | Xóa sạch, dán lại 1 lần, đếm `@bot.tree.command` để xác nhận |
| `/thongbao`, `/themtinnhan`,... báo "chỉ dành cho admin" dù đúng là admin | `ADMIN_USER_IDS` chưa khai báo trên Railway, hoặc sai ID | Kiểm tra tab Variables, đối chiếu đúng User ID |
| Fact luôn chỉ ra 1 trong 8 câu cũ, không đổi mới | Gemini API lỗi hoặc chưa cấu hình key | Xem log tìm dòng `Gọi Gemini API lỗi...`, kiểm tra `GEMINI_API_KEY` |
| Bot vẫn nhắc sau giờ đã đặt `QUIET_HOUR` | Biến chưa được thêm trên Railway (đang dùng mặc định 22:30) | Kiểm tra tab Variables |

---

## 16. Lịch sử phát triển (Changelog)

### v1.0 — MVP
Nhắc theo giờ cố định, nút ✅/⏳, 1 người dùng cố định.

### v1.1 — Multi-user
`/dangky` / `/huy`, nhiều người dùng chung 1 bot.

### v1.2 — Deploy production
Railway + Volume lưu trữ bền vững, `DATABASE_PATH` tùy chỉnh.

### v1.3 — Streak & nhắc lại (bản đầu)
`get_streak()`, cơ chế nhắc lại đơn giản (1 lần duy nhất).

### v1.4 — Xuất dữ liệu
`/xuatdata` — CSV qua Discord.

### v1.5 — Sửa lỗi múi giờ
Toàn bộ phép tính ngày/giờ chuyển sang tính dựa trên UTC+7, không phụ thuộc server.

### v1.6 — Vận hành & tài liệu
`/huongdan`, `/thongbao`, tài liệu kỹ thuật đầy đủ đầu tiên.

### v2.0 — Nâng cấp lớn: Admin, Reminder Cycle, Custom Messages, Facts
- **Phân quyền Admin riêng** (`ADMIN_USER_IDS`), độc lập role Discord
- **Viết lại hoàn toàn logic nhắc nhở** thành chu kỳ 2 nhánh (chưa bấm nút / đã bấm chưa uống), giới hạn số lần lặp, có giờ im lặng (`QUIET_HOUR`)
- Scheduler chuyển sang **persistent job store** (APScheduler + SQLAlchemyJobStore) — sống sót qua bot restart
- **Custom messages**: admin thêm/xem/xóa tin nhắn tùy chỉnh (`/themtinnhan`, `/xemtinnhan`, `/xoatinnhan`), gộp với danh sách có sẵn
- **Fun facts** 4 lần/ngày qua Gemini API, có fallback tĩnh (`/testfact` để test nhanh)

---

## 17. Hướng phát triển tiếp theo

- **Mục tiêu số ly/ngày**: tự đặt mục tiêu, xem % hoàn thành
- **Mood check-in đầy đủ**: bảng `mood_checkins` đã có schema, chưa có command
- **Bảng xếp hạng (leaderboard)**: so sánh streak giữa người dùng
- **Nhắc nhở thông minh hơn**: học thói quen người dùng để tối ưu giờ nhắc

---

*Tài liệu này nên được cập nhật song song mỗi khi có thay đổi lớn về code hoặc kiến trúc.*
