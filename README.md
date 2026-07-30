# 💧 Water Reminder Bot

Chatbot Discord nhắc người yêu uống nước, hỏi thăm sức khỏe, lưu lịch sử và vẽ biểu đồ thống kê.

## 📁 Cấu trúc project

```
water-reminder-bot/
├── bot.py           # File chính, chạy bot
├── database.py       # Xử lý lưu trữ dữ liệu (SQLite)
├── messages.py        # Kho tin nhắn nhắc nhở / hỏi thăm / khen
├── requirements.txt   # Danh sách thư viện cần cài
├── .env.example       # Mẫu file cấu hình
└── README.md
```

## 🚀 Bước 1: Tạo Discord Bot

1. Vào https://discord.com/developers/applications → **New Application** → đặt tên bất kỳ (VD: "Water Reminder")
2. Vào tab **Bot** (menu bên trái) → **Reset Token** → copy token này lại (chỉ hiện 1 lần, mất phải reset lại)
3. Trong tab **Bot**, kéo xuống mục **Privileged Gateway Intents** → **không cần bật gì** thêm (bot này không đọc nội dung tin nhắn)
4. Vào tab **OAuth2 → URL Generator**:
   - Ở mục **Scopes**: tick `bot` và `applications.commands`
   - Ở mục **Bot Permissions**: tick `Send Messages`, `Embed Links`, `Attach Files`, `Use Slash Commands`
   - Copy URL được sinh ra ở cuối trang, dán vào trình duyệt, chọn server của bạn để mời bot vào

## 🚀 Bước 2: Lấy Channel ID và User ID

1. Vào Discord → **Cài đặt người dùng → Nâng cao → bật "Chế độ nhà phát triển" (Developer Mode)**
2. Chuột phải vào kênh muốn bot gửi tin nhắn → **Copy Channel ID**
3. Chuột phải vào avatar người yêu bạn → **Copy User ID**

## 🚀 Bước 3: Cài đặt project

```bash
# Cài thư viện
pip install -r requirements.txt

# Tạo file cấu hình từ mẫu
cp .env.example .env
```

Mở file `.env` vừa tạo, điền:
- `DISCORD_TOKEN`: token lấy ở Bước 1
- `CHANNEL_ID`: channel ID lấy ở Bước 2
- `REMINDER_TIMES`: tùy chỉnh giờ nhắc nếu muốn (mặc định đã có sẵn 6 mốc/ngày)

## 🚀 Bước 4: Chạy bot

```bash
python bot.py
```

Nếu thấy log `Bot đã sẵn sàng: <tên bot>#xxxx` là thành công! Bot đã chạy, nhưng **chưa nhắc ai cả** cho tới khi có người `/dangky` (xem bên dưới).

## 🎮 Các lệnh có sẵn (slash commands)

| Lệnh | Chức năng |
|---|---|
| `/dangky` | Đăng ký nhận nhắc nhở uống nước - **bắt buộc làm trước tiên** |
| `/huy` | Ngừng nhận nhắc nhở (lịch sử uống nước vẫn được giữ) |
| `/uong` | Ghi nhận thủ công 1 lần đã uống nước (không cần đợi bot nhắc) |
| `/homnay` | Xem đã uống nước bao nhiêu lần trong hôm nay |
| `/thongke` | Vẽ biểu đồ số lần uống nước 7 ngày gần nhất |
| `/test` | Gửi thử tin nhắn nhắc nhở ngay lập tức, không cần đợi tới giờ |

Khi bot gửi tin nhắn nhắc nhở, sẽ có 2 nút **✅ Đã uống** / **⏳ Chưa uống** để bấm trực tiếp.

**Mô hình nhiều người dùng chung 1 bot**: bot này hỗ trợ nhiều người cùng đăng ký trong 1 kênh (VD: bạn dùng trước, sau này mời người yêu vào server, họ chỉ cần tự gõ `/dangky` là được nhắc nhở luôn — không cần sửa code hay `.env` gì cả).

## ⚠️ Lưu ý về hosting

Bot này cần chạy **liên tục 24/7** (không dùng được hosting serverless như Vercel).
Gợi ý: deploy lên **Railway** (dễ nhất) hoặc **Oracle Cloud Free Tier** (free vĩnh viễn nhưng cần tự setup VPS).
Mình có thể hướng dẫn chi tiết bước deploy khi bạn code chạy ổn ở local rồi.

## 🔧 Troubleshooting nhanh

- **Lỗi "Improper token"**: token trong `.env` bị sai hoặc dính khoảng trắng thừa
- **Slash command không hiện trong Discord**: đợi vài phút để Discord đồng bộ, hoặc thử `Ctrl+R` reload Discord
- **Bot online nhưng không gửi tin nhắn nhắc nhở đúng giờ**: kiểm tra lại `TIMEZONE` và `REMINDER_TIMES` trong `.env`, đảm bảo giờ hệ thống server đúng

Loading(test)