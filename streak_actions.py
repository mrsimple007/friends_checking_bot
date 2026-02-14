import logging
import random
from datetime import datetime, timezone
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters
from telegram.constants import ParseMode
from config import supabase
from friendship_streaks import (
    get_or_create_streak, update_streak, get_user_friends,
    get_streak_text, DAILY_QUESTIONS, FRIEND_INFO_QUESTIONS, GUESS_QUESTIONS
)
import urllib.parse



logger = logging.getLogger(__name__)

# Conversation states
ANSWERING_DAILY_Q = 100
REMEMBERING_FRIEND = 101


STREAK_QUOTES = {
    'uz': [
        "Do'stlik - bu har kuni yangilanishi kerak bo'lgan gul.",
        "Yaqin do'st - bu ikkinchi o'zing.",
        "Do'stlikni saqlash - bu baxt kaliti.",
        "Har kunlik muloqot do'stlikni mustahkamlaydi.",
        "Haqiqiy do'stlik vaqt sinovi bilan tekshiriladi.",
        "Do'st ko'nglida - ko'ngilning ko'zgusi.",
        "Yaxshi do'st - eng qimmatli xazina.",
        "Do'stlik - bu hayotning eng go'zal in'omi.",
        "Sodiq do'st - oltin topilmasi.",
        "Do'stlar bilan vaqt - eng yaxshi vaqt!",
    ],
    'ru': [
        "Дружба - это цветок, который нужно поливать каждый день.",
        "Близкий друг - это второе я.",
        "Сохранение дружбы - ключ к счастью.",
        "Ежедневное общение укрепляет дружбу.",
        "Настоящая дружба проверяется временем.",
        "Друг в сердце - зеркало души.",
        "Хороший друг - самое ценное сокровище.",
        "Дружба - самый прекрасный дар жизни.",
        "Верный друг - золотая находка.",
        "Время с друзьями - лучшее время!",
    ],
    'en': [
        "Friendship is a flower that needs watering every day.",
        "A close friend is your second self.",
        "Maintaining friendship is the key to happiness.",
        "Daily communication strengthens friendship.",
        "True friendship is tested by time.",
        "A friend in your heart is a mirror of your soul.",
        "A good friend is the most valuable treasure.",
        "Friendship is life's most beautiful gift.",
        "A loyal friend is a golden find.",
        "Time with friends is the best time!",
    ]
}



