"""
bot.py
File chính - khởi tạo bot Discord, xử lý reminder theo lịch,
nút bấm "Đã uống / Chưa uống", và slash command xem thống kê.

Mô hình multi-user: mỗi người tự gõ /dangky để nhận nhắc nhở,
phù hợp khi có nhiều người cùng dùng chung 1 bot (VD: bạn + người yêu).

Chạy: python bot.py
"""

import os
import io
import csv
import time
import random
import logging
from datetime import datetime, timedelta

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.jobstores.base import JobLookupError
import matplotlib
matplotlib.use("Agg")  # không cần giao diện đồ họa, chỉ xuất ảnh
import matplotlib.pyplot as plt

import database as db
import messages as msg

# ---------- Cấu hình & logging ----------
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

# Ép logging dùng giờ Việt Nam (UTC+7) thay vì giờ hệ thống server,
# vì time.localtime() mặc định phụ thuộc múi giờ OS của server (Railway).
logging.Formatter.converter = lambda *args: time.gmtime(time.time() + 7 * 3600)
log = logging.getLogger("water-bot")

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))
TIMEZONE = os.getenv("TIMEZONE", "Asia/Ho_Chi_Minh")
REMINDER_TIMES = [t.strip() for t in os.getenv("REMINDER_TIMES", "08:00,12:00,15:00,20:00").split(",")]

# Chuỗi nhắc "chưa bấm nút gì cả" - lặp mỗi bao nhiêu phút, tối đa mấy lần trước khi bỏ qua
BUTTON_REMINDER_INTERVAL = int(os.getenv("BUTTON_REMINDER_INTERVAL_MINUTES", "15"))
BUTTON_REMINDER_MAX = int(os.getenv("BUTTON_REMINDER_MAX", "2"))

# Chuỗi kiểm tra "đã uống chưa" sau khi bấm nút Chưa uống - lặp mỗi bao nhiêu phút, tối đa mấy lần
DRINK_CONFIRM_INTERVAL = int(os.getenv("DRINK_CONFIRM_INTERVAL_MINUTES", "5"))
DRINK_CONFIRM_MAX = int(os.getenv("DRINK_CONFIRM_MAX", "2"))

# Giờ bắt đầu im lặng, không nhắc thêm nữa (định dạng HH:MM)
_quiet_h, _quiet_m = map(int, os.getenv("QUIET_HOUR", "22:30").split(":"))
QUIET_HOUR_TUPLE = (_quiet_h, _quiet_m)

# Các mốc giờ gửi fact vui về uống nước - độc lập với lịch nhắc uống nước
FACTS_TIMES = [t.strip() for t in os.getenv("FACTS_TIMES", "07:00,11:30,15:00,21:00").split(",")]

# Nếu để trống, bot sẽ luôn dùng danh sách facts tĩnh trong messages.py thay vì gọi API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Prompt dùng để yêu cầu Gemini sinh fact - có thể đổi trực tiếp trên Railway (tab Variables)
# mà không cần sửa code/deploy lại.
PROMPT_FACT = os.getenv("PROMPT_FACT") or (
    "Viết đúng 1 câu fact ngắn gọn (dưới 40 từ), vui vẻ, bằng tiếng Việt, "
    "về lợi ích hoặc điều thú vị/hài hước liên quan tới việc uống nước. "
    "Có thể thêm 1 emoji phù hợp. Chỉ trả về đúng câu fact, không thêm lời dẫn hay giải thích gì khác."
)

# Danh sách Discord user ID được coi là admin (cách nhau bởi dấu phẩy).
# Đây là cơ chế phân quyền RIÊNG của bot, không dùng quyền "Administrator" của Discord server,
# nên 1 người có thể vừa là admin (theo bot) vừa dùng bot như user bình thường mà không xung đột,
# và không ai khác nhìn thấy được ai là admin (không lộ qua vai trò/role Discord).
ADMIN_USER_IDS = {uid.strip() for uid in os.getenv("ADMIN_USER_IDS", "").split(",") if uid.strip()}

if not DISCORD_TOKEN:
    raise RuntimeError("Chưa cấu hình DISCORD_TOKEN trong file .env")

