"""
Premium subscription handler for Friend Checking Bot with multi-language support
"""

import logging
from datetime import datetime, timezone
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from config import ADMIN_CHAT_ID, ADMIN_USERNAME, CARD_NUMBER, NOTIFICATION_ADMIN_IDS

logger = logging.getLogger(__name__)

# Import from main
from config import supabase

# Premium subscription prices (in UZS)
PREMIUM_PRICES = {
    "1_month": 15000,
    "3_months": 40000,
    "6_months": 75000,
    "1_year": 140000,
}



# Translations
PREMIUM_TRANSLATIONS = {
    "uz": {
        "premium_title": "⭐ <b>Premium obuna</b>",
        "premium_description": """
🎯 <b>Premium afzalliklari:</b>

🎂 <b>Cheksiz tug'ilgan kunlar</b>
   • Istalgancha tug'ilgan kun saqlang
   • Hech qachon esdan chiqarmang

✨ <b>Cheksiz testlar</b>
   • Istalgancha test yarating
   • Do'stlaringizni sinab ko'ring

🎨 <b>Maxsus dizaynlar</b>
   • Chiroyli test shablon
   • Shaxsiy stilingiz

📊 <b>Batafsil statistika</b>
   • Barcha natijalarga kirish
   • Eng yaxshi do'stlaringizni ko'ring

🔔 <b>Eslatmalar</b>
   • Tug'ilgan kunlar haqida xabarnomalar
   • Tabriknoma generatsiya

<b>Tarif rejalarini tanlang:</b>
""",
        "select_plan": "Tarif rejani tanlang:",
        "month_1": "1 oy - 15,000 UZS",
        "months_3": "3 oy - 40,000 UZS",
        "months_6": "6 oy - 75,000 UZS",
        "year_1": "1 yil - 140,000 UZS",
        "payment_instructions": """
💳 <b>To'lov ma'lumotlari</b>

💰 <b>Summa:</b> {amount} UZS
📅 <b>Muddat:</b> {period}

<b>💳 Karta raqami:</b>
<code>{card_number}</code>


<b>📋 To'lov qilish uchun:</b>
1️⃣ Yuqoridagi summani kartaga o'tkazing
2️⃣ To'lov chekini adminga yuboring: {admin_username}
3️⃣ Tasdiqlashni kuting (odatda 5-10 daqiqa)

⚠️ <b>Muhim:</b> Chekni 30 daqiqa ichida yuboring!
""",
        "send_receipt": "📤 Chekni yuborish",
        "payment_sent": """
✅ <b>To'lov so'rovi yuborildi!</b>

💰 Summa: <b>{amount} UZS</b>
📅 Muddat: <b>{period}</b>

⏳ Admin tasdiqlashini kuting.
📱 Tasdiqlangach sizga xabar beramiz!
""",
        "payment_approved": """
🎉 <b>To'lov tasdiqlandi!</b>

⭐ Sizning Premium obunangiz faollashtirildi!

<b>Obuna ma'lumotlari:</b>
📅 Muddat: {period}
⏰ Tugash sanasi: {expiry_date}

Endi barcha Premium imkoniyatlardan foydalanishingiz mumkin! 🚀
""",
        "payment_rejected": """
❌ <b>To'lov rad etildi!</b>

Iltimos, agar xatolik bo'lsa {admin_username} bilan bog'laning.
""",
        "back": "« Orqaga",
        "already_premium": """
⭐ <b>Siz allaqachon Premium foydalanuvchisiz!</b>

<b>Obuna ma'lumotlari:</b>
📅 Tugash sanasi: {expiry_date}

Obunangizni yangilash uchun admin bilan bog'laning: {admin_username}
""",
    },
    
    "ru": {
        "premium_title": "⭐ <b>Premium подписка</b>",
        "premium_description": """
🎯 <b>Преимущества Premium:</b>

🎂 <b>Неограниченные дни рождения</b>
   • Сохраняйте сколько хотите
   • Никогда не забывайте

✨ <b>Неограниченные тесты</b>
   • Создавайте любые тесты
   • Проверяйте друзей

🎨 <b>Специальные дизайны</b>
   • Красивые шаблоны тестов
   • Ваш личный стиль

📊 <b>Подробная статистика</b>
   • Доступ ко всем результатам
   • Смотрите лучших друзей

🔔 <b>Напоминания</b>
   • Уведомления о днях рождения
   • Генерация поздравлений

<b>Выберите тарифный план:</b>
""",
        "select_plan": "Выберите тарифный план:",
        "month_1": "1 месяц - 15,000 UZS",
        "months_3": "3 месяца - 40,000 UZS",
        "months_6": "6 месяцев - 75,000 UZS",
        "year_1": "1 год - 140,000 UZS",
        "payment_instructions": """
💳 <b>Платежная информация</b>

💰 <b>Сумма:</b> {amount} UZS
📅 <b>Период:</b> {period}

<b>💳 Номер карты:</b>
<code>{card_number}</code>

<b>📋 Для оплаты:</b>
1️⃣ Переведите указанную сумму на карту
2️⃣ Отправьте чек админу: {admin_username}
3️⃣ Дождитесь подтверждения (обычно 5-10 минут)

⚠️ <b>Важно:</b> Отправьте чек в течение 30 минут!
""",
        "send_receipt": "📤 Отправить чек",
        "payment_sent": """
✅ <b>Запрос на оплату отправлен!</b>

💰 Сумма: <b>{amount} UZS</b>
📅 Период: <b>{period}</b>

⏳ Ожидайте подтверждения админа.
📱 Мы уведомим вас после подтверждения!
""",
        "payment_approved": """
🎉 <b>Платеж подтвержден!</b>

⭐ Ваша Premium подписка активирована!

<b>Детали подписки:</b>
📅 Период: {period}
⏰ Дата окончания: {expiry_date}

Теперь вы можете пользоваться всеми Premium возможностями! 🚀
""",
        "payment_rejected": """
❌ <b>Платеж отклонен!</b>

Пожалуйста, свяжитесь с поддержкой {admin_username}, если это ошибка.
""",
        "back": "« Назад",
        "already_premium": """
⭐ <b>Вы уже Premium пользователь!</b>

<b>Детали подписки:</b>
📅 Дата окончания: {expiry_date}

Для продления подписки свяжитесь с админом: {admin_username}
""",
    },
    
    "en": {
        "premium_title": "⭐ <b>Premium Subscription</b>",
        "premium_description": """
🎯 <b>Premium Benefits:</b>

🎂 <b>Unlimited Birthdays</b>
   • Save as many as you want
   • Never forget

✨ <b>Unlimited Tests</b>
   • Create any tests
   • Test your friends

🎨 <b>Special Designs</b>
   • Beautiful test templates
   • Your personal style

📊 <b>Detailed Statistics</b>
   • Access to all results
   • See your best friends

🔔 <b>Reminders</b>
   • Birthday notifications
   • Wish generation

<b>Choose a plan:</b>
""",
        "select_plan": "Choose a plan:",
        "month_1": "1 month - 15,000 UZS",
        "months_3": "3 months - 40,000 UZS",
        "months_6": "6 months - 75,000 UZS",
        "year_1": "1 year - 140,000 UZS",
        "payment_instructions": """
💳 <b>Payment Information</b>

💰 <b>Amount:</b> {amount} UZS
📅 <b>Period:</b> {period}

<b>💳 Card Number:</b>
<code>{card_number}</code>

<b>📋 To pay:</b>
1️⃣ Transfer the amount to the card
2️⃣ Send receipt to admin: {admin_username}
3️⃣ Wait for confirmation (usually 5-10 minutes)

⚠️ <b>Important:</b> Send receipt within 30 minutes!
""",
        "send_receipt": "📤 Send receipt",
        "payment_sent": """
✅ <b>Payment request sent!</b>

💰 Amount: <b>{amount} UZS</b>
📅 Period: <b>{period}</b>

⏳ Waiting for admin confirmation.
📱 We'll notify you after confirmation!
""",
        "payment_approved": """
🎉 <b>Payment Approved!</b>

⭐ Your Premium subscription is activated!

<b>Subscription Details:</b>
📅 Period: {period}
⏰ Expiry Date: {expiry_date}

Now you can use all Premium features! 🚀
""",
        "payment_rejected": """
❌ <b>Payment Rejected!</b>

Please contact support {admin_username} if this is an error.
""",
        "back": "« Back",
        "already_premium": """
⭐ <b>You are already a Premium user!</b>

<b>Subscription Details:</b>
📅 Expiry Date: {expiry_date}

To renew your subscription, contact admin: {admin_username}
""",
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


def get_period_name(plan_key: str, lang: str) -> str:
    """Get period name in user's language"""
    period_names = {
        "uz": {
            "1_month": "1 oy",
            "3_months": "3 oy",
            "6_months": "6 oy",
            "1_year": "1 yil"
        },
        "ru": {
            "1_month": "1 месяц",
            "3_months": "3 месяца",
            "6_months": "6 месяцев",
            "1_year": "1 год"
        },
        "en": {
            "1_month": "1 month",
            "3_months": "3 months",
            "6_months": "6 months",
            "1_year": "1 year"
        }
    }
    return period_names.get(lang, period_names["en"]).get(plan_key, plan_key)


async def premium_info_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show premium subscription options"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    lang = get_user_language(user_id)
    
    # Check if user is already premium
    try:
        result = supabase.table('friends_users').select('is_premium, premium_until').eq('telegram_id', str(user_id)).execute()
        if result.data and result.data[0].get('is_premium'):
            premium_until = result.data[0].get('premium_until')
            if premium_until:
                expiry_date = datetime.fromisoformat(premium_until.replace('Z', '+00:00')).strftime('%d.%m.%Y')
                text = PREMIUM_TRANSLATIONS[lang]["already_premium"].format(
                    expiry_date=expiry_date,
                    admin_username=ADMIN_USERNAME
                )
                keyboard = [[InlineKeyboardButton(
                    PREMIUM_TRANSLATIONS[lang]["back"],
                    callback_data="back_to_menu"
                )]]
                await query.edit_message_text(
                    text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode=ParseMode.HTML
                )
                return
    except Exception as e:
        logger.error(f"Error checking premium status: {e}")
    
    # Show premium plans
    text = PREMIUM_TRANSLATIONS[lang]["premium_title"] + "\n\n"
    text += PREMIUM_TRANSLATIONS[lang]["premium_description"]
    
    keyboard = [
        [InlineKeyboardButton(
            PREMIUM_TRANSLATIONS[lang]["month_1"],
            callback_data="subscribe_1_month"
        )],
        [InlineKeyboardButton(
            PREMIUM_TRANSLATIONS[lang]["months_3"],
            callback_data="subscribe_3_months"
        )],
        [InlineKeyboardButton(
            PREMIUM_TRANSLATIONS[lang]["months_6"],
            callback_data="subscribe_6_months"
        )],
        [InlineKeyboardButton(
            PREMIUM_TRANSLATIONS[lang]["year_1"],
            callback_data="subscribe_1_year"
        )],
        [InlineKeyboardButton(
            PREMIUM_TRANSLATIONS[lang]["back"],
            callback_data="back_to_menu"
        )]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )


async def subscribe_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle subscription plan selection"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    username = query.from_user.username or query.from_user.first_name
    lang = get_user_language(user_id)
    
    # Extract plan from callback data
    plan_key = query.data.replace("subscribe_", "")
    
    if plan_key not in PREMIUM_PRICES:
        await query.answer("❌ Invalid plan", show_alert=True)
        return
    
    amount = PREMIUM_PRICES[plan_key]
    period = get_period_name(plan_key, lang)
    
    # Show payment instructions
    text = PREMIUM_TRANSLATIONS[lang]["payment_instructions"].format(
        amount=f"{amount:,}",
        period=period,
        card_number=CARD_NUMBER,
        admin_username=ADMIN_USERNAME
    )
    
    keyboard = [
        [InlineKeyboardButton(
            PREMIUM_TRANSLATIONS[lang]["send_receipt"],
            url=f"https://t.me/{ADMIN_USERNAME.replace('@', '')}"
        )],
        [InlineKeyboardButton(
            PREMIUM_TRANSLATIONS[lang]["back"],
            callback_data="premium"
        )]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )
    
    # Send confirmation to user
    confirmation_text = PREMIUM_TRANSLATIONS[lang]["payment_sent"].format(
        amount=f"{amount:,}",
        period=period
    )
    
    await context.bot.send_message(
        chat_id=user_id,
        text=confirmation_text,
        parse_mode=ParseMode.HTML
    )
    
    # Send notification to all admins
    admin_notification = f"""
🔔 <b>Yangi Premium so'rov!</b>

👤 <b>Foydalanuvchi:</b> {username} (ID: {user_id})
💰 <b>Summa:</b> {amount:,} UZS
📅 <b>Tarif:</b> {period}

Foydalanuvchi to'lov chekini yuboradi.
"""
    
    for admin_id in NOTIFICATION_ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=int(admin_id),
                text=admin_notification,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Error notifying admin {admin_id}: {e}")
    
    logger.info(f"User {user_id} requested {plan_key} subscription for {amount} UZS")


async def activate_premium(user_id: int, months: int):
    """Activate premium subscription for user"""
    try:
        from dateutil.relativedelta import relativedelta
        
        # Calculate expiry date
        expiry_date = datetime.now(timezone.utc) + relativedelta(months=months)
        
        # Update user
        supabase.table('friends_users').update({
            'is_premium': True,
            'premium_until': expiry_date.isoformat()
        }).eq('telegram_id', str(user_id)).execute()
        
        logger.info(f"Premium activated for user {user_id} until {expiry_date}")
        return True
    except Exception as e:
        logger.error(f"Error activating premium: {e}")
        return False