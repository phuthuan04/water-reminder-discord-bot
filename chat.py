"""
chat.py
Xử lý tính năng trò chuyện với bot.
Giai đoạn A: trò chuyện + đưa insight dựa trên dữ liệu thật.
Giai đoạn B: tự thực thi hành động AN TOÀN qua chat (ghi nhận uống nước) bằng function calling.
Giai đoạn "Tự do trò chuyện" (hiện tại): ngoài trả lời khi được @mention, bot có thể tự
quyết định góp lời vào cuộc trò chuyện trong kênh (khi tính năng này được bật qua /tudo),
với cơ chế "nghỉ" tối thiểu giữa các lần để tránh chen ngang quá nhiều.

Tách riêng file này khỏi bot.py vì logic ở đây khá độc lập (xây context, gọi Gemini,
quản lý lịch sử chat) - giữ bot.py gọn, chỉ lo việc orchestration (nhận sự kiện, gửi phản hồi).
"""

import os
import asyncio
import logging

from dotenv import load_dotenv

import database as db

load_dotenv()
log = logging.getLogger("water-bot.chat")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
CHAT_HISTORY_LIMIT = int(os.getenv("CHAT_HISTORY_LIMIT", "20"))

# Thời gian tối đa (giây) chờ 1 cuộc gọi Gemini trước khi coi là "treo" và bỏ qua -
# tránh việc bot bị nghẽn vô thời hạn nếu Gemini không phản hồi.
GEMINI_TIMEOUT_SECONDS = int(os.getenv("GEMINI_TIMEOUT_SECONDS", "15"))

# Khi Gemini báo lỗi "503 quá tải", thử lại tối đa mấy lần và chờ bao nhiêu giây giữa các lần.
# Các loại lỗi khác (sai key, hết quota, mất mạng,...) KHÔNG thử lại vì thử lại cũng không ích gì.
GEMINI_RETRY_MAX = int(os.getenv("GEMINI_RETRY_MAX", "1"))
GEMINI_RETRY_DELAY_SECONDS = int(os.getenv("GEMINI_RETRY_DELAY_SECONDS", "3"))

DEFAULT_SYSTEM_PROMPT = (
    "Bạn là trợ lý ảo của \"Stay Hydrated!\" - 1 Discord bot nhắc uống nước dành riêng cho cặp đôi phuthuan04 và Khánh Đan. "
    "Nói chuyện như 1 người bạn thân nhắn tin bình thường: ngắn gọn, tự nhiên, đúng trọng tâm câu hỏi - KHÔNG viết dài dòng, "
    "KHÔNG cố nhồi thêm kiến thức/insight nếu người dùng không hỏi tới.\n\n"
    "Độ dài trả lời: ưu tiên 1-3 câu ngắn cho hầu hết tin nhắn. Chỉ viết dài hơn khi người dùng rõ ràng muốn tìm hiểu sâu 1 chủ đề cụ thể. "
    "Không cần luôn kết thúc bằng 1 câu hỏi hay gợi ý thêm - chỉ hỏi lại khi thực sự cần làm rõ ý.\n\n"
    "Bạn sẽ được cung cấp kèm số liệu uống nước thật (hôm nay, streak, 7 ngày) - CHỈ nhắc tới khi đúng chủ đề đang nói tới, "
    "không tự chèn vào nếu không liên quan. Dùng đúng số liệu, không bịa.\n\n"
    "Bạn CÓ THỂ gọi hàm ghi_nhan_uong_nuoc khi người dùng xác nhận VỪA/ĐÃ uống nước xong. Sau khi gọi, xác nhận ngắn gọn là đã ghi nhận.\n\n"
    "Nếu được hỏi cách đổi giờ nhắc nhở: nói ngắn là hiện cần chỉnh thủ công qua cấu hình, chưa đổi qua chat được.\n\n"
    "Không đưa lời khuyên y tế chuyên sâu - nếu vấn đề sức khỏe nghiêm trọng thì khuyên gặp bác sĩ, ngắn gọn thôi."
)

# Có thể tùy chỉnh trực tiếp trên Railway qua biến PROMPT_CHAT, không cần sửa code/deploy lại.
PROMPT_CHAT = os.getenv("PROMPT_CHAT") or DEFAULT_SYSTEM_PROMPT

FALLBACK_REPLY = "Xin lỗi, mình đang gặp chút trục trặc, thử lại sau nha 😅"

# Chuỗi đặc biệt để Gemini báo hiệu "không cần góp lời" khi ở chế độ tự do trò chuyện.
# Không hiển thị cho người dùng thấy, chỉ dùng nội bộ để bot biết im lặng.
SKIP_TOKEN = "__KHONG_CAN_TRA_LOI__"