def get_streak_message(streak_days: int, lang: str, include_cta: bool = True) -> str:
    """Get appropriate message based on streak days with call-to-action"""
    quotes = STREAK_QUOTES.get(lang, STREAK_QUOTES['en'])
    quote = random.choice(quotes)
    
    # Call-to-action messages
    cta_messages = {
        'uz': "\n\n🏆 /leaderboard orqali eng yaxshi do'stliklarni ko'ring!\n💪 Raqobatlashing va TOP-20 ga kirish uchun do'stingiz bilan har kuni muloqot qiling!",
        'ru': "\n\n🏆 Смотрите лучшие дружбы через /leaderboard!\n💪 Соревнуйтесь и общайтесь каждый день, чтобы попасть в ТОП-20!",
        'en': "\n\n🏆 Check the best friendships via /leaderboard!\n💪 Compete and communicate daily to reach TOP-20!"
    }
    
    messages = {
        'uz': {
            1: f"✅ <b>Muloqot boshlandi!</b>\n\n🔥 1-kun\n\n💭 <i>{quote}</i>",
            2: f"🎉 <b>Muloqot davom etmoqda!</b>\n\n🔥 2-kun\n\n💭 <i>{quote}</i>",
            3: f"🔥 <b>Ajoyib!</b>\n\n🔥 3-kun\n\n💭 <i>{quote}</i>",
            7: f"⭐ <b>Bir hafta!</b>\n\n🔥 7-kun ketma-ket\n\n💭 <i>{quote}</i>\n\n🎯 <i>Siz allaqachon ko'pchilikdan oldinda!</i>",
            14: f"🌟 <b>Ikki hafta!</b>\n\n🔥 14-kun ketma-ket\n\n💭 <i>{quote}</i>\n\n🎯 <i>Ajoyib natija! Davom eting!</i>",
            30: f"🏆 <b>Bir oy!</b>\n\n🔥 30-kun ketma-ket\n\n💭 <i>{quote}</i>\n\n🎯 <i>Siz TOP-20 ga yaqinsiz!</i>",
            50: f"💎 <b>50 kun!</b>\n\n🔥 Afsona darajasida!\n\n💭 <i>{quote}</i>\n\n🎯 <i>Liderlar jadvalida o'rningizni tekshiring!</i>",
            100: f"👑 <b>100 kun!</b>\n\n🔥 Siz haqiqiy chempionsiz!\n\n💭 <i>{quote}</i>\n\n🎯 <i>Bu muloqot tarixga kirdi!</i>",
        },
        'ru': {
            1: f"✅ <b>Общение началось!</b>\n\n🔥 День 1\n\n💭 <i>{quote}</i>",
            2: f"🎉 <b>Общение продолжается!</b>\n\n🔥 День 2\n\n💭 <i>{quote}</i>",
            3: f"🔥 <b>Отлично!</b>\n\n🔥 День 3\n\n💭 <i>{quote}</i>",
            7: f"⭐ <b>Неделя!</b>\n\n🔥 7 дней подряд\n\n💭 <i>{quote}</i>\n\n🎯 <i>Вы уже впереди многих!</i>",
            14: f"🌟 <b>Две недели!</b>\n\n🔥 14 дней подряд\n\n💭 <i>{quote}</i>\n\n🎯 <i>Отличный результат! Продолжайте!</i>",
            30: f"🏆 <b>Месяц!</b>\n\n🔥 30 дней подряд\n\n💭 <i>{quote}</i>\n\n🎯 <i>Вы близки к ТОП-20!</i>",
            50: f"💎 <b>50 дней!</b>\n\n🔥 Легендарный уровень!\n\n💭 <i>{quote}</i>\n\n🎯 <i>Проверьте свою позицию в таблице лидеров!</i>",
            100: f"👑 <b>100 дней!</b>\n\n🔥 Вы настоящие чемпионы!\n\n💭 <i>{quote}</i>\n\n🎯 <i>Это общение вошло в историю!</i>",
        },
        'en': {
            1: f"✅ <b>Communication started!</b>\n\n🔥 Day 1\n\n💭 <i>{quote}</i>",
            2: f"🎉 <b>Communication continues!</b>\n\n🔥 Day 2\n\n💭 <i>{quote}</i>",
            3: f"🔥 <b>Awesome!</b>\n\n🔥 Day 3\n\n💭 <i>{quote}</i>",
            7: f"⭐ <b>One week!</b>\n\n🔥 7 days in a row\n\n💭 <i>{quote}</i>\n\n🎯 <i>You're already ahead of many!</i>",
            14: f"🌟 <b>Two weeks!</b>\n\n🔥 14 days in a row\n\n💭 <i>{quote}</i>\n\n🎯 <i>Great result! Keep going!</i>",
            30: f"🏆 <b>One month!</b>\n\n🔥 30 days in a row\n\n💭 <i>{quote}</i>\n\n🎯 <i>You're close to TOP-20!</i>",
            50: f"💎 <b>50 days!</b>\n\n🔥 Legendary level!\n\n💭 <i>{quote}</i>\n\n🎯 <i>Check your position on the leaderboard!</i>",
            100: f"👑 <b>100 days!</b>\n\n🔥 You're true champions!\n\n💭 <i>{quote}</i>\n\n🎯 <i>This communication has made history!</i>",
        }
    }
    
    lang_messages = messages.get(lang, messages['en'])
    
    # Get milestone message or default
    if streak_days in lang_messages:
        message = lang_messages[streak_days]
    elif streak_days < 7:
        message = lang_messages.get(3, "").replace("3", str(streak_days))
    else:
        # For days > 3 but not milestone, use generic format
        if lang == 'uz':
            message = f"🔥 <b>{streak_days}-kun ketma-ket!</b>\n\n💭 <i>{quote}</i>"
        elif lang == 'ru':
            message = f"🔥 <b>День {streak_days} подряд!</b>\n\n💭 <i>{quote}</i>"
        else:
            message = f"🔥 <b>Day {streak_days} in a row!</b>\n\n💭 <i>{quote}</i>"
    
    # Add CTA for first 3 days and milestones
    if include_cta and (streak_days <= 3 or streak_days in [7, 14, 30, 50, 100]):
        message += cta_messages.get(lang, cta_messages['en'])
    
    return message


