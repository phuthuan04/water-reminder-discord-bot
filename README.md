# 💧 Water Reminder Bot (Stay Hydrated!)

Chatbot Discord nhắc uống nước, hỏi thăm sức khỏe, theo dõi streak, gửi fact vui, và hỗ trợ nhiều người dùng chung 1 bot.

> 💌 **Chatbot này dành cho Khánh Đan, người yêu của anh.**
>
> Mong rằng nó sẽ phần nào nhắc nhở em uống nước đầy đủ hơn. Phải luôn giữ gìn sức khỏe đấy nhé. 
>
> Anh yêu em.
>
> — *phuthuan04*

## 📁 Cấu trúc project

```
water-reminder-bot/
├── bot.py           # File chính, chạy bot
├── database.py       # Xử lý lưu trữ dữ liệu (SQLite)
├── messages.py         # Kho tin nhắn nhắc nhở / hỏi thăm / khen / fact
├── requirements.txt     # Danh sách thư viện cần cài
├── .env.example           # Mẫu file cấu hình
├── Procfile                 # Lệnh chạy cho Railway
├── README.md                 # File này - hướng dẫn setup nhanh
└── DOCUMENTATION.md            # Tài liệu kỹ thuật đầy đủ (kiến trúc, schema, troubleshooting...)
```

## 🚀 Bước 1: Tạo Discord Bot

1. Vào https://discord.com/developers/applications → **New Application** → đặt tên bất kỳ (VD: "Water Reminder")
2. Vào tab **Bot** → **Reset Token** → copy token này lại (chỉ hiện 1 lần)
3. Trong tab **Bot**, mục **Privileged Gateway Intents** → **không cần bật gì** thêm
4. Vào tab **OAuth2 → URL Generator**:
   - **Scopes**: tick `bot` và `applications.commands`
   - **Bot Permissions**: tick `Send Messages`, `Embed Links`, `Attach Files`, `Use Slash Commands`
   - Copy URL sinh ra ở cuối trang, dán vào trình duyệt, chọn server để mời bot vào

## 🚀 Bước 2: Lấy Channel ID và User ID

1. Discord → **Cài đặt người dùng → Nâng cao → bật "Chế độ nhà phát triển"**
2. Chuột phải vào kênh muốn bot gửi tin nhắn → **Copy Channel ID**
3. Chuột phải vào avatar của bạn → **Copy User ID** (để làm admin, xem Bước 3)

## 🚀 Bước 3: Cài đặt project

```bash
pip install -r requirements.txt
cp .env.example .env      # macOS/Linux
copy .env.example .env    # Windows PowerShell
```

Mở file `.env`, điền các biến **bắt buộc**:
- `DISCORD_TOKEN` — token lấy ở Bước 1
- `CHANNEL_ID` — channel ID lấy ở Bước 2
- `ADMIN_USER_IDS` — User ID của bạn (từ Bước 2), để dùng các lệnh quản trị

Các biến còn lại đều có giá trị mặc định hợp lý, xem đầy đủ trong `.env.example` hoặc mục Biến môi trường trong `DOCUMENTATION.md`.

## 🚀 Bước 4: Chạy bot

```bash
python bot.py
```

Thấy log `Bot đã sẵn sàng: <tên bot>#xxxx` là thành công. Bot chưa nhắc ai cả cho tới khi có người gõ `/dangky`.

## 💬 Trò chuyện với bot

Tag `@Tên bot` kèm tin nhắn trong kênh để trò chuyện trực tiếp — bot sẽ đọc lịch sử chat gần đây (giữ riêng theo từng người) + dữ liệu uống nước thật (hôm nay, streak, 7 ngày) để trả lời có ngữ cảnh, đưa insight.

**Bot có thể tự ghi nhận uống nước qua chat** — chỉ cần nói kiểu "tôi vừa uống nước xong" là bot tự động log, không cần gõ `/uong` hay bấm nút.

Cần bật thêm quyền **Message Content Intent** trong Discord Developer Portal (xem `DOCUMENTATION.md` mục Trò chuyện qua @mention).

## 🎮 Danh sách lệnh (tóm tắt — xem đầy đủ trong DOCUMENTATION.md)

| Lệnh | Ai dùng | Mô tả |
|---|---|---|
| `/dangky` | Mọi người | Đăng ký nhận nhắc nhở — làm trước tiên |
| `/huy` | Mọi người | Ngừng nhận nhắc nhở |
| `/uong` | Mọi người | Ghi nhận thủ công 1 lần uống nước |
| `/homnay` | Mọi người | Xem số lần uống hôm nay + streak |
| `/streak` | Mọi người | Xem chuỗi ngày uống nước liên tục |
| `/thongke` | Mọi người | Biểu đồ 7 ngày gần nhất |
| `/xuatdata` | Mọi người | Xuất dữ liệu thô ra CSV |
| `/huongdan` | Mọi người | Đăng hướng dẫn sử dụng vào kênh |
| `/test`, `/testfact` | Mọi người | Test nhanh reminder/fact, không cần đợi tới giờ |
| `/thongbao` | **Admin** | Đăng thông báo cập nhật |
| `/themtinnhan`, `/xemtinnhan`, `/xoatinnhan` | **Admin** | Quản lý tin nhắn tùy chỉnh |

Khi bot nhắc nhở, có 2 nút **✅ Đã uống** / **⏳ Chưa uống**. Nếu không phản hồi, bot tự nhắc lại theo chu kỳ (xem `DOCUMENTATION.md` mục Reminder Cycle) cho tới 22h30 thì ngừng hẳn trong ngày.

## ⚠️ Lưu ý về hosting

Bot cần chạy **liên tục 24/7**, không dùng được hosting serverless. Xem hướng dẫn deploy Railway chi tiết trong `DOCUMENTATION.md`.

## 🔧 Troubleshooting nhanh

Xem bảng troubleshooting đầy đủ trong `DOCUMENTATION.md` — bao gồm các lỗi thực tế đã gặp: thiếu env var, mất dữ liệu khi redeploy, lệch múi giờ, SSH key Railway CLI, v.v.

## 📜 Lịch sử cập nhật

Toàn bộ thay đổi qua từng phiên bản, kèm ngày tháng cụ thể, được ghi lại tại mục **Changelog** trong `DOCUMENTATION.md`.