FREECHAT_INSTRUCTION = (
    f"\n\n[Lưu ý: đây là 1 tin nhắn trong kênh chat chung, KHÔNG trực tiếp nhắn cho bạn. "
    f"Bạn đang tự do quan sát, chỉ nên góp lời nếu thực sự có gì thú vị/đáng nói hoặc liên "
    f"quan tới sức khỏe/uống nước. Nếu không có gì cần nói, trả lời ĐÚNG DUY NHẤT chuỗi: "
    f"{SKIP_TOKEN} (không thêm bất kỳ ký tự nào khác)."
)


def _get_log_water_tool():
    """
    Định nghĩa hàm 'ghi_nhan_uong_nuoc' cho Gemini - đặt trong hàm riêng (không phải hằng số
    ở module level) vì cần import types từ google.genai, chỉ import khi thực sự cần dùng.
    """
    from google.genai import types

    function = types.FunctionDeclaration(
        name="ghi_nhan_uong_nuoc",
        description=(
            "Ghi nhận 1 lần người dùng vừa uống nước. CHỈ gọi hàm này khi người dùng "
            "xác nhận rõ ràng là họ VỪA uống nước hoặc ĐÃ uống nước xong ngay lúc này. "
            "KHÔNG gọi nếu chỉ đang hỏi/nói chuyện phiếm về nước."
        ),
        parameters_json_schema={"type": "object", "properties": {}},
    )
    return types.Tool(function_declarations=[function])


def _extract_function_name(function_call_part) -> str:
    """Truy xuất tên hàm được gọi, phòng trường hợp cấu trúc object khác nhau giữa các phiên bản SDK."""
    name = getattr(function_call_part, "name", None)
    if name:
        return name
    inner = getattr(function_call_part, "function_call", None)
    return getattr(inner, "name", "") if inner else ""


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


async def call_gemini_with_retry(make_coro, max_retries: int = None, retry_delay: int = None):
    """
    Gọi 1 API Gemini bất kỳ, có kèm 2 lớp bảo vệ:
    1. TIMEOUT: nếu Gemini không phản hồi sau GEMINI_TIMEOUT_SECONDS giây, coi như treo và bỏ qua
       (dùng asyncio.wait_for) - tránh làm nghẽn bot vô thời hạn.
    2. TỰ ĐỘNG THỬ LẠI: nếu gặp đúng lỗi "503 UNAVAILABLE" (Google báo đang quá tải - thông điệp
       lỗi của chính Google gợi ý thử lại sau vài giây thường sẽ thành công), tự động chờ
       retry_delay giây rồi gọi lại, tối đa max_retries lần. Các lỗi KHÁC (sai key, hết quota,
       mất mạng,...) sẽ raise lỗi ngay lập tức, KHÔNG thử lại - vì thử lại không giải quyết được.

    Tham số:
    - make_coro: 1 hàm KHÔNG NHẬN THAM SỐ, mỗi lần gọi trả về 1 coroutine MỚI (VD: 1 lambda bọc
      quanh client.aio.models.generate_content(...)). Bắt buộc phải truyền vào dạng hàm như vậy
      (không phải coroutine dựng sẵn), vì 1 coroutine trong Python chỉ await được đúng 1 lần -
      nếu muốn gọi lại lần 2 (khi retry) thì cần tạo ra 1 coroutine hoàn toàn mới.
    - max_retries: số lần thử lại tối đa (không tính lần gọi đầu). Mặc định lấy từ env
      GEMINI_RETRY_MAX (mặc định 1 lần).
    - retry_delay: số giây chờ giữa các lần thử lại. Mặc định lấy từ env
      GEMINI_RETRY_DELAY_SECONDS (mặc định 3 giây).

    Nếu vẫn lỗi sau khi hết lượt thử lại (hoặc gặp lỗi không phải 503), hàm raise lại đúng lỗi gốc
    để hàm gọi nó (_generate_reply, generate_fact_via_gemini,...) tự bắt và fallback như cũ.
    """
    if max_retries is None:
        max_retries = GEMINI_RETRY_MAX
    if max_retries < 0:
        max_retries = 0
    if retry_delay is None:
        retry_delay = GEMINI_RETRY_DELAY_SECONDS

    last_exception = None
    for attempt in range(max_retries + 1):
        try:
            return await asyncio.wait_for(make_coro(), timeout=GEMINI_TIMEOUT_SECONDS)
        except Exception as e:
            last_exception = e
            is_overloaded = "503" in str(e) or "UNAVAILABLE" in str(e)
            if is_overloaded and attempt < max_retries:
                log.info(
                    "Gemini bị quá tải (503) - thử lại lần %d/%d sau %ds",
                    attempt + 1, max_retries, retry_delay,
                )
                await asyncio.sleep(retry_delay)
                continue
            raise

    # Về lý thuyết không bao giờ chạy tới đây (mọi nhánh trên đều return hoặc raise),
    # nhưng giữ lại như 1 lớp an toàn cuối cùng, tránh hàm "rơi" ra ngoài mà không rõ lý do.
    raise last_exception


