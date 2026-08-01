"""
messages.py
Kho chứa các mẫu tin nhắn. Tách riêng ra để dễ chỉnh sửa, thêm bớt
mà không cần đụng vào logic chính của bot.

Mỗi hàm get_random_* sẽ gộp danh sách có sẵn (viết cứng bên dưới)
VỚI danh sách tin nhắn admin tự thêm qua lệnh /themtinnhan (lưu trong database),
rồi mới chọn ngẫu nhiên 1 câu trong toàn bộ danh sách gộp đó.
"""

import random
import database as db

# Tin nhắn nhắc nhở uống nước - sẽ được chọn ngẫu nhiên mỗi lần nhắc
REMINDER_MESSAGES = [
    "Đến giờ uống nước rồi nè 💧 Nhớ uống cho khỏe nha!",
    "Ê, uống nước chưa đó? Cơ thể đang cần nước nè 🥤",
    "Nhắc nhẹ: 1 ly nước cho làn da đẹp và tinh thần sảng khoái nha 💦",
    "Đừng quên uống nước đó nha, đừng để tới lúc khát mới uống 😤",
    "Giờ vàng để uống nước đây! Làm 1 ly cho khỏe nào 💧",
    "Người yêu bé nhỏ ơi, uống nước đi rồi mình hỏi thăm tiếp nè 🥰",
]

# Câu hỏi thăm sức khỏe - chèn ngẫu nhiên xen kẽ để tạo cảm giác quan tâm thật
HEALTH_CHECKIN_MESSAGES = [
    "Hôm nay cảm thấy sao rồi? Có mệt không? 🤗",
    "Ăn uống đầy đủ chưa đó? Đừng bỏ bữa nha 🍚",
    "Ngủ đủ giấc tối qua không? Nhớ giữ sức khỏe nha 😴",
    "Có đau đầu hay khó chịu gì không? Nói cho biết nha 💭",
    "Nhớ nghỉ ngơi xíu giữa giờ làm việc/học nha, đừng ráng quá sức 🌿",
]

# Tin nhắn khen khi bấm "Đã uống"
PRAISE_MESSAGES = [
    "Giỏi quá! Cứ giữ vậy nha 🥰",
    "Ngoan ghê, uống nước đều đặn là khỏe re đó 💪",
    "Yeah! Cảm ơn đã chăm sóc bản thân nha 💧",
    "Tốt lắm đó! Cơ thể đang cảm ơn bạn đó nè 🌟",
]

# Tin nhắn khi bấm "Chưa uống"
NUDGE_MESSAGES = [
    "Ok, tranh thủ uống liền nha, đừng để quên luôn đó 😗",
    "Nhớ uống sớm nha, mình sẽ nhắc lại sau đó!",
    "Được rồi, nhưng đừng trì hoãn lâu quá nha 🥺",
]

# Tin nhắn nhắc LẠI khi sau 1 khoảng thời gian vẫn chưa thấy uống nước
FOLLOWUP_MESSAGES = [
    "Nãy nhắc rồi mà vẫn chưa thấy uống nước nè, tranh thủ đi nha 🥺",
    "Ê, nước đang đợi bạn đó! Đừng để quên luôn nha 💧",
    "Nhắc lại nè, uống 1 ly nước rồi quay lại làm việc tiếp nha 😌",
    "Chưa uống nước thiệt hả? Đi uống ngay đi nha, mình đợi 🙏",
]

# Ánh xạ category (dùng trong lệnh /themtinnhan, /xemtinnhan, /xoatinnhan)
# sang danh sách có sẵn tương ứng - dùng chung ở nhiều nơi nên định nghĩa 1 lần.
CATEGORY_TO_BUILTIN = {
    "reminder": REMINDER_MESSAGES,
    "health": HEALTH_CHECKIN_MESSAGES,
    "praise": PRAISE_MESSAGES,
    "nudge": NUDGE_MESSAGES,
    "followup": FOLLOWUP_MESSAGES,
}


def _get_combined(category: str) -> list:
    """Gộp danh sách có sẵn (viết cứng) + danh sách tùy chỉnh (lưu trong DB)."""
    builtin = CATEGORY_TO_BUILTIN.get(category, [])
    custom = [content for _id, content in db.get_custom_messages(category)]
    return builtin + custom


def get_random_reminder() -> str:
    return random.choice(_get_combined("reminder"))


def get_random_health_checkin() -> str:
    return random.choice(_get_combined("health"))


def get_random_praise() -> str:
    return random.choice(_get_combined("praise"))


def get_random_nudge() -> str:
    return random.choice(_get_combined("nudge"))


def get_random_followup() -> str:
    return random.choice(_get_combined("followup"))