# ---------- Khởi tạo bot ----------
intents = discord.Intents.default()
intents.message_content = False  # không cần đọc nội dung tin nhắn, chỉ dùng slash command + button

bot = commands.Bot(command_prefix="!", intents=intents)

# Scheduler dùng "persistent job store" - lưu toàn bộ lịch (kể cả chu kỳ nhắc lại
# đang dở) thẳng vào file SQLite, dùng chung ổ Volume với database chính.
# Nhờ vậy nếu bot restart (deploy code mới, Railway khởi động lại,...), mọi lịch
# nhắc đang dở sẽ tự động được khôi phục đúng như cũ, không bị mất.
_SCHEDULER_DB_PATH = os.getenv("DATABASE_PATH", "water_reminder.db")
scheduler = AsyncIOScheduler(
    timezone=TIMEZONE,
    jobstores={"default": SQLAlchemyJobStore(url=f"sqlite:///{_SCHEDULER_DB_PATH}")},
)


def vn_now() -> datetime:
    """
    Giờ hiện tại theo giờ Việt Nam, tính từ datetime.utcnow() + 7 giờ.
    Không dùng datetime.now() vì nó phụ thuộc múi giờ hệ điều hành của server
    (Railway có thể chạy ở UTC hoặc múi giờ khác), trong khi datetime.utcnow()
    luôn cho giờ UTC chuẩn bất kể server đặt ở đâu.
    """
    return datetime.utcnow() + timedelta(hours=7)


def is_admin(user_id) -> bool:
    """Kiểm tra user có nằm trong danh sách admin của bot không (không liên quan quyền Discord)."""
    return str(user_id) in ADMIN_USER_IDS


def is_quiet_hours() -> bool:
    """Từ QUIET_HOUR (mặc định 22:30) trở đi, không gửi thêm bất kỳ nhắc nhở nào nữa."""
    now = vn_now()
    return (now.hour, now.minute) >= QUIET_HOUR_TUPLE


# ---------- Giao diện nút bấm (View) ----------
def _cycle_job_id(user_id) -> str:
    """Mỗi user chỉ có tối đa 1 job chu kỳ nhắc đang chờ tại 1 thời điểm, dùng chung 1 ID để dễ hủy/thay thế."""
    return f"cycle_{user_id}"


def _cancel_cycle(user_id):
    """Hủy job chu kỳ nhắc đang chờ của user này, nếu có."""
    try:
        scheduler.remove_job(_cycle_job_id(user_id))
    except JobLookupError:
        pass


class WaterReminderView(discord.ui.View):
    """
    View chứa 2 nút: Đã uống / Chưa uống.
    timeout=None để nút không bao giờ hết hạn (Discord giới hạn 15 phút nếu không set None).

    Lưu ý: 1 tin nhắn nhắc nhở có thể gửi cho NHIỀU người đăng ký cùng lúc
    (VD: cả bạn và người yêu cùng dùng chung kênh). Ai bấm nút thì log cho
    chính người đó, không giới hạn chỉ 1 người cố định.
    """

    def __init__(self):
        super().__init__(timeout=None)

    async def _check_registered(self, interaction: discord.Interaction) -> bool:
        """Chỉ người đã /dangky mới được log qua nút bấm."""
        if not db.is_user_registered(interaction.user.id):
            await interaction.response.send_message(
                "Bạn chưa đăng ký nhận nhắc nhở nha, gõ lệnh `/dangky` trước đã 😉",
                ephemeral=True,
            )
            return False
        return True

    @discord.ui.button(label="✅ Đã uống", style=discord.ButtonStyle.success, custom_id="water_done")
    async def done_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_registered(interaction):
            return

        # Đã uống rồi -> hủy luôn mọi chu kỳ nhắc đang chờ của người này
        _cancel_cycle(interaction.user.id)

        db.log_water(interaction.user.id)
        today_count = db.get_today_count(interaction.user.id)
        streak_count = db.get_streak(interaction.user.id)

        # Trả lời riêng (ephemeral) cho người bấm, không disable nút chung
        # vì tin nhắn này có thể còn người khác chưa bấm.
        await interaction.response.send_message(
            f"{msg.get_random_praise()}\n"
            f"📊 Hôm nay bạn đã uống nước **{today_count} lần** rồi đó!\n"
            f"🔥 Streak: **{streak_count} ngày**",
            ephemeral=True,
        )

    @discord.ui.button(label="⏳ Chưa uống", style=discord.ButtonStyle.secondary, custom_id="water_not_yet")
    async def not_yet_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_registered(interaction):
            return

        await interaction.response.send_message(msg.get_random_nudge(), ephemeral=True)

        if is_quiet_hours():
            return  # Đã qua giờ im lặng, không lên lịch kiểm tra thêm nữa

        # Chuyển sang chuỗi "kiểm tra đã uống chưa", hủy chuỗi cũ (nếu có) và bắt đầu lại từ đầu
        _cancel_cycle(interaction.user.id)
        baseline = db.get_today_count(interaction.user.id)
        scheduler.add_job(
            check_drink_confirm,
            trigger="date",
            run_date=vn_now() + timedelta(minutes=DRINK_CONFIRM_INTERVAL),
            args=[interaction.user.id, baseline, 1],
            id=_cycle_job_id(interaction.user.id),
            replace_existing=True,
            misfire_grace_time=300,
        )


