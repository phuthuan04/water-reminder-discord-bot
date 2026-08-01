"""
database.py
Định nghĩa schema và các hàm thao tác dữ liệu (CRUD) cho bot.
Dùng SQLite + SQLAlchemy ORM - nhẹ, không cần cài server riêng.

Mô hình multi-user: bảng `users` lưu ai đã /dangky nhận nhắc nhở.
"""

import os
from datetime import datetime, date, timedelta
from sqlalchemy import create_engine, Column, Integer, String, DateTime, func
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

# Cho phép chỉ định đường dẫn file database qua biến môi trường DATABASE_PATH.
# Khi chạy local: mặc định lưu ngay trong thư mục project (water_reminder.db).
# Khi deploy lên Railway: sẽ trỏ tới thư mục volume để dữ liệu không mất khi redeploy.
DB_PATH = os.getenv("DATABASE_PATH", "water_reminder.db")
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
SessionLocal = sessionmaker(bind=engine)


class User(Base):
    """Người dùng đã đăng ký nhận nhắc nhở qua lệnh /dangky."""
    __tablename__ = "users"

    id = Column(String, primary_key=True)  # Discord user ID
    display_name = Column(String, nullable=True)
    is_active = Column(Integer, default=1)  # 1 = đang nhận nhắc nhở, 0 = đã /huy


class WaterLog(Base):
    """Mỗi lần người dùng bấm nút 'Đã uống' (hoặc gõ /uong) sẽ tạo 1 dòng ở đây."""
    __tablename__ = "water_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)


class MoodCheckin(Base):
    """Lưu lại các lần hỏi thăm sức khỏe (mở rộng cho giai đoạn sau)."""
    __tablename__ = "mood_checkins"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    note = Column(String, nullable=True)


class CustomMessage(Base):
    """
    Tin nhắn do admin tự thêm, bổ sung thêm vào các mẫu tin nhắn có sẵn trong messages.py
    (không thay thế, chỉ mở rộng thêm lựa chọn khi bot chọn ngẫu nhiên).
    """
    __tablename__ = "custom_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String, nullable=False)  # reminder / health / praise / nudge / followup
    content = Column(String, nullable=False)
    added_by = Column(String, nullable=True)  # Discord user ID người thêm


def init_db():
    """Tạo bảng nếu chưa tồn tại. Gọi 1 lần khi bot khởi động."""
    Base.metadata.create_all(engine)


def _vn_now() -> datetime:
    """
    Giờ hiện tại theo giờ Việt Nam (UTC+7), tính từ datetime.utcnow().
    Dùng cách này thay vì datetime.now() vì datetime.now() phụ thuộc múi giờ
    hệ điều hành của server (VD Railway có thể chạy ở UTC hoặc múi giờ khác),
    trong khi datetime.utcnow() luôn cho giờ UTC chuẩn bất kể server ở đâu.
    """
    return datetime.utcnow() + timedelta(hours=7)


def _vn_today() -> date:
    """Ngày hiện tại theo giờ Việt Nam, không phụ thuộc múi giờ server."""
    return _vn_now().date()


# ---------- Quản lý đăng ký người dùng ----------

def register_user(user_id: str, display_name: str = None) -> bool:
    """
    Đăng ký 1 người dùng nhận nhắc nhở.
    Trả về True nếu đây là lần đăng ký đầu tiên (mới tạo),
    False nếu người này đã tồn tại từ trước (chỉ cần bật lại is_active).
    """
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.id == str(user_id)).first()
        if user is None:
            user = User(id=str(user_id), display_name=display_name, is_active=1)
            session.add(user)
            session.commit()
            return True
        else:
            was_inactive = user.is_active == 0
            user.is_active = 1
            if display_name:
                user.display_name = display_name
            session.commit()
            return was_inactive
    finally:
        session.close()


def unregister_user(user_id: str):
    """Ngừng gửi nhắc nhở cho người này (không xóa lịch sử uống nước)."""
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.id == str(user_id)).first()
        if user:
            user.is_active = 0
            session.commit()
    finally:
        session.close()


def is_user_registered(user_id: str) -> bool:
    """Kiểm tra người này có đang đăng ký nhận nhắc nhở không."""
    session = SessionLocal()
    try:
        user = session.query(User).filter(
            User.id == str(user_id), User.is_active == 1
        ).first()
        return user is not None
    finally:
        session.close()


def get_active_users() -> list:
    """Trả về danh sách [(user_id, display_name), ...] đang bật nhận nhắc nhở."""
    session = SessionLocal()
    try:
        users = session.query(User).filter(User.is_active == 1).all()
        return [(u.id, u.display_name) for u in users]
    finally:
        session.close()


# ---------- Ghi nhận & thống kê uống nước ----------

def log_water(user_id: str):
    """Ghi nhận 1 lần uống nước."""
    session = SessionLocal()
    try:
        entry = WaterLog(user_id=str(user_id), timestamp=datetime.utcnow())
        session.add(entry)
        session.commit()
    finally:
        session.close()


def get_today_count(user_id: str) -> int:
    """Đếm số lần đã uống nước trong ngày hôm nay (theo giờ UTC)."""
    session = SessionLocal()
    try:
        # Nửa đêm giờ VN = 17:00 UTC ngày hôm trước, cần quy đổi để so sánh đúng
        # với timestamp lưu trong DB (vốn lưu dạng UTC qua datetime.utcnow())
        today_start = datetime.combine(_vn_today(), datetime.min.time()) - timedelta(hours=7)
        count = (
            session.query(func.count(WaterLog.id))
            .filter(WaterLog.user_id == str(user_id))
            .filter(WaterLog.timestamp >= today_start)
            .scalar()
        )
        return count or 0
    finally:
        session.close()