def log_interaction(streak_id: int, user_id: int, friend_id: int, interaction_type: str, data: dict = None):
    """Log streak interaction to database"""
    try:
        interaction_data = {
            'streak_id': streak_id,
            'user_id': str(user_id),
            'friend_id': str(friend_id),
            'interaction_type': interaction_type,
            'interaction_data': data or {},
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        supabase.table('streak_interactions').insert(interaction_data).execute()
        logger.info(f"INTERACTION_LOGGED: {interaction_type} | User {user_id} -> Friend {friend_id}")
    except Exception as e:
        logger.error(f"Error logging interaction: {e}")


async def handle_ping_friend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle ping friend action - create shareable streak link"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Get language from database
    try:
        result = supabase.table('friends_users').select('language').eq('telegram_id', str(user_id)).execute()
        if result.data:
            lang = result.data[0]['language']
        else:
            lang = 'en'
    except Exception:
        lang = 'en'
    
    context.user_data['language'] = lang
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        # Create generic streak link
        bot_username = context.bot.username
        streak_link = f"https://t.me/{bot_username}?start=streak_{user_id}"
        
        # Get sender name
        sender_name = f"{update.effective_user.first_name} {update.effective_user.last_name or ''}".strip()
        
        # Create share messages
        share_messages = {
            'uz': f"👋 Salom! {sender_name} siz bilan har kunlik muloqotni boshlashni xohlaydi!\n\n🔥 Boshlash uchun havolani bosing:\n{streak_link}",
            'ru': f"👋 Привет! {sender_name} хочет начать ежедневное общение с вами!\n\n🔥 Нажмите ссылку, чтобы начать:\n{streak_link}",
            'en': f"👋 Hey! {sender_name} wants to start daily communication with you!\n\n🔥 Click the link to start:\n{streak_link}"
        }
        
        share_text_encoded = urllib.parse.quote(share_messages.get(lang, share_messages['en']))
        
        # Show confirmation
        text = get_streak_text(lang, 'streak_link_created').format(link=streak_link)
        
        keyboard = [
            [InlineKeyboardButton(
                get_streak_text(lang, 'share_test'),
                url=f"https://t.me/share/url?url={streak_link}&text={share_text_encoded}"
            )],
            [InlineKeyboardButton(
                get_streak_text(lang, 'back'),
                callback_data='streaks_menu'
            )]
        ]
        
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
        
        logger.info(f"STREAK_LINK_CREATED: User {user_id} created streak link")
        
    except Exception as e:
        logger.error(f"Error creating streak link: {e}")
        await query.edit_message_text("❌ Error creating streak link")


async def handle_daily_question_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start daily question flow"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    lang = context.user_data.get('language', 'en')
    
    # Extract friend_id
    friend_id = int(query.data.split('_')[-1])
    
    # Get random question
    question = random.choice(DAILY_QUESTIONS.get(lang, DAILY_QUESTIONS['en']))
    
    # Store in context
    context.user_data['daily_q_friend_id'] = friend_id
    context.user_data['daily_q_question'] = question
    
    # Show question with options
    text = get_streak_text(lang, 'daily_q_title').format(question=question)
    
    keyboard = [
        [InlineKeyboardButton(get_streak_text(lang, 'answer'), callback_data=f'daily_q_answer_{friend_id}')],
        [InlineKeyboardButton(get_streak_text(lang, 'skip'), callback_data='streaks_menu')],
    ]
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)