# ---------- Logic gửi nhắc nhở ----------
async def send_water_reminder():
    """Được scheduler gọi theo giờ đã cấu hình."""
    if is_quiet_hours():
        log.info("Đang trong giờ im lặng (từ %02d:%02d) - bỏ qua lượt nhắc này", *QUIET_HOUR_TUPLE)
        return

    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        log.error("Không tìm thấy channel ID %s - kiểm tra lại .env", CHANNEL_ID)
        return

    active_users = db.get_active_users()
    if not active_users:
        log.info("Chưa có ai đăng ký (/dangky) - bỏ qua lượt nhắc này")
        return

    mentions = " ".join(f"<@{user_id}>" for user_id, _ in active_users)
    text = f"{mentions} {msg.get_random_reminder()}"

    # 30% khả năng kèm thêm câu hỏi thăm sức khỏe cho đỡ nhàm
    if random.random() < 0.3:
        text += f"\n\n{msg.get_random_health_checkin()}"

    view = WaterReminderView()
    await channel.send(text, view=view)
    log.info("Đã gửi nhắc nhở lúc %s cho %d người", vn_now().strftime("%H:%M:%S"), len(active_users))

    # Với mỗi người, lên lịch riêng chuỗi "chưa bấm nút gì cả" - ghi lại baseline
    # (số lần đã uống hiện tại) để lát so sánh xem có uống thêm chưa.
    for user_id, _ in active_users:
        baseline = db.get_today_count(user_id)
        scheduler.add_job(
            check_no_response,
            trigger="date",
            run_date=vn_now() + timedelta(minutes=BUTTON_REMINDER_INTERVAL),
            args=[user_id, baseline, 1],
            id=_cycle_job_id(user_id),
            replace_existing=True,
            misfire_grace_time=300,
        )


async def check_no_response(user_id, baseline: int, repeat_number: int):
    """
    Chuỗi nhắc khi người dùng CHƯA BẤM NÚT GÌ CẢ.
    repeat_number: lần nhắc lại thứ mấy (1, 2, ...). Vượt quá BUTTON_REMINDER_MAX thì bỏ qua.
    """
    if is_quiet_hours():
        return

    if db.get_today_count(user_id) > baseline:
        return  # Đã uống rồi (qua /uong hoặc nút bấm) - không cần nhắc nữa

    if repeat_number > BUTTON_REMINDER_MAX:
        log.info("Đã nhắc tối đa cho user %s mà chưa phản hồi - bỏ qua", user_id)
        return

    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        return

    view = WaterReminderView()
    await channel.send(f"<@{user_id}> {msg.get_random_reminder()}", view=view)
    log.info("Nhắc lại (chưa bấm nút) lần %d cho user %s", repeat_number, user_id)

    scheduler.add_job(
        check_no_response,
        trigger="date",
        run_date=vn_now() + timedelta(minutes=BUTTON_REMINDER_INTERVAL),
        args=[user_id, baseline, repeat_number + 1],
        id=_cycle_job_id(user_id),
        replace_existing=True,
        misfire_grace_time=300,
    )