def get_last_n_days_stats(user_id: str, n_days: int = 7) -> dict:
    """
    Trả về dict {ngày: số lần uống nước} cho n ngày gần nhất, dùng để vẽ biểu đồ.
    """
    session = SessionLocal()
    try:
        start_date = _vn_today() - timedelta(days=n_days - 1)
        start_datetime = datetime.combine(start_date, datetime.min.time()) - timedelta(hours=7)

        logs = (
            session.query(WaterLog)
            .filter(WaterLog.user_id == str(user_id))
            .filter(WaterLog.timestamp >= start_datetime)
            .all()
        )

        # Khởi tạo đủ n ngày với giá trị 0, để biểu đồ không bị thiếu ngày
        stats = {
            (start_date + timedelta(days=i)).strftime("%d/%m"): 0
            for i in range(n_days)
        }

        for log_entry in logs:
            # Quy đổi timestamp (UTC) về giờ VN trước khi lấy ngày, để không bị lệch
            # vào khung giờ tối muộn (VD 23h VN = 16h UTC cùng ngày, không lệch,
            # nhưng qua nửa đêm VN 0h-6h59 lại là ngày hôm trước theo giờ UTC).
            vn_time = log_entry.timestamp + timedelta(hours=7)
            key = vn_time.strftime("%d/%m")
            if key in stats:
                stats[key] += 1

        return stats
    finally:
        session.close()


# ---------- Hỏi thăm sức khỏe (mở rộng) ----------

def get_streak(user_id: str) -> int:
    """
    Tính chuỗi ngày liên tục gần nhất có ít nhất 1 lần uống nước.
    Nếu hôm nay chưa uống lần nào, vẫn tính streak từ hôm qua trở về trước
    (không bị mất streak chỉ vì hôm nay chưa kịp uống).
    """
    session = SessionLocal()
    try:
        rows = session.query(WaterLog.timestamp).filter(WaterLog.user_id == str(user_id)).all()
        logged_dates = sorted({(r.timestamp + timedelta(hours=7)).date() for r in rows}, reverse=True)

        if not logged_dates:
            return 0

        today = _vn_today()

        if logged_dates[0] == today:
            streak = 1
            expected = today - timedelta(days=1)
            remaining = logged_dates[1:]
        elif logged_dates[0] == today - timedelta(days=1):
            streak = 1
            expected = today - timedelta(days=2)
            remaining = logged_dates[1:]
        else:
            # Lần uống gần nhất đã cách đây hơn 1 ngày -> streak bị đứt
            return 0

        for d in remaining:
            if d == expected:
                streak += 1
                expected -= timedelta(days=1)
            else:
                break

        return streak
    finally:
        session.close()


def log_mood_checkin(user_id: str, note: str = None):
    session = SessionLocal()
    try:
        entry = MoodCheckin(user_id=str(user_id), timestamp=datetime.utcnow(), note=note)
        session.add(entry)
        session.commit()
    finally:
        session.close()


# ---------- Xuất dữ liệu thô (dùng cho lệnh /xuatdata) ----------

def get_all_water_logs() -> list:
    """Trả về toàn bộ lịch sử uống nước, mới nhất trước: [(user_id, display_name, timestamp), ...]"""
    session = SessionLocal()
    try:
        rows = (
            session.query(WaterLog, User.display_name)
            .outerjoin(User, User.id == WaterLog.user_id)
            .order_by(WaterLog.timestamp.desc())
            .all()
        )
        return [(log.user_id, name, log.timestamp) for log, name in rows]
    finally:
        session.close()


def get_all_users_raw() -> list:
    """Trả về toàn bộ danh sách người dùng: [(user_id, display_name, is_active), ...]"""
    session = SessionLocal()
    try:
        users = session.query(User).all()
        return [(u.id, u.display_name, u.is_active) for u in users]
    finally:
        session.close()


# ---------- Tin nhắn tùy chỉnh (custom messages) ----------

def add_custom_message(category: str, content: str, added_by: str) -> int:
    """Thêm 1 tin nhắn tùy chỉnh, trả về ID vừa tạo."""
    session = SessionLocal()
    try:
        entry = CustomMessage(category=category, content=content, added_by=str(added_by))
        session.add(entry)
        session.commit()
        return entry.id
    finally:
        session.close()


def remove_custom_message(message_id: int) -> bool:
    """Xóa 1 tin nhắn tùy chỉnh theo ID. Trả về True nếu xóa thành công, False nếu không tìm thấy."""
    session = SessionLocal()
    try:
        entry = session.query(CustomMessage).filter(CustomMessage.id == message_id).first()
        if entry is None:
            return False
        session.delete(entry)
        session.commit()
        return True
    finally:
        session.close()


def get_custom_messages(category: str) -> list:
    """Trả về danh sách [(id, content), ...] các tin nhắn tùy chỉnh thuộc 1 category."""
    session = SessionLocal()
    try:
        rows = session.query(CustomMessage).filter(CustomMessage.category == category).all()
        return [(r.id, r.content) for r in rows]
    finally:
        session.close()
