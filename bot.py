import logging
import os
from datetime import datetime
from collections import defaultdict

from telegram import Update, ChatPermissions
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ChatMemberHandler,
    filters,
    ContextTypes,
)
from telegram.constants import ChatMemberStatus

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Uyarı sayacı: {chat_id: {user_id: warn_count}}
warn_counts = defaultdict(lambda: defaultdict(int))
WARN_LIMIT = 3  # Kaç uyarıda ban atılacak

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")


# ─── Yardımcı Fonksiyonlar ───────────────────────────────────────────────────

async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    chat = update.effective_chat
    member = await context.bot.get_chat_member(chat.id, user_id)
    return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]


async def get_target_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reply veya argümandan hedef kullanıcıyı bulur."""
    message = update.effective_message
    if message.reply_to_message:
        return message.reply_to_message.from_user, None
    if context.args:
        try:
            user_id = int(context.args[0])
            user = await context.bot.get_chat_member(update.effective_chat.id, user_id)
            return user.user, None
        except Exception:
            return None, "❌ Kullanıcı bulunamadı. Reply at ya da geçerli bir ID gir."
    return None, "❌ Bir kullanıcıya reply at veya ID belirt."


# ─── /ban ────────────────────────────────────────────────────────────────────

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    executor = update.effective_user

    if not await is_admin(update, context, executor.id):
        await update.message.reply_text("🚫 Bu komutu kullanmak için admin olman gerekiyor.")
        return

    target, err = await get_target_user(update, context)
    if err:
        await update.message.reply_text(err)
        return

    if await is_admin(update, context, target.id):
        await update.message.reply_text("⚠️ Başka bir admini ban edemezsin.")
        return

    reason = " ".join(context.args[1:]) if context.args and len(context.args) > 1 else "Sebep belirtilmedi"
    await context.bot.ban_chat_member(chat.id, target.id)
    await update.message.reply_text(
        f"🔨 <b>{target.full_name}</b> banlandı!\n"
        f"👤 Admin: {executor.full_name}\n"
        f"📝 Sebep: {reason}",
        parse_mode="HTML"
    )


# ─── /unban ──────────────────────────────────────────────────────────────────

async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    executor = update.effective_user

    if not await is_admin(update, context, executor.id):
        await update.message.reply_text("🚫 Bu komutu kullanmak için admin olman gerekiyor.")
        return

    target, err = await get_target_user(update, context)
    if err:
        await update.message.reply_text(err)
        return

    await context.bot.unban_chat_member(chat.id, target.id, only_if_banned=True)
    await update.message.reply_text(
        f"✅ <b>{target.full_name}</b> ban'dan çıkarıldı!\n"
        f"👤 Admin: {executor.full_name}",
        parse_mode="HTML"
    )


# ─── /warn ───────────────────────────────────────────────────────────────────

async def warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    executor = update.effective_user

    if not await is_admin(update, context, executor.id):
        await update.message.reply_text("🚫 Bu komutu kullanmak için admin olman gerekiyor.")
        return

    target, err = await get_target_user(update, context)
    if err:
        await update.message.reply_text(err)
        return

    if await is_admin(update, context, target.id):
        await update.message.reply_text("⚠️ Başka bir admini uyaramazsın.")
        return

    reason = " ".join(context.args[1:]) if context.args and len(context.args) > 1 else "Sebep belirtilmedi"
    warn_counts[chat.id][target.id] += 1
    count = warn_counts[chat.id][target.id]

    if count >= WARN_LIMIT:
        await context.bot.ban_chat_member(chat.id, target.id)
        warn_counts[chat.id][target.id] = 0
        await update.message.reply_text(
            f"🔨 <b>{target.full_name}</b> {WARN_LIMIT} uyarı aldığı için otomatik olarak banlandı!\n"
            f"👤 Admin: {executor.full_name}",
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            f"⚠️ <b>{target.full_name}</b> uyarıldı! ({count}/{WARN_LIMIT})\n"
            f"👤 Admin: {executor.full_name}\n"
            f"📝 Sebep: {reason}",
            parse_mode="HTML"
        )


# ─── /unwarn ─────────────────────────────────────────────────────────────────

async def unwarn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    executor = update.effective_user

    if not await is_admin(update, context, executor.id):
        await update.message.reply_text("🚫 Bu komutu kullanmak için admin olman gerekiyor.")
        return

    target, err = await get_target_user(update, context)
    if err:
        await update.message.reply_text(err)
        return

    count = warn_counts[chat.id][target.id]
    if count == 0:
        await update.message.reply_text(f"ℹ️ <b>{target.full_name}</b> adlı kullanıcının aktif uyarısı yok.", parse_mode="HTML")
        return

    warn_counts[chat.id][target.id] = max(0, count - 1)
    new_count = warn_counts[chat.id][target.id]
    await update.message.reply_text(
        f"✅ <b>{target.full_name}</b> için bir uyarı silindi. ({new_count}/{WARN_LIMIT})\n"
        f"👤 Admin: {executor.full_name}",
        parse_mode="HTML"
    )


# ─── /mute ───────────────────────────────────────────────────────────────────

async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    executor = update.effective_user

    if not await is_admin(update, context, executor.id):
        await update.message.reply_text("🚫 Bu komutu kullanmak için admin olman gerekiyor.")
        return

    target, err = await get_target_user(update, context)
    if err:
        await update.message.reply_text(err)
        return

    if await is_admin(update, context, target.id):
        await update.message.reply_text("⚠️ Başka bir admini sustuuramazsın.")
        return

    reason = " ".join(context.args[1:]) if context.args and len(context.args) > 1 else "Sebep belirtilmedi"
    permissions = ChatPermissions(
        can_send_messages=False,
        can_send_media_messages=False,
        can_send_other_messages=False,
        can_add_web_page_previews=False,
    )
    await context.bot.restrict_chat_member(chat.id, target.id, permissions)
    await update.message.reply_text(
        f"🔇 <b>{target.full_name}</b> susturuldu!\n"
        f"👤 Admin: {executor.full_name}\n"
        f"📝 Sebep: {reason}",
        parse_mode="HTML"
    )


# ─── /unmute ─────────────────────────────────────────────────────────────────

async def unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    executor = update.effective_user

    if not await is_admin(update, context, executor.id):
        await update.message.reply_text("🚫 Bu komutu kullanmak için admin olman gerekiyor.")
        return

    target, err = await get_target_user(update, context)
    if err:
        await update.message.reply_text(err)
        return

    permissions = ChatPermissions(
        can_send_messages=True,
        can_send_media_messages=True,
        can_send_other_messages=True,
        can_add_web_page_previews=True,
    )
    await context.bot.restrict_chat_member(chat.id, target.id, permissions)
    await update.message.reply_text(
        f"🔊 <b>{target.full_name}</b> sesi açıldı!\n"
        f"👤 Admin: {executor.full_name}",
        parse_mode="HTML"
    )


# ─── /warns ──────────────────────────────────────────────────────────────────

async def warns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    target, err = await get_target_user(update, context)
    if err:
        await update.message.reply_text(err)
        return

    count = warn_counts[chat.id][target.id]
    await update.message.reply_text(
        f"📊 <b>{target.full_name}</b> uyarı durumu: {count}/{WARN_LIMIT}",
        parse_mode="HTML"
    )


# ─── Hoşgeldin / Gülegüle ─────────────────────────────────────────────────────

async def member_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = update.chat_member
    old_status = result.old_chat_member.status
    new_status = result.new_chat_member.status
    user = result.new_chat_member.user
    chat = result.chat

    joined = (
        old_status in [ChatMemberStatus.LEFT, ChatMemberStatus.BANNED]
        and new_status == ChatMemberStatus.MEMBER
    )
    left = (
        old_status == ChatMemberStatus.MEMBER
        and new_status in [ChatMemberStatus.LEFT, ChatMemberStatus.BANNED]
    )

    if joined:
        member_count = await context.bot.get_chat_member_count(chat.id)
        await context.bot.send_message(
            chat_id=chat.id,
            text=(
                f"👋 Hoş geldin, <b>{user.full_name}</b>!\n\n"
                f"🎉 <b>{chat.title}</b> grubuna katıldın.\n"
                f"👥 Artık grubumuzda <b>{member_count}</b> üye var!\n\n"
                f"📜 Lütfen grup kurallarına uyduğundan emin ol."
            ),
            parse_mode="HTML"
        )
    elif left:
        await context.bot.send_message(
            chat_id=chat.id,
            text=(
                f"😢 <b>{user.full_name}</b> gruptan ayrıldı.\n"
                f"Güle güle, tekrar bekleriz! 👋"
            ),
            parse_mode="HTML"
        )


# ─── /start & /help ──────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 <b>Grup Yönetim Botu</b> aktif!\n\n"
        "Komutlar için /help yazabilirsin.",
        parse_mode="HTML"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛠 <b>Kullanılabilir Komutlar</b>\n\n"
        "<b>🔨 Moderasyon (Admin):</b>\n"
        "/ban [reply/id] [sebep] — Kullanıcıyı banla\n"
        "/unban [reply/id] — Banı kaldır\n"
        "/warn [reply/id] [sebep] — Uyarı ver\n"
        "/unwarn [reply/id] — Uyarı sil\n"
        "/warns [reply/id] — Uyarı sayısını gör\n"
        "/mute [reply/id] [sebep] — Sustur\n"
        "/unmute [reply/id] — Sesi aç\n\n"
        "<b>ℹ️ Genel:</b>\n"
        "/start — Botu başlat\n"
        "/help — Bu mesajı göster\n\n"
        f"⚠️ {WARN_LIMIT} uyarı alan kullanıcı otomatik banlanır!",
        parse_mode="HTML"
    )


# ─── Ana Fonksiyon ───────────────────────────────────────────────────────────

def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN environment variable is not set!")

    app = Application.builder().token(BOT_TOKEN).build()

    # Komutlar
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("unban", unban))
    app.add_handler(CommandHandler("warn", warn))
    app.add_handler(CommandHandler("unwarn", unwarn))
    app.add_handler(CommandHandler("warns", warns))
    app.add_handler(CommandHandler("mute", mute))
    app.add_handler(CommandHandler("unmute", unmute))

    # Hoşgeldin / Gülegüle
    app.add_handler(ChatMemberHandler(member_change, ChatMemberHandler.CHAT_MEMBER))

    logger.info("✅ Bot başlatıldı...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