async def check_drink_confirm(user_id, baseline: int, check_number: int):
    """
    Chuỗi kiểm tra sau khi người dùng bấm "Chưa uống".
    check_number: lần hỏi lại thứ mấy (1, 2, ...). Vượt quá DRINK_CONFIRM_MAX thì bỏ qua.
    """
    if is_quiet_hours():
        return

    if db.get_today_count(user_id) > baseline:
        return  # Đã uống rồi - không cần hỏi nữa

    if check_number > DRINK_CONFIRM_MAX:
        log.info("Đã hỏi tối đa cho user %s mà vẫn chưa uống - bỏ qua", user_id)
        return

    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        return

    view = WaterReminderView()
    await channel.send(f"<@{user_id}> {msg.get_random_followup()}", view=view)
    log.info("Hỏi lại (đã uống chưa) lần %d cho user %s", check_number, user_id)

    scheduler.add_job(
        check_drink_confirm,
        trigger="date",
        run_date=vn_now() + timedelta(minutes=DRINK_CONFIRM_INTERVAL),
        args=[user_id, baseline, check_number + 1],
        id=_cycle_job_id(user_id),
        replace_existing=True,
        misfire_grace_time=300,
    )


async def generate_fact_via_gemini():
    """
    Gọi Gemini API sinh 1 fact vui về uống nước.
    Trả về None nếu chưa cấu hình GEMINI_API_KEY hoặc gọi API lỗi bất kỳ lý do gì
    (mất mạng, hết quota, sai key,...) - để hàm gọi nó tự fallback về danh sách tĩnh.
    """
    if not GEMINI_API_KEY:
        return None

    try:
        from google import genai  # import trong hàm để không bắt buộc cài nếu không dùng tính năng này

        client = genai.Client(api_key=GEMINI_API_KEY)
        response = await client.aio.models.generate_content(
            model="gemini-3.5-flash",
            contents=PROMPT_FACT,
        )
        text = (response.text or "").strip()
        return text if text else None
    except Exception as e:
        log.warning("Gọi Gemini API lỗi, sẽ dùng fact dự phòng: %s", e)
        return None


async def get_water_fact() -> str:
    """Ưu tiên fact từ Gemini, lỗi thì tự động dùng fact tĩnh trong messages.py."""
    fact = await generate_fact_via_gemini()
    return fact if fact else msg.get_random_fact()


async def send_water_fact():
    """Gửi 1 fact vui về uống nước vào kênh, độc lập với lịch nhắc uống nước (không kèm nút bấm)."""
    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        log.error("Không tìm thấy channel ID %s - kiểm tra lại .env", CHANNEL_ID)
        return

    fact = await get_water_fact()
    await channel.send(f"💡 **Fact vui về nước:**\n{fact}")
    log.info("Đã gửi fact lúc %s", vn_now().strftime("%H:%M:%S"))


def setup_scheduler():
    """Đăng ký các job nhắc nhở theo REMINDER_TIMES trong .env"""
    for time_str in REMINDER_TIMES:
        try:
            hour, minute = map(int, time_str.split(":"))
        except ValueError:
            log.warning("Bỏ qua giờ nhắc không hợp lệ: %s", time_str)
            continue

        scheduler.add_job(
            send_water_reminder,
            trigger=CronTrigger(hour=hour, minute=minute),
            id=f"reminder_{time_str}",
            replace_existing=True,
        )
        log.info("Đã đăng ký nhắc nhở lúc %s hằng ngày", time_str)

    for time_str in FACTS_TIMES:
        try:
            hour, minute = map(int, time_str.split(":"))
        except ValueError:
            log.warning("Bỏ qua giờ fact không hợp lệ: %s", time_str)
            continue

        scheduler.add_job(
            send_water_fact,
            trigger=CronTrigger(hour=hour, minute=minute),
            id=f"fact_{time_str}",
            replace_existing=True,
        )
        log.info("Đã đăng ký gửi fact lúc %s hằng ngày", time_str)


