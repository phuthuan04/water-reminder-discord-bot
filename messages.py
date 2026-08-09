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

"""
messages.py
Kho chứa các mẫu tin nhắn đã được bổ sung & tối ưu văn phong tự nhiên.
"""

# Tin nhắn nhắc nhở uống nước (Chọn ngẫu nhiên mỗi lần nhắc)
REMINDER_MESSAGES = [
    "Đến giờ uống nước rồi nè 💧 Nhớ uống cho khỏe nha!",
    "Nhắc nhẹ: 1 ly nước cho làn da đẹp và tinh thần sảng khoái nha 💦",
    "Giờ vàng để uống nước đây! Làm 1 ly cho khỏe nào 💧",
    "Nạp thêm xíu 'nhiên liệu' nước để tiếp tục chinh phục ngày mới nào 🚀",
    "Một ly nước lọc mát lành đang chờ bạn nè, uống đi cho tỉnh táo nhé 🥛",
    "Ê, uống nước chưa đó? Cơ thể đang kêu gào cần nước nè 🥤",
    "Đừng quên uống nước đó nha, đừng để tới lúc môi khô khốc mới đi tìm 😤",
    "Alo alo! Máy lọc nước chạy bằng cơm ơi, nạp nước thôi nào 🤖💧",
    "Hệ thống báo động: Lượng nước trong cơ thể đang tụt dốc, uống ngay! 🚨",
    "Đang làm gì đó? Tạm dừng 10 giây làm 1 ngụm nước rồi làm tiếp nha ⏱️",
    "Người yêu bé nhỏ ơi, uống nước đi rồi mình làm gì thì làm tiếp nè 🥰",
    "Thương mình thì nhớ uống nước đều đặn nha, đừng để cơ thể mệt mỏi 🥺",
    "Trời có nóng hay lạnh thì cũng phải giữ cho cơ thể đủ nước đó nhe 🌿",
    "Ting ting! Lịch hẹn uống nước đến rồi, đứng dậy rót đầy 1 ly đi nào 🔔",
    "Mắt mỏi, cổ mỏi thì uống ngụm nước rồi vươn vai xíu cho đỡ căng thẳng nha 🧘",
    "Làm việc hăng hái nhưng đừng quên tiếp nước cho cơ thể vận hành mượt mà nha ⚡",
    "Uống nước không chỉ đỡ khát mà còn giúp tư duy sáng suốt hơn đó, làm 1 ly liền! 💡",
    "Nước lọc - thức uống 0 calo nhưng đem lại 100% năng lượng cho ngày mới 🥂",
    "Nhanh tay bấm 'Đã uống' sau khi làm xong 1 ly nước mát lạnh nào 🎯",
    "Cơ thể đang 'order' 1 ly nước tinh khiết, phục vụ ngay thôi bạn ơi 🛵",
    "Nước là liều thuốc bổ miễn phí tốt nhất đó, uống đều đặn mỗi ngày nha ☘️",
    "Đừng đợi đến khi môi khô hay họng gắt mới nhớ tới nước nhé, uống ngay thôi 🧊",
    "1 ly nước lúc này sẽ giúp bạn lấy lại 200% tập trung để chạy deadline đó 💻",
]

# Câu hỏi thăm sức khỏe (Chèn ngẫu nhiên xen kẽ tạo cảm giác như người thật)
HEALTH_CHECKIN_MESSAGES = [
    "Hôm nay cảm thấy sao rồi? Có mệt mỏi hay áp lực gì không? 🤗",
    "Ăn uống đầy đủ chưa đó? Đừng vì bận việc mà bỏ bữa nha 🍚",
    "Ngủ đủ giấc tối qua không? Nhớ giữ sức khỏe thật tốt nha 😴",
    "Có đau đầu, mỏi mắt hay khó chịu gì không? Nói cho biết nha 💭",
    "Nhớ nghỉ ngơi xíu giữa giờ làm việc/học tập nha, vươn vai phát nào 🌿",
    "Ngồi máy tính/điện thoại lâu rồi đó, chớp mắt vài cái rồi quay sang nhìn xa xíu đi 👁️✨",
    "Có đang căng thẳng chuyện gì không? Uống ngụm nước sâu rồi hít thở đều nha 🧘‍♂️",
    "Vai cổ có đang bị cứng mỏi không? Xoay cổ nhẹ nhàng vài vòng giải mỏi đi nào 💆",
    "Công việc hôm nay có suôn sẻ không? Vẫn ổn cả chứ bạn tôi? ☕",
    "Nhớ thả lỏng cơ hàm và vai xuống nha, bạn đang gồng mình hơi lâu rồi đó 🌿",
    "Đã bước ra ngoài hít thở không khí tự nhiên chút nào chưa hay ngồi một chỗ suốt thế? 🌤️",
    "Thời tiết dạo này thất thường, nhớ giữ ấm/hạ nhiệt cơ thể cẩn thận nha 🌡️",
    "Đừng quên mỉm cười một cái tự thưởng cho sự nỗ lực của bản thân hôm nay nhé 😊",
    "Mắt có bị khô không? Nhắm mắt nghỉ ngơi khoảng 30 giây cho mắt hồi phục đi nè 🙈",
    "Uống nước xong nhớ tranh thủ đi lại vài bước cho máu huyết lưu thông tốt nha 👣",
    "Đang tập trung cao độ lắm đúng không? Xong việc này nhớ thư giãn xíu nhé 🎧",
    "Dù bận rộn đến đâu thì sức khỏe của bạn vẫn luôn là ưu tiên số 1 đó nha 💖",
]