async def _generate_reply(user_id: str, user_message: str, extra_instruction: str = "") -> str:
    """
    Lõi xử lý dùng chung cho cả 2 chế độ (@mention và tự do góp lời): đọc lịch sử,
    gọi Gemini kèm ngữ cảnh + tool ghi_nhan_uong_nuoc, thực thi hàm nếu được yêu cầu,
    trả về câu trả lời cuối cùng (có thể là SKIP_TOKEN nếu extra_instruction cho phép im lặng).
    KHÔNG tự lưu lịch sử ở đây - để hàm gọi nó (get_chat_response / maybe_join_conversation)
    tự quyết định có lưu hay không, vì chế độ tự do góp lời không muốn lưu các lượt "im lặng".
    """
    
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=GEMINI_API_KEY)
    tool = _get_log_water_tool()
    config = types.GenerateContentConfig(system_instruction=PROMPT_CHAT, tools=[tool])

    history = db.get_chat_history(user_id, limit=CHAT_HISTORY_LIMIT)
    contents = [
        types.Content(role=role, parts=[types.Part.from_text(text=content)])
        for role, content in history
    ]

    data_context = _build_data_context(user_id)
    full_message = f"{data_context}\n\n{user_message}{extra_instruction}"
    contents.append(types.Content(role="user", parts=[types.Part.from_text(text=full_message)]))

    response = await call_gemini_with_retry(
        lambda: client.aio.models.generate_content(model="gemini-3.5-flash", contents=contents, config=config)
    )

    function_calls = getattr(response, "function_calls", None) or []
    if function_calls:
        fc = function_calls[0]
        fc_name = _extract_function_name(fc)

        if fc_name == "ghi_nhan_uong_nuoc":
            db.log_water(user_id)
            new_count = db.get_today_count(user_id)
            function_result = {"result": f"Đã ghi nhận thành công. Hôm nay đã uống nước {new_count} lần."}
        else:
            function_result = {"error": f"Không rõ hàm '{fc_name}'"}

        function_response_part = types.Part.from_function_response(name=fc_name, response=function_result)
        model_call_content = response.candidates[0].content
        contents.append(model_call_content)
        contents.append(types.Content(role="tool", parts=[function_response_part]))

        response = await call_gemini_with_retry(
            lambda: client.aio.models.generate_content(model="gemini-3.5-flash", contents=contents, config=config)
        )

    return (response.text or "").strip()


async def get_chat_response(user_id: str, user_message: str) -> str:
    """Xử lý 1 lượt trò chuyện khi được @mention - LUÔN trả lời, luôn lưu lịch sử."""
    if not GEMINI_API_KEY:
        return "Mình chưa được bật tính năng trò chuyện (thiếu cấu hình API key) 😅"

    try:
        reply = await _generate_reply(user_id, user_message)
        if not reply:
            return FALLBACK_REPLY

        db.add_chat_message(user_id, "user", user_message)
        db.add_chat_message(user_id, "model", reply)
        return reply
    except Exception as e:
        log.warning("Lỗi khi trò chuyện qua Gemini: %s", e)
        return FALLBACK_REPLY


async def maybe_join_conversation(user_id: str, user_message: str):
    """
    Dùng cho chế độ TỰ DO trò chuyện (không được @mention).
    Trả về None nếu bot quyết định im lặng (không có gì đáng nói, hoặc có lỗi xảy ra) -
    trường hợp None thì KHÔNG lưu lịch sử, để tránh làm rối ngữ cảnh với các lượt "im lặng".
    Trả về chuỗi câu trả lời nếu bot quyết định góp lời.
    """
    if not GEMINI_API_KEY:
        return None

    try:
        reply = await _generate_reply(user_id, user_message, extra_instruction=FREECHAT_INSTRUCTION)

        if not reply or SKIP_TOKEN in reply:
            return None

        db.add_chat_message(user_id, "user", user_message)
        db.add_chat_message(user_id, "model", reply)
        return reply
    except Exception as e:
        log.warning("Lỗi khi tự do góp lời qua Gemini: %s", e)
        return None