# ---------- Sự kiện bot ----------
@bot.event
async def on_ready():
    db.init_db()

    # Đăng ký lại view "vĩnh viễn" để nút vẫn hoạt động sau khi bot restart
    bot.add_view(WaterReminderView())

    if not scheduler.running:
        setup_scheduler()
        scheduler.start()

    try:
        synced = await bot.tree.sync()
        log.info("Đã đồng bộ %d slash command(s)", len(synced))
    except Exception as e:
        log.error("Lỗi khi đồng bộ slash command: %s", e)

    log.info("Bot đã sẵn sàng: %s", bot.user)


# ---------- Slash Commands ----------
@bot.tree.command(name="dangky", description="Đăng ký nhận nhắc nhở uống nước từ bot")
async def dangky(interaction: discord.Interaction):
    is_new = db.register_user(interaction.user.id, interaction.user.display_name)
    if is_new:
        await interaction.response.send_message(
            "🎉 Đăng ký thành công! Từ giờ bạn sẽ được nhắc uống nước theo lịch nha.\n"
            "Muốn ngừng nhận thì gõ `/huy`."
        )
    else:
        await interaction.response.send_message("Bạn đã đăng ký từ trước rồi nha 😉")


@bot.tree.command(name="huy", description="Ngừng nhận nhắc nhở uống nước")
async def huy(interaction: discord.Interaction):
    db.unregister_user(interaction.user.id)
    await interaction.response.send_message(
        "Đã ngừng nhắc nhở. Lịch sử uống nước của bạn vẫn được lưu, "
        "muốn nhận lại thì gõ `/dangky` bất cứ lúc nào nha."
    )


@bot.tree.command(name="uong", description="Ghi nhận thủ công 1 lần đã uống nước")
async def uong(interaction: discord.Interaction):
    db.log_water(interaction.user.id)
    today_count = db.get_today_count(interaction.user.id)
    await interaction.response.send_message(
        f"{msg.get_random_praise()}\n📊 Hôm nay đã uống nước **{today_count} lần**."
    )


@bot.tree.command(name="homnay", description="Xem số lần đã uống nước hôm nay")
async def homnay(interaction: discord.Interaction):
    today_count = db.get_today_count(interaction.user.id)
    streak = db.get_streak(interaction.user.id)
    await interaction.response.send_message(
        f"📊 Hôm nay bạn đã uống nước **{today_count} lần** rồi!\n"
        f"🔥 Streak hiện tại: **{streak} ngày** liên tục"
    )


@bot.tree.command(name="streak", description="Xem chuỗi ngày uống nước liên tục của bạn")
async def streak(interaction: discord.Interaction):
    streak_count = db.get_streak(interaction.user.id)
    if streak_count == 0:
        await interaction.response.send_message(
            "Chưa có streak nào cả, uống nước ngay hôm nay để bắt đầu chuỗi mới nha! 💧"
        )
    else:
        await interaction.response.send_message(
            f"🔥 Bạn đang giữ streak **{streak_count} ngày** liên tục uống nước! Cố lên nha!"
        )


@bot.tree.command(name="test", description="[Test] Gửi thử tin nhắn nhắc nhở ngay lập tức, không cần đợi tới giờ")
async def test_reminder(interaction: discord.Interaction):
    await interaction.response.send_message("Đang gửi thử tin nhắn nhắc nhở... ⏳", ephemeral=True)
    await send_water_reminder()


@bot.tree.command(name="testfact", description="[Test] Gửi thử 1 fact vui về uống nước ngay lập tức")
async def testfact(interaction: discord.Interaction):
    await interaction.response.send_message("Đang gửi thử fact... ⏳", ephemeral=True)
    await send_water_fact()