# Tin nhắn khen khi bấm "Đã uống"
PRAISE_MESSAGES = [
    "Giỏi quá! Cứ duy trì phong độ này nha 🥰",
    "Ngoan ghê, uống nước đều đặn là khỏe re ngay 💪",
    "Yeah! Cảm ơn bạn vì đã biết chăm sóc bản thân nha 💧",
    "Tốt lắm đó! Các tế bào trong cơ thể đang nhảy múa cảm ơn bạn đó 🌟",
    "Xuất sắc! Đã cộng 100 điểm chăm chỉ cho bạn 💯✨",
    "10 điểm không có nhưng! Giữ tinh thần này suốt ngày nha 👑",
    "Siêu cấp chăm chỉ! Da đẹp tinh thần minh mẫn ngay lập tức 🌸",
    "Cơ thể vừa được nạp năng lượng chuẩn chỉnh, tiếp tục tỏa sáng thôi 🚀",
    "Quá tuyệt vời! Bạn đang tự tạo thói quen cực kỳ có lợi cho sức khỏe đấy 🎉",
    "Tuyệt cú mèo! Tim, thận và não bộ đồng loạt thả tim cho bạn 💓",
    "Đã ghi nhận! Bạn vừa hoàn thành 1 nhiệm vụ quan trọng trong ngày 🏅",
    "Đúng là người biết tự yêu thương bản thân, thả ngàn tim cho bạn nè 💞",
    "Đã uống xong rồi hử? Thần thái tự nhiên thăng hạng lên liền luôn 😉",
    "Phong độ rất ổn định! Hãy duy trì chuỗi ngày sống khỏe này nhé 🏆",
    "Cơ thể bạn vừa gửi lời cảm ơn ngọt ngào nhất vì hành động này đó 🍧",
    "Bấm nút chuẩn đấy! Giờ thì quay lại làm việc với 100% năng lượng thôi ⚡",
]

# Tin nhắn khi bấm "Chưa uống"
NUDGE_MESSAGES = [
    "Ok, tranh thủ uống liền nha, đừng để quên luôn đó 😗",
    "Nhớ uống sớm nha, mình sẽ quay lại kiểm tra đó!",
    "Được rồi, nhưng chốt deal là chút nữa phải uống liền nha 🥺",
    "Hứa với mình là trong vòng 5 phút nữa phải uống đó nha 🤝",
    "Tạm hoãn chút thôi nha, nước vẫn đang đợi bạn đó 🥛",
    "Ghi nhận hoãn lịch! Nhưng xong tay việc này là phải đi rót nước ngay nha 📝",
    "Đang dở tay đúng không? Xử lý xong bước này nhớ tự thưởng 1 ly nước mát nhé ⏳",
    "Đừng delay lâu quá nha, cơ thể không chờ được lâu đâu đó 🏃‍♂️",
    "Oki cho nợ 3 phút nha, chút nữa nhớ trả đủ 1 ly nước đầy đó 💸",
    "Đừng quên luôn nha người ơi, tớ vẫn đang tính giờ đó ⏱️",
    "Tạm tha lần này, nhưng lần nhắc sau là phải uống thật đấy nhé 😜",
    "Nhớ nhé, deadline công việc quan trọng nhưng deadline uống nước cũng gấp lắm rồi 🚨",
    "Đừng để ly nước cô đơn trên bàn nha, uống sớm cho tươi tắn lại nè 🧊",
    "Cảnh báo nhẹ: Trì hoãn uống nước có thể gây sụt giảm năng lượng đó nha 📉",
    "Hứa chắc chắn chút nữa uống đó nha, không được thất hứa đâu đấy 🤙",
]

