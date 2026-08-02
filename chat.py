"""
chat.py
Xử lý tính năng trò chuyện qua @mention với bot (Giai đoạn A: chỉ trò chuyện + đưa insight,
CHƯA tự thực thi hành động như log nước - phần đó sẽ thêm ở Giai đoạn B).

Tách riêng file này khỏi bot.py vì logic ở đây khá độc lập (xây context, gọi Gemini,
quản lý lịch sử chat) - giữ bot.py gọn, chỉ lo việc orchestration (nhận sự kiện, gửi phản hồi).
"""

import os
import logging
from datetime import datetime, timedelta

from dotenv import load_dotenv

import database as db

load_dotenv()
log = logging.getLogger("water-bot.chat")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
CHAT_HISTORY_LIMIT = int(os.getenv("CHAT_HISTORY_LIMIT", "20"))

DEFAULT_SYSTEM_PROMPT = (
    "Bạn là trợ lý ảo của \"Stay Hydrated!\" - 1 Discord bot nhắc uống nước dành riêng cho "
    "cặp đôi phuthuan04 và Khánh Đan. Giọng điệu thân thiện, quan tâm, gần gũi như người "
    "yêu chăm sóc nhau, dùng tiếng Việt tự nhiên.\n\n"
    "Bạn sẽ luôn được cung cấp kèm theo: số lần uống nước hôm nay, streak hiện tại, "
    "thống kê 7 ngày gần nhất của người đang nhắn tin. Dùng ĐÚNG các số liệu này khi "
    "trả lời, TUYỆT ĐỐI không tự bịa số liệu.\n\n"
    "Hiện tại bạn CHƯA thể tự thực hiện hành động gì (như ghi nhận uống nước) - chỉ có thể "
    "trò chuyện, tư vấn, và đưa insight dựa trên dữ liệu được cung cấp. Nếu người dùng muốn "
    "ghi nhận đã uống nước, hướng dẫn họ dùng lệnh /uong hoặc bấm nút trong tin nhắn nhắc nhở.\n\n"
    "Nếu được hỏi cách đổi giờ nhắc nhở, giải thích rằng hiện tại cần chỉnh thủ công qua "
    "cấu hình, chưa tự đổi qua chat được.\n\n"
    "Trả lời ngắn gọn (dưới 150 từ), phù hợp hiển thị trên Discord. Có thể trò chuyện phiếm "
    "nhẹ nhàng nhưng khéo léo lái về chủ đề sức khỏe/uống nước. Không đưa lời khuyên y tế "
    "chuyên sâu - khuyến khích gặp bác sĩ nếu có vấn đề sức khỏe nghiêm trọng."
)

# Có thể tùy chỉnh trực tiếp trên Railway qua biến PROMPT_CHAT, không cần sửa code/deploy lại.
PROMPT_CHAT = os.getenv("PROMPT_CHAT") or DEFAULT_SYSTEM_PROMPT

FALLBACK_REPLY = "Xin lỗi, mình đang gặp chút trục trặc, thử lại sau nha 😅"


def _build_data_context(user_id: str) -> str:
    """Tóm tắt dữ liệu uống nước hiện tại của user, chèn kèm tin nhắn gửi Gemini."""
    today_count = db.get_today_count(user_id)
    streak = db.get_streak(user_id)
    stats = db.get_last_n_days_stats(user_id, 7)
    stats_str = ", ".join(f"{day}: {count} lần" for day, count in stats.items())

    return (
        f"[Dữ liệu hiện tại - hôm nay đã uống {today_count} lần, streak {streak} ngày, "
        f"thống kê 7 ngày gần nhất ({stats_str})]"
    )


async def get_chat_response(user_id: str, user_message: str) -> str:
    """
    Xử lý 1 lượt trò chuyện: đọc lịch sử, gọi Gemini kèm ngữ cảnh, lưu lại lịch sử mới.
    Trả về FALLBACK_REPLY nếu có bất kỳ lỗi gì (chưa cấu hình key, mất mạng, lỗi API,...).
    """
    if not GEMINI_API_KEY:
        return "Mình chưa được bật tính năng trò chuyện (thiếu cấu hình API key) 😅"

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=GEMINI_API_KEY)

        history = db.get_chat_history(user_id, limit=CHAT_HISTORY_LIMIT)
        contents = [
            types.Content(role=role, parts=[types.Part.from_text(text=content)])
            for role, content in history
        ]

        data_context = _build_data_context(user_id)
        contents.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=f"{data_context}\n\n{user_message}")],
            )
        )

        response = await client.aio.models.generate_content(
            model="gemini-3.5-flash",
            contents=contents,
            config=types.GenerateContentConfig(system_instruction=PROMPT_CHAT),
        )
        reply = (response.text or "").strip()
        if not reply:
            return FALLBACK_REPLY

        # Lưu lại lịch sử - lưu tin nhắn GỐC của user (không kèm data_context để lịch sử gọn,
        # data_context sẽ tự tính lại mới mỗi lượt sau).
        db.add_chat_message(user_id, "user", user_message)
        db.add_chat_message(user_id, "model", reply)

        return reply
    except Exception as e:
        log.warning("Lỗi khi trò chuyện qua Gemini: %s", e)
        return FALLBACK_REPLY
