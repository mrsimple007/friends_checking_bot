"""
certificate_command.py
Handles /certificate command – lets a user manually generate and download
their friendship certificate for any quiz result they have taken.
"""

import io
import asyncio
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from config import supabase
from start_handler import get_user_language, get_text

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────
# Localised strings
# ──────────────────────────────────────────────────────────────
CERT_TEXTS = {
    "uz": {
        "no_results":      "❌ Siz hali hech qanday testni topshirmagansiz.",
        "choose_result":   "🏅 Sertifikat olish uchun natijani tanlang:",
        "generating":      "⏳ Sertifikat tayyorlanmoqda...",
        "caption":         "🏅 Sizning do'stlik sertifikatingiz!",
        "error":           "❌ Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.",
        "cancel":          "❌ Bekor qilish",
    },
    "ru": {
        "no_results":      "❌ Вы ещё не прошли ни одного теста.",
        "choose_result":   "🏅 Выберите результат для получения сертификата:",
        "generating":      "⏳ Сертификат генерируется...",
        "caption":         "🏅 Ваш сертификат дружбы!",
        "error":           "❌ Произошла ошибка. Пожалуйста, попробуйте снова.",
        "cancel":          "❌ Отмена",
    },
    "en": {
        "no_results":      "❌ You haven't taken any tests yet.",
        "choose_result":   "🏅 Choose a result to get your certificate:",
        "generating":      "⏳ Generating your certificate...",
        "caption":         "🏅 Your friendship certificate!",
        "error":           "❌ An error occurred. Please try again.",
        "cancel":          "❌ Cancel",
    },
}


def _t(lang: str, key: str) -> str:
    return CERT_TEXTS.get(lang, CERT_TEXTS["en"])[key]


def _format_display_name(row: dict) -> str:
    first = row.get("first_name") or ""
    last  = row.get("last_name")  or ""
    uname = row.get("username")   or ""
    full  = f"{first} {last}".strip()
    if full and uname:
        return f"{full} (@{uname})"
    return full or (f"@{uname}" if uname else f"User {row.get('telegram_id', '?')}")


# ──────────────────────────────────────────────────────────────
# /certificate command
# ──────────────────────────────────────────────────────────────
async def certificate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the user their past test results so they can pick one for a cert."""
    user_id = update.effective_user.id
    lang    = get_user_language(user_id)

    try:
        results = (
            supabase.table("test_results")
            .select("test_id, score, created_at")
            .eq("user_id", str(user_id))
            .order("created_at", desc=True)
            .limit(10)
            .execute()
        )

        if not results.data:
            await update.message.reply_text(_t(lang, "no_results"), parse_mode=ParseMode.HTML)
            return

        keyboard = []
        for r in results.data:
            test_id = r["test_id"]
            score   = r["score"]
            # Try to resolve owner name
            try:
                test_row = (
                    supabase.table("tests")
                    .select("user_id")
                    .eq("id", test_id)
                    .execute()
                )
                if test_row.data:
                    owner_row = (
                        supabase.table("friends_users")
                        .select("first_name, last_name, username")
                        .eq("telegram_id", test_row.data[0]["user_id"])
                        .execute()
                    )
                    owner_name = (
                        _format_display_name(owner_row.data[0])
                        if owner_row.data
                        else "?"
                    )
                else:
                    owner_name = "?"
            except Exception:
                owner_name = "?"

            label = f"{score}% — {owner_name}"
            keyboard.append(
                [InlineKeyboardButton(label, callback_data=f"cert_pick_{test_id}")]
            )

        keyboard.append([InlineKeyboardButton(_t(lang, "cancel"), callback_data="cert_cancel")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            _t(lang, "choose_result"),
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML,
        )

    except Exception as e:
        logger.error(f"certificate_command error: {e}")
        await update.message.reply_text(_t(lang, "error"), parse_mode=ParseMode.HTML)


# ──────────────────────────────────────────────────────────────
# Callback: user tapped a result button
# ──────────────────────────────────────────────────────────────
async def certificate_select_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query   = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    lang    = get_user_language(user_id)

    if query.data == "cert_cancel":
        await query.edit_message_text("👌", parse_mode=ParseMode.HTML)
        return

    test_id = query.data.replace("cert_pick_", "")

    # Acknowledge immediately
    await query.edit_message_text(_t(lang, "generating"), parse_mode=ParseMode.HTML)

    try:
        # Fetch score
        result_row = (
            supabase.table("test_results")
            .select("score")
            .eq("test_id", test_id)
            .eq("user_id", str(user_id))
            .execute()
        )
        if not result_row.data:
            await query.edit_message_text(_t(lang, "error"), parse_mode=ParseMode.HTML)
            return

        score = result_row.data[0]["score"]

        # Fetch owner
        test_row = (
            supabase.table("tests")
            .select("user_id")
            .eq("id", test_id)
            .execute()
        )
        if not test_row.data:
            await query.edit_message_text(_t(lang, "error"), parse_mode=ParseMode.HTML)
            return

        test_owner_id = test_row.data[0]["user_id"]
        try:
            owner_row = (
                supabase.table("friends_users")
                .select("first_name, last_name, username")
                .eq("telegram_id", str(test_owner_id))
                .execute()
            )
            owner_display = (
                _format_display_name(owner_row.data[0])
                if owner_row.data
                else f"User {test_owner_id}"
            )
        except Exception:
            owner_display = f"User {test_owner_id}"

        taker_display = (
            update.effective_user.first_name or f"User {user_id}"
        )

        # Generate certificate in executor (blocking Pillow work)
        from certificate_generator import generate_certificate_image

        cert_bytes = await asyncio.get_event_loop().run_in_executor(
            None,
            generate_certificate_image,
            taker_display,
            owner_display,
            score,
            lang,
        )

        if not cert_bytes:
            await query.edit_message_text(_t(lang, "error"), parse_mode=ParseMode.HTML)
            return

        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=io.BytesIO(cert_bytes),
            caption=_t(lang, "caption"),
            parse_mode=ParseMode.HTML,
            filename="friendship_certificate.png",
        )
        logger.info(f"CERT_MANUAL: user={user_id} test={test_id} score={score}%")

    except Exception as e:
        logger.error(f"certificate_select_callback error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        try:
            await query.edit_message_text(_t(lang, "error"), parse_mode=ParseMode.HTML)
        except Exception:
            pass