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
    """Handle ping friend action - create shareable streak link without friend selection"""
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
        # Create generic streak link (without specific friend_id)
        bot_username = context.bot.username
        streak_link = f"https://t.me/{bot_username}?start=streak_{user_id}"
        
        # Get sender name
        sender_name = f"{update.effective_user.first_name} {update.effective_user.last_name or ''}".strip()
        
        # Create share messages
        share_messages = {
            'uz': f"👋 Salom! {sender_name} siz bilan do'stlik streakini boshlashni xohlaydi!\n\n🔥 Streak boshlash uchun quyidagi havolani bosing:\n{streak_link}",
            'ru': f"👋 Привет! {sender_name} хочет начать полосу дружбы с вами!\n\n🔥 Нажмите ссылку, чтобы начать полосу:\n{streak_link}",
            'en': f"👋 Hey! {sender_name} wants to start a friendship streak with you!\n\n🔥 Click the link to start the streak:\n{streak_link}"
        }
        
        share_text_encoded = urllib.parse.quote(share_messages.get(lang, share_messages['en']))
        
        # Show confirmation with share button
        confirmation_messages = {
            'uz': f"✅ <b>Streak havolasi tayyor!</b>\n\n💡 <i>Havolani do'stlaringizga ulashing. Ular uni bosganida streak avtomatik boshlanadi!</i>\n\n🔗 <b>Havola:</b>\n<code>{streak_link}</code>",
            'ru': f"✅ <b>Ссылка на полосу готова!</b>\n\n💡 <i>Поделитесь ссылкой с друзьями. Когда они нажмут её, полоса автоматически начнётся!</i>\n\n🔗 <b>Ссылка:</b>\n<code>{streak_link}</code>",
            'en': f"✅ <b>Streak link ready!</b>\n\n💡 <i>Share the link with your friends. When they click it, the streak will automatically start!</i>\n\n🔗 <b>Link:</b>\n<code>{streak_link}</code>"
        }
        
        text = confirmation_messages.get(lang, confirmation_messages['en'])
        
        keyboard = [
            [InlineKeyboardButton(
                get_streak_text(lang, 'share_test'),  # Reuse "Share" translation
                url=f"https://t.me/share/url?url={streak_link}&text={share_text_encoded}"
            )],
            [InlineKeyboardButton(
                get_streak_text(lang, 'back'),
                callback_data='streaks_menu'
            )]
        ]
        
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
        
        logger.info(f"STREAK_LINK_CREATED: User {user_id} created general streak link")
        
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