async def handle_daily_question_answer_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Prompt user to write answer"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('language', 'en')
    
    text = get_streak_text(lang, 'answer_prompt')
    
    keyboard = [[InlineKeyboardButton(get_streak_text(lang, 'back'), callback_data='streaks_menu')]]
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    
    return ANSWERING_DAILY_Q


async def handle_daily_question_answer_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process answer text"""
    user_id = update.effective_user.id
    lang = context.user_data.get('language', 'en')
    answer = update.message.text
    
    friend_id = context.user_data.get('daily_q_friend_id')
    question = context.user_data.get('daily_q_question')
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        # Get or create streak
        streak = get_or_create_streak(user_id, friend_id)
        if not streak:
            await update.message.reply_text("❌ Error")
            return ConversationHandler.END
        
        # Update streak
        streak_days = update_streak(streak['id'], user_id, friend_id)
        
        # Log interaction
        log_interaction(streak['id'], user_id, friend_id, 'daily_question', {
            'question': question,
            'answer': answer
        })
        
        # Send confirmation
        text = get_streak_text(lang, 'answer_saved').format(days=streak_days)
        
        keyboard = [
            [InlineKeyboardButton(
                get_streak_text(lang, 'send_to_friend'),
                callback_data=f'daily_q_send_{friend_id}'
            )],
            [InlineKeyboardButton(get_streak_text(lang, 'back'), callback_data='streaks_menu')]
        ]
        
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
        
        # Store answer for potential sending
        context.user_data['daily_q_answer'] = answer
        
        logger.info(f"DAILY_Q_ANSWERED: User {user_id} | Friend {friend_id} | Streak: {streak_days}")
        
    except Exception as e:
        logger.error(f"Error processing daily question answer: {e}")
        await update.message.reply_text("❌ Error")
    
    return ConversationHandler.END


async def handle_daily_question_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send answer to friend"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    lang = context.user_data.get('language', 'en')
    
    friend_id = int(query.data.split('_')[-1])
    question = context.user_data.get('daily_q_question')
    answer = context.user_data.get('daily_q_answer')
    
    try:
        # Get friend info
        friend_info = supabase.table('friends_users')\
            .select('first_name, language')\
            .eq('telegram_id', str(friend_id))\
            .execute()
        
        if friend_info.data:
            friend_name = friend_info.data[0].get('first_name', 'Friend')
            friend_lang = friend_info.data[0].get('language', 'en')
            
            # Send to friend
            sender_name = f"{update.effective_user.first_name} {update.effective_user.last_name or ''}".strip()
            friend_text = get_streak_text(friend_lang, 'friend_answered').format(
                sender_name=sender_name,
                answer=answer
            )
            
            await context.bot.send_message(
                chat_id=friend_id,
                text=friend_text,
                parse_mode=ParseMode.HTML
            )
            
            # Confirm to user
            text = get_streak_text(lang, 'answer_sent_to_friend').format(friend_name=friend_name)
            
            keyboard = [[InlineKeyboardButton(get_streak_text(lang, 'back'), callback_data='streaks_menu')]]
            
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
            
            logger.info(f"DAILY_Q_SENT: User {user_id} sent answer to {friend_id}")
        
    except Exception as e:
        logger.error(f"Error sending daily question: {e}")
        await query.edit_message_text("❌ Error")


async def handle_remember_friend_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start remember friend flow"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    lang = context.user_data.get('language', 'en')
    
    friend_id = int(query.data.split('_')[-1])
    
    # Get random question
    question = random.choice(FRIEND_INFO_QUESTIONS.get(lang, FRIEND_INFO_QUESTIONS['en']))
    
    # Store in context
    context.user_data['remember_friend_id'] = friend_id
    context.user_data['remember_question'] = question
    
    # Show question
    text = get_streak_text(lang, 'remember_title').format(question=question)
    
    keyboard = [[InlineKeyboardButton(get_streak_text(lang, 'back'), callback_data='streaks_menu')]]
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    
    return REMEMBERING_FRIEND


async def handle_remember_friend_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process remembered info"""
    user_id = update.effective_user.id
    lang = context.user_data.get('language', 'en')
    answer = update.message.text
    
    friend_id = context.user_data.get('remember_friend_id')
    question = context.user_data.get('remember_question')
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        # Save to friend_info table
        info_data = {
            'user_id': str(user_id),
            'friend_id': str(friend_id),
            'question': question,
            'answer': answer,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        supabase.table('friend_info').insert(info_data).execute()
        
        # Update streak
        streak = get_or_create_streak(user_id, friend_id)
        if streak:
            streak_days = update_streak(streak['id'], user_id, friend_id)
            log_interaction(streak['id'], user_id, friend_id, 'remember', {
                'question': question,
                'answer': answer
            })
        
        # Get friend name
        friend_info = supabase.table('friends_users')\
            .select('first_name')\
            .eq('telegram_id', str(friend_id))\
            .execute()
        
        friend_name = friend_info.data[0].get('first_name', 'Friend') if friend_info.data else 'Friend'
        
        # Confirm
        text = get_streak_text(lang, 'info_saved').format(
            friend_name=friend_name,
            info=answer
        )
        
        keyboard = [[InlineKeyboardButton(get_streak_text(lang, 'back'), callback_data='streaks_menu')]]
        
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
        
        logger.info(f"REMEMBER_SAVED: User {user_id} saved info about {friend_id}")
        
    except Exception as e:
        logger.error(f"Error saving friend info: {e}")
        await update.message.reply_text("❌ Error")
    
    return ConversationHandler.END


async def handle_guess_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start guess game"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    lang = context.user_data.get('language', 'en')
    
    friend_id = int(query.data.split('_')[-1])
    
    # Get random question
    question = random.choice(GUESS_QUESTIONS.get(lang, GUESS_QUESTIONS['en']))
    
    # Get friend name
    friend_info = supabase.table('friends_users')\
        .select('first_name')\
        .eq('telegram_id', str(friend_id))\
        .execute()
    
    friend_name = friend_info.data[0].get('first_name', 'Friend') if friend_info.data else 'Friend'
    user_name = update.effective_user.first_name
    
    # Show question
    text = get_streak_text(lang, 'guess_title').format(question=question)
    
    # Random order for buttons
    options = [
        (user_name, 'user'),
        (friend_name, 'friend')
    ]
    random.shuffle(options)
    
    keyboard = [
        [InlineKeyboardButton(options[0][0], callback_data=f'guess_answer_{friend_id}_{options[0][1]}')],
        [InlineKeyboardButton(options[1][0], callback_data=f'guess_answer_{friend_id}_{options[1][1]}')],
        [InlineKeyboardButton(get_streak_text(lang, 'back'), callback_data='streaks_menu')]
    ]
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)


