"""
Share functionality for Friend Checking Bot with multi-language support
"""

import logging
import urllib.parse
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

logger = logging.getLogger(__name__)

# Import from main
from config import supabase

# Translations for share messages
SHARE_TRANSLATIONS = {
    "uz": {
        "share_text_plain": """🎮 Do'stlaringizni qanchalik yaxshi bilishingizni tekshiring!

🎯 Do'stlik testlari yarating va do'stlaringizni sinab ko'ring
🎂 Tug'ilgan kunlarni hech qachon esdan chiqarmang
✨ Qiziqarli va bepul!

📊 Natijalarga e'tibor qiling va kimning eng yaqin do'stingiz ekanligini bilib oling!

🚀 Men bilan qo'shiling va do'stlaringizni sinab ko'ring!""",
        
        "share_text_intro": "🎉 Bu mening havolam:",
        
        "share_message": """🔗 <b>Ulashing va do'stlaringizni taklif qiling!</b>

Sizning taklif havolangiz:
<code>{referral_link}</code>

<b>📱 Botni ulashing:</b>
Do'stlaringiz bilan botni ulashing va qiziqarli testlar yarating!

<b>🎯 Nima qilish mumkin:</b>
• Do'stlik testlari yaratish
• Tug'ilgan kunlarni eslab qolish
• Do'stlaringiz sizni qanchalik bilishini tekshirish

<b>📊 Sizning statistikangiz:</b>
• Taklif qilingan do'stlar: <b>{invited_count}</b> kishi""",
        
        "share_telegram": "📱 Telegram'da ulashish",
        "back_to_menu": "🔙 Menyuga qaytish",


        "share_test_text": """🎮 Bu mening do'stlik testim!

Testni ishlang va qanchalik yaxshi do'st ekanligingizni bilib oling! 🎯

Sizning natijangiz qanchalik yuqori bo'lsa, biz shunchalik yaqin do'stmiz! 💫

Omad! 🍀""",
        
        "share_test_intro": "🎯 Mening testim:",





    },



    
    
    "ru": {
        "share_text_plain": """🎮 Проверьте, насколько хорошо вы знаете своих друзей!

🎯 Создавайте тесты на дружбу и проверяйте друзей
🎂 Никогда не забывайте дни рождения
✨ Интересно и бесплатно!

📊 Смотрите результаты и узнайте, кто ваш лучший друг!

🚀 Присоединяйтесь и проверьте своих друзей!""",
        
        "share_text_intro": "🎉 Это моя ссылка:",
        
        "share_message": """🔗 <b>Поделитесь и пригласите друзей!</b>

Ваша реферальная ссылка:
<code>{referral_link}</code>

<b>📱 Поделитесь ботом:</b>
Поделитесь ботом с друзьями и создавайте интересные тесты!

<b>🎯 Что можно делать:</b>
• Создавать тесты на дружбу
• Запоминать дни рождения
• Проверять, как хорошо друзья вас знают

<b>📊 Ваша статистика:</b>
• Приглашенных друзей: <b>{invited_count}</b> человек""",
        
        "share_telegram": "📱 Поделиться в Telegram",
        "back_to_menu": "🔙 Назад в меню",


        "share_test_text": """🎮 Это мой тест на дружбу!

Пройдите тест и узнайте, насколько хорошо вы меня знаете! 🎯

Чем выше ваш результат, тем ближе мы друзья! 💫

Удачи! 🍀""",
        
        "share_test_intro": "🎯 Мой тест:",




    },
    
    "en": {
        "share_text_plain": """🎮 Check how well you know your friends!

🎯 Create friendship tests and test your friends
🎂 Never forget birthdays
✨ Fun and free!

📊 See the results and find out who's your best friend!

🚀 Join me and test your friends!""",
        
        "share_text_intro": "🎉 This is my link:",
        
        "share_message": """🔗 <b>Share and invite your friends!</b>

Your referral link:
<code>{referral_link}</code>

<b>📱 Share the bot:</b>
Share the bot with friends and create fun tests!

<b>🎯 What you can do:</b>
• Create friendship tests
• Remember birthdays
• Check how well friends know you

<b>📊 Your statistics:</b>
• Invited friends: <b>{invited_count}</b> people""",
        
        "share_telegram": "📱 Share on Telegram",
        "back_to_menu": "🔙 Back to Menu",


        "share_test_text": """🎮 This is my friendship test!

Take the test and find out how well you know me! 🎯

The higher your score, the closer we are as friends! 💫

Good luck! 🍀""",
        
        "share_test_intro": "🎯 My test:",



    }
}


def get_user_language(user_id: int) -> str:
    """Get user's language from database"""
    try:
        result = supabase.table('friends_users').select('language').eq('telegram_id', str(user_id)).execute()
        if result.data:
            return result.data[0]['language']
    except Exception as e:
        logger.error(f"Error getting user language: {e}")
    return 'en'


async def get_invited_users_count(user_id: int) -> int:
    """Get count of users invited by this user"""
    try:
        result = supabase.table('friends_users').select('id', count='exact').eq('invited_by', str(user_id)).execute()
        return result.count if result.count else 0
    except Exception as e:
        logger.error(f"Error getting invited count: {e}")
        return 0


async def share_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show share menu with referral link and statistics"""
    query = update.callback_query
    if query:
        await query.answer()
        user = query.from_user
    else:
        user = update.effective_user

    # Add typing indicator
    if query:
        await context.bot.send_chat_action(chat_id=query.message.chat_id, action="typing")
    elif update.message:
        await context.bot.send_chat_action(chat_id=update.message.chat_id, action="typing")

    language = get_user_language(user.id)
    
    # Get bot username
    bot_username = context.bot.username
    referral_link = f"https://t.me/{bot_username}?start=ref_{user.id}"

    # Get number of invited users
    invited_count = await get_invited_users_count(user.id)

    translations = SHARE_TRANSLATIONS.get(language, SHARE_TRANSLATIONS["en"])

    share_message = translations["share_message"].format(
        referral_link=referral_link,
        invited_count=invited_count
    )

    share_text_plain = translations["share_text_plain"]
    share_text_intro = translations["share_text_intro"]
    share_text_full = f"{share_text_intro}\n\n{referral_link}\n\n{share_text_plain}"
    share_text_encoded = urllib.parse.quote(share_text_full)

    # Create keyboard with share options
    share_button_text = translations["share_telegram"]
    back_button_text = translations["back_to_menu"]

    keyboard = [
        [InlineKeyboardButton(
            share_button_text,
            url=f"https://t.me/share/url?url={referral_link}&text={share_text_encoded}"
        )],
        [InlineKeyboardButton(
            back_button_text,
            callback_data="back_to_menu"
        )]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    if query:
        await query.edit_message_text(
            share_message,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    elif update.message:
        await update.message.reply_text(
            share_message,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )


async def back_to_main_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle back to main menu"""
    from main import show_main_menu, get_user_language
    
    query = update.callback_query
    await query.answer()
    
    lang = get_user_language(query.from_user.id)
    await show_main_menu(update, context, lang)