# Tin nhắn nhắc LẠI (Follow-up) khi sau khoảng thời gian vẫn chưa thấy uống
FOLLOWUP_MESSAGES = [
    "Nãy nhắc rồi mà vẫn chưa thấy uống nước nè, tranh thủ đi nha 🥺",
    "Ê, nước đang đợi bạn dài cổ rồi đó! Đừng để quên luôn nha 💧",
    "Nhắc lại nè: Uống 1 ly nước rồi quay lại làm việc tiếp cho năng suất nha 😌",
    "Chưa uống nước thiệt hả? Đi uống ngay đi, mình đứng đây đợi nè 🙏",
    "Lần thứ n trong ngày rồi đó nha! Đi lấy nước liền không mình dỗi đó 😤",
    "Đang bận lắm đúng không? Nhưng sức khỏe quan trọng nhất, uống 1 ngụm thôi cũng được nè 🤏",
    "Còi báo động lần 2! Bạn vẫn chưa chịu uống nước đúng không đó? 🚨",
    "Alo alo! Đừng lờ tin nhắn của tớ chứ, đi làm ngụm nước cho tỉnh táo liền nào 📢",
    "Dừng khoảng chừng là 2 giây! Đứng dậy đi lấy nước ngay và luôn 🛑",
    "Cơ thể đang 'đình công' vì thiếu nước rồi kìa, cứu nguy cho nó gấp thôi 🆘",
    "Nhắc nhẹ lần cuối nè, lười uống nước là da khô, não lag thiệt đó nha 🙈",
    "Trời ơi vẫn chưa uống nữa hả? Rót 1 ly nước đâu có mất tới 1 phút đâu nè 🤦‍♂️",
    "Tớ sẽ xuất hiện liên tục cho tới khi nào bạn chịu bấm 'Đã uống' mới thôi 👻",
    "Bận rộn tới mấy cũng đừng bỏ quên bản thân chứ, đi uống ngụm nước đi mà 🥺",
    "Một ngụm thôi cũng được, nhấp môi cái cho bớt khô họng đi bạn ơi 🥛",
    "Đừng để tớ phải kích hoạt chế độ 'nhắc nhở siêu dai dẳng' nha, đi uống liền đi ⚡",
]

# Facts vui về uống nước (Dùng dự phòng khi Gemini API lỗi/chưa cấu hình)
WATER_FACTS = [
    "💧 Cơ thể bạn chiếm khoảng 60% là nước — về cơ bản bạn là 1 cái bình nước biết đi lại và than phiền.",
    "🧠 Não bộ chứa tới ~85% là nước, thiếu nước 1 chút thôi là não đã 'lag' và giảm tập trung liền.",
    "⏳ Con người có thể nhịn ăn cả tháng, nhưng thiếu nước thì chỉ trụ được vài ngày thôi — nước quan trọng hơn đồ ăn nhiều.",
    "😌 Đau đầu bất chợt? Có thể chỉ đơn giản là do thiếu nước, uống 1 ly trước khi vội tìm thuốc nha.",
    "✨ Uống đủ nước giúp da căng mọng, giảm khô ráp — giải pháp skincare rẻ tiền nhất lịch sử.",
    "🏃 Chỉ cần mất nước nhẹ (1-2%) thôi cũng đủ khiến cơ thể uể oải và giảm tới 15% hiệu suất làm việc.",
    "🩸 Thiếu nước làm máu đặc hơn, tim phải đập cực hơn — uống nước là đang trực tiếp 'thương' trái tim mình đó.",
    "🌊 Trái Đất có tới 70% là nước, nhưng chưa tới 1% là nước sạch dùng được — trân trọng từng ly nước bạn đang có nha.",
    "🦴 Xương của chúng ta nhìn cứng cáp vậy thôi chứ thực chất chứa tới khoảng 31% là nước đó!",
    "😴 Bạn có biết: Uống 1 ly nước ngay sau khi ngủ dậy giúp 'thức tỉnh' các cơ quan nội tạng sau một đêm dài nghỉ ngơi.",
    "👅 Cảm giác thèm ăn vặt đôi khi chỉ là tín hiệu giả do cơ thể bị thiếu nước bộc phát ra thôi đó.",
    "🧊 Uống nước lạnh giúp đốt cháy một lượng calo nhỏ vì cơ thể phải tốn năng lượng để làm ấm nước lại.",
    "🏋️ Mất 2% lượng nước trong cơ thể có thể làm giảm tới 10% sức bền và sức mạnh khi vận động thể thao.",
    "🫁 Phổi của bạn chứa khoảng 83% là nước để duy trì độ ẩm cho quá trình trao đổi khí diễn ra mượt mà.",
    "💩 Uống đủ nước kết hợp chất xơ là phương thuốc tự nhiên hoàn hảo nhất để bài trừ bệnh táo bón.",
    "😄 Uống nước thúc đẩy sản xuất Dopamine nhẹ, giúp cải thiện tâm trạng và giảm cảm giác gắt gỏng bất chợt.",
    "🦷 Nước giúp kích thích sản xuất nước bọt, hỗ trợ làm sạch vi khuẩn và bảo vệ men răng khỏi sâu răng.",
    "🌡️ Nước hoạt động như một hệ thống làm mát nội bộ, giúp điều hòa thân nhiệt qua việc tiết mồ hôi.",
    "☀️ Ngay cả khi ngồi phòng máy lạnh cả ngày, cơ thể bạn vẫn bị mất nước liên tục qua hơi thở và da đấy.",
    "🥑 Thiếu nước làm giảm khả năng hấp thụ các chất dinh dưỡng từ thức ăn vào máu của ruột non.",
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


def get_random_fact() -> str:
    """Fact tĩnh, dùng làm dự phòng khi Gemini API lỗi hoặc chưa cấu hình."""
    return random.choice(WATER_FACTS)