@bot.tree.command(name="xuatdata", description="Xuất toàn bộ dữ liệu thô ra file CSV")
async def xuatdata(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    # --- File 1: water_logs.csv ---
    logs = db.get_all_water_logs()
    logs_buffer = io.StringIO()
    writer = csv.writer(logs_buffer)
    writer.writerow(["user_id", "display_name", "timestamp_vn"])
    for user_id, display_name, timestamp in logs:
        vn_timestamp = timestamp + timedelta(hours=7)
        writer.writerow([user_id, display_name or "", vn_timestamp.isoformat()])
    logs_bytes = io.BytesIO(logs_buffer.getvalue().encode("utf-8-sig"))  # utf-8-sig để Excel đọc đúng tiếng Việt

    # --- File 2: users.csv ---
    users = db.get_all_users_raw()
    users_buffer = io.StringIO()
    writer = csv.writer(users_buffer)
    writer.writerow(["user_id", "display_name", "is_active"])
    for user_id, display_name, is_active in users:
        writer.writerow([user_id, display_name or "", is_active])
    users_bytes = io.BytesIO(users_buffer.getvalue().encode("utf-8-sig"))

    await interaction.followup.send(
        content=f"📦 Đã xuất dữ liệu: **{len(logs)} lượt uống nước**, **{len(users)} người dùng**.",
        files=[
            discord.File(logs_bytes, filename="water_logs.csv"),
            discord.File(users_bytes, filename="users.csv"),
        ],
        ephemeral=True,
    )


@bot.tree.command(name="thongke", description="Xem biểu đồ uống nước 7 ngày gần nhất")
async def thongke(interaction: discord.Interaction):
    await interaction.response.defer()  # vẽ biểu đồ có thể mất >3s, cần defer trước

    stats = db.get_last_n_days_stats(interaction.user.id, n_days=7)
    days = list(stats.keys())
    counts = list(stats.values())

    fig, ax = plt.subplots(figsize=(8, 4.5))
    bars = ax.bar(days, counts, color="#4FC3F7")
    ax.set_title("Số lần uống nước - 7 ngày gần nhất", fontsize=14, fontweight="bold")
    ax.set_ylabel("Số lần")
    ax.set_ylim(bottom=0)

    # Ghi số lên đầu mỗi cột cho dễ đọc
    for bar, count in zip(bars, counts):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.1,
            str(count),
            ha="center",
            fontsize=10,
        )

    plt.tight_layout()

    buffer = io.BytesIO()
    plt.savefig(buffer, format="png", dpi=120)
    buffer.seek(0)
    plt.close(fig)

    file = discord.File(buffer, filename="thongke.png")
    total = sum(counts)
    avg = total / len(counts) if counts else 0

    await interaction.followup.send(
        content=f"📈 Trung bình **{avg:.1f} lần/ngày** trong 7 ngày qua.",
        file=file,
    )


@bot.tree.command(name="huongdan", description="Đăng hướng dẫn sử dụng bot vào kênh này")
async def huongdan(interaction: discord.Interaction):
    guide = (
        "## 💧 Hướng dẫn dùng Stay Hydrated Bot\n\n"
        "**Bước 1 - Đăng ký (bắt buộc trước tiên):**\n"
        "`/dangky` — đăng ký nhận nhắc nhở uống nước theo lịch cố định trong ngày.\n\n"
        "**Các lệnh chính:**\n"
        "• `/uong` — ghi nhận thủ công 1 lần đã uống nước (không cần đợi bot nhắc)\n"
        "• `/homnay` — xem số lần đã uống nước hôm nay + streak hiện tại\n"
        "• `/streak` — xem chuỗi ngày uống nước liên tục\n"
        "• `/thongke` — xem biểu đồ 7 ngày gần nhất\n"
        "• `/xuatdata` — xuất toàn bộ lịch sử ra file CSV (mở bằng Excel)\n"
        "• `/huy` — ngừng nhận nhắc nhở (lịch sử vẫn được giữ, đăng ký lại bất cứ lúc nào)\n\n"
        "**Khi bot nhắc nhở:** sẽ có 2 nút **✅ Đã uống** / **⏳ Chưa uống** ngay dưới tin nhắn, bấm trực tiếp là được, không cần gõ lệnh.\n\n"
        "**Nếu quên bấm nút:** bot sẽ tự nhắc lại sau 1 khoảng thời gian nếu thấy bạn vẫn chưa uống thêm lần nào 💧"
    )
    await interaction.response.send_message(guide)