async def handle_guess_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle guess answer"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    lang = context.user_data.get('language', 'en')
    
    # Parse callback data
    parts = query.data.split('_')
    friend_id = int(parts[2])
    answer = parts[3]  # 'user' or 'friend'
    
    # Random correct answer
    correct = random.choice(['user', 'friend'])
    is_correct = (answer == correct)
    
    try:
        # Update streak regardless
        streak = get_or_create_streak(user_id, friend_id)
        if streak:
            streak_days = update_streak(streak['id'], user_id, friend_id)
            log_interaction(streak['id'], user_id, friend_id, 'guess', {
                'correct': is_correct
            })
        else:
            streak_days = 0
        
        # Show result
        if is_correct:
            text = get_streak_text(lang, 'guess_correct').format(days=streak_days)
        else:
            text = get_streak_text(lang, 'guess_wrong').format(days=streak_days)
        
        keyboard = [[InlineKeyboardButton(get_streak_text(lang, 'back'), callback_data='streaks_menu')]]
        
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
        
        logger.info(f"GUESS_GAME: User {user_id} | Friend {friend_id} | Correct: {is_correct} | Streak: {streak_days}")
        
    except Exception as e:
        logger.error(f"Error handling guess: {e}")
        await query.edit_message_text("❌ Error")


