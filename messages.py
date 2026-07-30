"""
messages.py
Kho chứa các mẫu tin nhắn. Tách riêng ra để dễ chỉnh sửa, thêm bớt
mà không cần đụng vào logic chính của bot.
"""

import random

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


def get_random_reminder() -> str:
    return random.choice(REMINDER_MESSAGES)


def get_random_health_checkin() -> str:
    return random.choice(HEALTH_CHECKIN_MESSAGES)


def get_random_praise() -> str:
    return random.choice(PRAISE_MESSAGES)


def get_random_nudge() -> str:
    return random.choice(NUDGE_MESSAGES)