_CATEGORY_CHOICES = [
    app_commands.Choice(name="Nhắc nhở uống nước", value="reminder"),
    app_commands.Choice(name="Hỏi thăm sức khỏe", value="health"),
    app_commands.Choice(name="Khen ngợi (khi bấm Đã uống)", value="praise"),
    app_commands.Choice(name="Nhắc khi bấm Chưa uống", value="nudge"),
    app_commands.Choice(name="Hỏi lại đã uống chưa", value="followup"),
]


@bot.tree.command(name="themtinnhan", description="[Admin] Thêm 1 tin nhắn tùy chỉnh vào loại đã chọn")
@app_commands.describe(loai="Loại tin nhắn", noi_dung="Nội dung tin nhắn muốn thêm")
@app_commands.choices(loai=_CATEGORY_CHOICES)
async def themtinnhan(interaction: discord.Interaction, loai: app_commands.Choice[str], noi_dung: str):
    if not is_admin(interaction.user.id):
        await interaction.response.send_message("Lệnh này chỉ dành cho admin thôi nha 😉", ephemeral=True)
        return

    message_id = db.add_custom_message(loai.value, noi_dung, interaction.user.id)
    await interaction.response.send_message(
        f"✅ Đã thêm tin nhắn tùy chỉnh (ID: `{message_id}`) vào loại **{loai.name}**:\n> {noi_dung}",
        ephemeral=True,
    )


@bot.tree.command(name="xemtinnhan", description="[Admin] Xem danh sách tin nhắn (mặc định + tùy chỉnh) theo loại")
@app_commands.describe(loai="Loại tin nhắn muốn xem")
@app_commands.choices(loai=_CATEGORY_CHOICES)
async def xemtinnhan(interaction: discord.Interaction, loai: app_commands.Choice[str]):
    if not is_admin(interaction.user.id):
        await interaction.response.send_message("Lệnh này chỉ dành cho admin thôi nha 😉", ephemeral=True)
        return

    builtin = msg.CATEGORY_TO_BUILTIN.get(loai.value, [])
    custom = db.get_custom_messages(loai.value)

    lines = [f"## Danh sách tin nhắn - {loai.name}", "", f"**Mặc định ({len(builtin)}):**"]
    lines += [f"• {text}" for text in builtin]
    lines.append("")
    lines.append(f"**Tùy chỉnh ({len(custom)}):**")
    if custom:
        lines += [f"• `ID {mid}` — {text}" for mid, text in custom]
    else:
        lines.append("_(chưa có tin nhắn tùy chỉnh nào)_")

    await interaction.response.send_message("\n".join(lines), ephemeral=True)


@bot.tree.command(name="xoatinnhan", description="[Admin] Xóa 1 tin nhắn tùy chỉnh theo ID")
@app_commands.describe(id="ID tin nhắn tùy chỉnh muốn xóa (xem qua /xemtinnhan)")
async def xoatinnhan(interaction: discord.Interaction, id: int):
    if not is_admin(interaction.user.id):
        await interaction.response.send_message("Lệnh này chỉ dành cho admin thôi nha 😉", ephemeral=True)
        return

    success = db.remove_custom_message(id)
    if success:
        await interaction.response.send_message(f"🗑️ Đã xóa tin nhắn tùy chỉnh ID `{id}`.", ephemeral=True)
    else:
        await interaction.response.send_message(f"Không tìm thấy tin nhắn tùy chỉnh ID `{id}`.", ephemeral=True)


@bot.tree.command(name="thongbao", description="[Admin] Đăng thông báo cập nhật mới của bot vào kênh này")
@app_commands.describe(noi_dung="Nội dung cập nhật muốn thông báo")
async def thongbao(interaction: discord.Interaction, noi_dung: str):
    if not is_admin(interaction.user.id):
        await interaction.response.send_message(
            "Lệnh này chỉ dành cho admin thôi nha 😉", ephemeral=True
        )
        return

    active_users = db.get_active_users()
    mentions = " ".join(f"<@{uid}>" for uid, _ in active_users) if active_users else ""

    text = f"## 📢 Cập nhật mới\n\n{noi_dung}"
    if mentions:
        text += f"\n\n{mentions}"

    await interaction.response.send_message(text)


# ---------- Chạy bot ----------
if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