async def handle_weekly_checkin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show weekly check-in"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    lang = context.user_data.get('language', 'en')
    
    friend_id = int(query.data.split('_')[-1])
    
    # Get friend name
    friend_info = supabase.table('friends_users')\
        .select('first_name')\
        .eq('telegram_id', str(friend_id))\
        .execute()
    
    friend_name = friend_info.data[0].get('first_name', 'Friend') if friend_info.data else 'Friend'
    
    # Show question
    text = get_streak_text(lang, 'weekly_title').format(friend_name=friend_name)
    
    keyboard = [
        [InlineKeyboardButton(get_streak_text(lang, 'yes'), callback_data=f'weekly_yes_{friend_id}')],
        [InlineKeyboardButton(get_streak_text(lang, 'not_yet'), callback_data=f'weekly_no_{friend_id}')],
        [InlineKeyboardButton(get_streak_text(lang, 'back'), callback_data='streaks_menu')]
    ]
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)


async def handle_weekly_yes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle weekly check-in yes"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    lang = context.user_data.get('language', 'en')
    
    friend_id = int(query.data.split('_')[-1])
    
    try:
        # Update streak
        streak = get_or_create_streak(user_id, friend_id)
        if streak:
            streak_days = update_streak(streak['id'], user_id, friend_id)
            log_interaction(streak['id'], user_id, friend_id, 'weekly_checkin', {'talked': True})
        else:
            streak_days = 0
        
        text = get_streak_text(lang, 'weekly_yes').format(days=streak_days)
        
        keyboard = [[InlineKeyboardButton(get_streak_text(lang, 'back'), callback_data='streaks_menu')]]
        
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
        
        logger.info(f"WEEKLY_CHECKIN: User {user_id} | Friend {friend_id} | Talked: Yes | Streak: {streak_days}")
        
    except Exception as e:
        logger.error(f"Error handling weekly yes: {e}")
        await query.edit_message_text("❌ Error")


async def handle_weekly_no(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle weekly check-in no"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('language', 'en')
    
    text = get_streak_text(lang, 'weekly_not_yet')
    
    keyboard = [[InlineKeyboardButton(get_streak_text(lang, 'back'), callback_data='streaks_menu')]]
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)


async def handle_quiz_retake(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle quiz retake - redirect to taking test"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    friend_id = int(query.data.split('_')[-1])
    
    try:
        # Get friend's test
        test_result = supabase.table('tests').select('id').eq('user_id', str(friend_id)).execute()
        
        if test_result.data:
            test_id = test_result.data[0]['id']
            
            # Redirect to test
            from main import show_taking_test_question
            
            context.user_data['taking_test_id'] = test_id
            context.user_data['taking_test_answers'] = {}
            context.user_data['taking_test_question'] = 0
            context.user_data['is_retake'] = True
            
            await show_taking_test_question(update, context, context.user_data.get('language', 'en'))
        else:
            await query.edit_message_text("❌ Test not found")
            
    except Exception as e:
        logger.error(f"Error starting quiz retake: {e}")
        await query.edit_message_text("❌ Error")