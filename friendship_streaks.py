import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Tuple
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from config import supabase
import random
import urllib.parse


logger = logging.getLogger(__name__)

# Daily questions pool
DAILY_QUESTIONS = {
    'uz': [
        "Eng yaxshi xotirangiz nima?",
        "Birgalikda qayerga sayohat qilishni xohlaysiz?",
        "Do'stingiz haqida eng yaxshi narsa nima?",
        "Birgalikda qilgan eng qiziqarli ishingiz?",
        "Do'stingizning eng kuchli tomoni nima?",
        "Birgalikda qanday hobbing bor?",
        "Do'stingiz sizga qachon yordam bergan?",
        "Eng kulgili lahzangiz qanday edi?",
    ],
    'ru': [
        "Какое ваше любимое воспоминание?",
        "Куда бы вы хотели поехать вместе?",
        "Что лучшее в вашем друге?",
        "Самое веселое, что вы делали вместе?",
        "Какая самая сильная сторона вашего друга?",
        "Какое у вас общее хобби?",
        "Когда ваш друг помог вам?",
        "Какой был самый смешной момент?",
    ],
    'en': [
        "What is your favorite memory together?",
        "Where would you like to travel together?",
        "What's the best thing about your friend?",
        "What's the funniest thing you did together?",
        "What is your friend's strongest quality?",
        "What hobby do you share?",
        "When did your friend help you?",
        "What was your funniest moment?",
    ]
}

# Friend info questions
FRIEND_INFO_QUESTIONS = {
    'uz': [
        "Do'stingizning sevimli ovqati nima?",
        "Do'stingiz qaysi rangni yaxshi ko'radi?",
        "Do'stingizning sevimli filmi nima?",
        "Do'stingiz bo'sh vaqtida nima qiladi?",
        "Do'stingizning orzusi nima?",
    ],
    'ru': [
        "Какая любимая еда вашего друга?",
        "Какой цвет любит ваш друг?",
        "Какой любимый фильм вашего друга?",
        "Чем занимается друг в свободное время?",
        "О чем мечтает ваш друг?",
    ],
    'en': [
        "What is your friend's favorite food?",
        "What color does your friend like?",
        "What is your friend's favorite movie?",
        "What does your friend do in free time?",
        "What is your friend's dream?",
    ]
}

# Guess questions
GUESS_QUESTIONS = {
    'uz': [
        "Kim ko'proq qahva ichadi?",
        "Kim erta turadi?",
        "Kim ko'proq o'qiydi?",
        "Kim ko'proq sport bilan shug'ullanadi?",
        "Kim ko'proq sayohat qiladi?",
    ],
    'ru': [
        "Кто пьет больше кофе?",
        "Кто встает раньше?",
        "Кто больше читает?",
        "Кто больше занимается спортом?",
        "Кто больше путешествует?",
    ],
    'en': [
        "Who drinks more coffee?",
        "Who wakes up earlier?",
        "Who reads more?",
        "Who exercises more?",
        "Who travels more?",
    ]
}

STREAK_TRANSLATIONS = {
    'uz': {
        'streak_title': '🔥 <b>Do\'stlik Streak</b>',
        'your_streaks': '📊 <b>Sizning streaklar</b>\n\nDo\'stlaringiz bilan streak:',
        'no_streaks': '😔 <b>Hali streaklar yo\'q</b>\n\nDo\'stlaringiz bilan muloqot qilishni boshlang!',
        'streak_with': '🔥 <b>{name}</b> bilan: {days} kun',
        'ping_friend': '👋 Salom yuboring',
        'daily_question': '❓ Kunlik savol',
        'remember_friend': '💭 Do\'st haqida eslang',
        'guess_game': '🎮 O\'yinni toping',
        'quiz_retake': '🔁 Testni qayta toping',
        'weekly_checkin': '📅 Haftalik tekshiruv',
        'leaderboard': '🏆 Liderlar jadvali',
        'back': '◀️ Orqaga',
        'ping_sent': '✅ <b>Salom yuborildi!</b>\n\n👋 {friend_name}ga salom yubordingiz!\n\n🔥 Streak: {days} kun',
        'ping_received': '👋 <b>Salom!</b>\n\n{sender_name} sizga salom yubordi!\n\n🔥 Streak: {days} kun',
        'daily_q_title': '💭 <b>Kunlik savol</b>\n\n{question}',
        'answer': '✍️ Javob berish',
        'skip': '⏭️ O\'tkazib yuborish',
        'send_to_friend': '📤 Do\'stga yuborish',
        'answer_prompt': '✍️ Javobingizni yozing:',
        'answer_saved': '✅ <b>Javob saqlandi!</b>\n\n🔥 Streak yangilandi: {days} kun',
        'answer_sent_to_friend': '📤 <b>Javob do\'stga yuborildi!</b>\n\n{friend_name} sizning javobingizni ko\'radi.',
        'friend_answered': '💭 <b>Yangi javob!</b>\n\n{sender_name} savolga javob berdi:\n\n<i>"{answer}"</i>',
        'remember_title': '💭 <b>Do\'st haqida eslang</b>\n\n{question}',
        'info_saved': '✅ <b>Ma\'lumot saqlandi!</b>\n\n📝 {friend_name} haqida: {info}',
        'guess_title': '🎮 <b>Topish o\'yini</b>\n\n{question}',
        'guess_correct': '🎉 <b>To\'g\'ri!</b>\n\nSiz to\'g\'ri topdingiz!\n\n🔥 Streak: {days} kun',
        'guess_wrong': '❌ <b>Noto\'g\'ri</b>\n\nLekin streak saqlanadi!\n\n🔥 Streak: {days} kun',
        'weekly_title': '📅 <b>Haftalik tekshiruv</b>\n\nBu hafta {friend_name} bilan gaplashdingizmi?',
        'yes': '✅ Ha',
        'not_yet': '⏰ Hali yo\'q',
        'weekly_yes': '🎉 <b>Ajoyib!</b>\n\nDo\'stlik aloqalarini davom eting!\n\n🔥 Streak: {days} kun',
        'weekly_not_yet': '⏰ <b>Unutmang!</b>\n\nDo\'stingizga qo\'ng\'iroq qiling yoki xabar yuboring!',
        'streak_broken': '💔 <b>Streak uzildi!</b>\n\n{friend_name} bilan streakingiz tugadi.\n\n<i>Yana boshdan boshlang!</i>',
        'streak_restore_offer': '🛡️ <b>Streak himoyasi</b>\n\n{friend_name} bilan streakingiz uzilish xavfida!\n\nStreakni tiklash: Premium funksiya\n\n💎 Streak himoyasidan foydalaning?',
        'restore': '🛡️ Tiklash',
        'let_break': '💔 Uzilsin',
        'streak_restored': '✅ <b>Streak tiklandi!</b>\n\n🔥 {friend_name} bilan streakingiz davom etmoqda: {days} kun',
        'no_restores': '❌ <b>Tiklanishlar yo\'q</b>\n\nSizda hech qanday streak himoyasi qolmagan.\n\nPremiumga o\'ting va ko\'proq himoya oling!',
        'select_friend': '👥 <b>Do\'stni tanlang</b>\n\nStreakni kim bilan boshlashni xohlaysiz?',
        'no_test_results': '😔 Hali do\'stlar yo\'q\n\nTestlarni yarating va ulashing!',
        'share_test': '📤 Testni ulashish',
        'create_test': '📝 Test yaratish',
        'ping_sent': '✅ <b>Salom yuborildi!</b>\n\n👋 {friend_name}ga salom yubordingiz!\n\n🔥 Streak: {days} kun\n\n💡 <i>Har kunlik muloqot streakni davom ettiradi!</i>',
        'ping_received': '👋 <b>Salom!</b>\n\n{sender_name} sizga salom yubordi!\n\n🔥 Streak: {days} kun',














    },
    'ru': {
        'streak_title': '🔥 <b>Полоса дружбы</b>',
        'your_streaks': '📊 <b>Ваши полосы</b>\n\nПолосы с друзьями:',
        'no_streaks': '😔 <b>Пока нет полос</b>\n\nНачните взаимодействовать с друзьями!',
        'streak_with': '🔥 <b>{name}</b>: {days} дней',
        'ping_friend': '👋 Поздороваться',
        'daily_question': '❓ Ежедневный вопрос',
        'remember_friend': '💭 Вспомнить о друге',
        'guess_game': '🎮 Игра-угадайка',
        'quiz_retake': '🔁 Пройти тест снова',
        'weekly_checkin': '📅 Недельная проверка',
        'leaderboard': '🏆 Таблица лидеров',
        'back': '◀️ Назад',
        'ping_sent': '✅ <b>Привет отправлен!</b>\n\n👋 Вы поздоровались с {friend_name}!\n\n🔥 Полоса: {days} дней',
        'ping_received': '👋 <b>Привет!</b>\n\n{sender_name} поздоровался с вами!\n\n🔥 Полоса: {days} дней',
        'daily_q_title': '💭 <b>Ежедневный вопрос</b>\n\n{question}',
        'answer': '✍️ Ответить',
        'skip': '⏭️ Пропустить',
        'send_to_friend': '📤 Отправить другу',
        'answer_prompt': '✍️ Напишите ваш ответ:',
        'answer_saved': '✅ <b>Ответ сохранен!</b>\n\n🔥 Полоса обновлена: {days} дней',
        'answer_sent_to_friend': '📤 <b>Ответ отправлен другу!</b>\n\n{friend_name} увидит ваш ответ.',
        'friend_answered': '💭 <b>Новый ответ!</b>\n\n{sender_name} ответил на вопрос:\n\n<i>"{answer}"</i>',
        'remember_title': '💭 <b>Вспомните о друге</b>\n\n{question}',
        'info_saved': '✅ <b>Информация сохранена!</b>\n\n📝 О {friend_name}: {info}',
        'guess_title': '🎮 <b>Игра-угадайка</b>\n\n{question}',
        'guess_correct': '🎉 <b>Правильно!</b>\n\nВы угадали!\n\n🔥 Полоса: {days} дней',
        'guess_wrong': '❌ <b>Неправильно</b>\n\nНо полоса сохранена!\n\n🔥 Полоса: {days} дней',
        'weekly_title': '📅 <b>Недельная проверка</b>\n\nВы общались с {friend_name} на этой неделе?',
        'yes': '✅ Да',
        'not_yet': '⏰ Еще нет',
        'weekly_yes': '🎉 <b>Отлично!</b>\n\nПродолжайте поддерживать связь!\n\n🔥 Полоса: {days} дней',
        'weekly_not_yet': '⏰ <b>Не забудьте!</b>\n\nПозвоните или напишите другу!',
        'streak_broken': '💔 <b>Полоса прервана!</b>\n\nВаша полоса с {friend_name} закончилась.\n\n<i>Начните заново!</i>',
        'streak_restore_offer': '🛡️ <b>Защита полосы</b>\n\nВаша полоса с {friend_name} под угрозой!\n\nВосстановление полосы: Premium функция\n\n💎 Использовать защиту полосы?',
        'restore': '🛡️ Восстановить',
        'let_break': '💔 Пусть прервется',
        'streak_restored': '✅ <b>Полоса восстановлена!</b>\n\n🔥 Ваша полоса с {friend_name} продолжается: {days} дней',
        'no_restores': '❌ <b>Нет восстановлений</b>\n\nУ вас не осталось защит полосы.\n\nПерейдите на Premium и получите больше защит!',
        'select_friend': '👥 <b>Выберите друга</b>\n\nС кем хотите начать полосу?',
        'no_test_results': '😔 Пока нет друзей\n\nСоздайте и поделитесь тестами!',
        'share_test': '📤 Поделиться тестом',
        'create_test': '📝 Создать тест',
        'ping_sent': '✅ <b>Привет отправлен!</b>\n\n👋 Вы поздоровались с {friend_name}!\n\n🔥 Полоса: {days} дней\n\n💡 <i>Ежедневное общение поддерживает полосу!</i>',
        'ping_received': '👋 <b>Привет!</b>\n\n{sender_name} поздоровался с вами!\n\n🔥 Полоса: {days} дней',


















    },
    'en': {
        'streak_title': '🔥 <b>Friendship Streak</b>',
        'your_streaks': '📊 <b>Your Streaks</b>\n\nStreaks with friends:',
        'no_streaks': '😔 <b>No streaks yet</b>\n\nStart interacting with friends!',
        'streak_with': '🔥 <b>{name}</b>: {days} days',
        'ping_friend': '👋 Ping Friend',
        'daily_question': '❓ Daily Question',
        'remember_friend': '💭 Remember Friend',
        'guess_game': '🎮 Guess Game',
        'quiz_retake': '🔁 Retake Quiz',
        'weekly_checkin': '📅 Weekly Check-in',
        'leaderboard': '🏆 Leaderboard',
        'back': '◀️ Back',
        'ping_sent': '✅ <b>Ping sent!</b>\n\n👋 You pinged {friend_name}!\n\n🔥 Streak: {days} days',
        'ping_received': '👋 <b>Ping!</b>\n\n{sender_name} says hi!\n\n🔥 Streak: {days} days',
        'daily_q_title': '💭 <b>Daily Question</b>\n\n{question}',
        'answer': '✍️ Answer',
        'skip': '⏭️ Skip',
        'send_to_friend': '📤 Send to Friend',
        'answer_prompt': '✍️ Write your answer:',
        'answer_saved': '✅ <b>Answer saved!</b>\n\n🔥 Streak updated: {days} days',
        'answer_sent_to_friend': '📤 <b>Answer sent to friend!</b>\n\n{friend_name} will see your answer.',
        'friend_answered': '💭 <b>New answer!</b>\n\n{sender_name} answered:\n\n<i>"{answer}"</i>',
        'remember_title': '💭 <b>Remember about friend</b>\n\n{question}',
        'info_saved': '✅ <b>Info saved!</b>\n\n📝 About {friend_name}: {info}',
        'guess_title': '🎮 <b>Guess Game</b>\n\n{question}',
        'guess_correct': '🎉 <b>Correct!</b>\n\nYou guessed right!\n\n🔥 Streak: {days} days',
        'guess_wrong': '❌ <b>Wrong</b>\n\nBut streak saved!\n\n🔥 Streak: {days} days',
        'weekly_title': '📅 <b>Weekly Check-in</b>\n\nDid you talk to {friend_name} this week?',
        'yes': '✅ Yes',
        'not_yet': '⏰ Not yet',
        'weekly_yes': '🎉 <b>Awesome!</b>\n\nKeep staying connected!\n\n🔥 Streak: {days} days',
        'weekly_not_yet': '⏰ <b>Don\'t forget!</b>\n\nCall or message your friend!',
        'streak_broken': '💔 <b>Streak broken!</b>\n\nYour streak with {friend_name} has ended.\n\n<i>Start again!</i>',
        'streak_restore_offer': '🛡️ <b>Streak Protection</b>\n\nYour streak with {friend_name} is at risk!\n\nStreak restore: Premium feature\n\n💎 Use streak protection?',
        'restore': '🛡️ Restore',
        'let_break': '💔 Let it break',
        'streak_restored': '✅ <b>Streak restored!</b>\n\n🔥 Your streak with {friend_name} continues: {days} days',
        'no_restores': '❌ <b>No restores left</b>\n\nYou have no streak protections remaining.\n\nUpgrade to Premium for more protections!',
        'select_friend': '👥 <b>Select Friend</b>\n\nWho do you want to start a streak with?',
        'no_test_results': '😔 No friends yet\n\nCreate and share tests!',
        'share_test': '📤 Share Test',
        'create_test': '📝 Create Test',
        'ping_sent': '✅ <b>Ping sent!</b>\n\n👋 You pinged {friend_name}!\n\n🔥 Streak: {days} days\n\n💡 <i>Daily interaction keeps the streak alive!</i>',
        'ping_received': '👋 <b>Ping!</b>\n\n{sender_name} says hi!\n\n🔥 Streak: {days} days',
    













    }
}

def get_streak_text(lang: str, key: str) -> str:
    """Get translated streak text"""
    return STREAK_TRANSLATIONS.get(lang, STREAK_TRANSLATIONS['en']).get(key, key)


def get_or_create_streak(user_id: int, friend_id: int) -> Dict:
    """Get existing streak or create new one"""
    try:
        # Try to find existing streak (bidirectional)
        result = supabase.table('friendship_streaks')\
            .select('*')\
            .or_(f'and(user_id.eq.{user_id},friend_id.eq.{friend_id}),and(user_id.eq.{friend_id},friend_id.eq.{user_id})')\
            .execute()
        
        if result.data:
            return result.data[0]
        
        # Create new streak
        streak_data = {
            'user_id': str(user_id),
            'friend_id': str(friend_id),
            'current_streak': 0,
            'longest_streak': 0,
            'last_interaction': None,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        new_streak = supabase.table('friendship_streaks').insert(streak_data).execute()
        logger.info(f"STREAK_CREATED: User {user_id} with friend {friend_id}")
        return new_streak.data[0]
        
    except Exception as e:
        logger.error(f"Error in get_or_create_streak: {e}")
        return None


def update_streak(streak_id: int, user_id: int, friend_id: int) -> int:
    """Update streak after interaction, returns current streak days"""
    try:
        streak = supabase.table('friendship_streaks').select('*').eq('id', streak_id).execute()
        
        if not streak.data:
            return 0
        
        streak_data = streak.data[0]
        last_interaction = streak_data.get('last_interaction')
        current_streak = streak_data.get('current_streak', 0)
        longest_streak = streak_data.get('longest_streak', 0)
        
        now = datetime.now(timezone.utc)
        
        # Check if interaction is today
        if last_interaction:
            last_date = datetime.fromisoformat(last_interaction.replace('Z', '+00:00'))
            days_diff = (now.date() - last_date.date()).days
            
            if days_diff == 0:
                # Same day - no change
                logger.info(f"STREAK_SAME_DAY: User {user_id} with friend {friend_id} | Streak: {current_streak}")
                return current_streak
            elif days_diff == 1:
                # Next day - increment
                current_streak += 1
                logger.info(f"STREAK_INCREMENT: User {user_id} with friend {friend_id} | Streak: {current_streak}")
            else:
                # Missed days - reset
                current_streak = 1
                logger.info(f"STREAK_RESET: User {user_id} with friend {friend_id} | Was {streak_data.get('current_streak')} days")
        else:
            # First interaction
            current_streak = 1
            logger.info(f"STREAK_FIRST: User {user_id} with friend {friend_id}")
        
        # Update longest streak if needed
        if current_streak > longest_streak:
            longest_streak = current_streak
        
        # Update database
        supabase.table('friendship_streaks').update({
            'current_streak': current_streak,
            'longest_streak': longest_streak,
            'last_interaction': now.isoformat()
        }).eq('id', streak_id).execute()
        
        return current_streak
        
    except Exception as e:
        logger.error(f"Error updating streak: {e}")
        return 0


async def get_user_friends(user_id: int) -> List[Dict]:
    """Get list of friends (people who took user's test)"""
    try:
        # Get user's test
        test_result = supabase.table('tests').select('id').eq('user_id', str(user_id)).execute()
        
        if not test_result.data:
            return []
        
        test_id = test_result.data[0]['id']
        
        # Get people who took the test
        results = supabase.table('test_results')\
            .select('user_id, score')\
            .eq('test_id', test_id)\
            .order('score', desc=True)\
            .execute()
        
        friends = []
        for result in results.data:
            friend_id = result['user_id']
            
            # Get friend info
            friend_info = supabase.table('friends_users')\
                .select('first_name, last_name, username')\
                .eq('telegram_id', friend_id)\
                .execute()
            
            if friend_info.data:
                friend = friend_info.data[0]
                friends.append({
                    'id': int(friend_id),
                    'name': f"{friend.get('first_name', '')} {friend.get('last_name', '')}".strip() or friend.get('username', 'Friend'),
                    'score': result['score']
                })
        
        return friends
        
    except Exception as e:
        logger.error(f"Error getting user friends: {e}")
        return []


async def show_streaks_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show main streaks menu"""
    query = update.callback_query
    if query:
        await query.answer()
    
    user_id = update.effective_user.id
    
    # FIX: Get language from database, not from context
    try:
        result = supabase.table('friends_users').select('language').eq('telegram_id', str(user_id)).execute()
        if result.data:
            lang = result.data[0]['language']
        else:
            lang = 'en'
    except Exception:
        lang = 'en'
    
    # Store in context for other handlers
    context.user_data['language'] = lang
    
    # Get user's streaks
    try:
        streaks = supabase.table('friendship_streaks')\
            .select('*')\
            .or_(f'user_id.eq.{user_id},friend_id.eq.{user_id}')\
            .order('current_streak', desc=True)\
            .execute()
        
        text = get_streak_text(lang, 'streak_title') + '\n\n'
        
        if streaks.data:
            text += get_streak_text(lang, 'your_streaks') + '\n\n'
            
            for streak in streaks.data:
                friend_id = streak['friend_id'] if str(streak['user_id']) == str(user_id) else streak['user_id']
                
                # Get friend name
                friend_info = supabase.table('friends_users')\
                    .select('first_name, last_name')\
                    .eq('telegram_id', friend_id)\
                    .execute()
                
                friend_name = 'Friend'
                if friend_info.data:
                    friend_name = f"{friend_info.data[0].get('first_name', '')} {friend_info.data[0].get('last_name', '')}".strip()
                
                text += get_streak_text(lang, 'streak_with').format(
                    name=friend_name,
                    days=streak['current_streak']
                ) + '\n'
        else:
            text += get_streak_text(lang, 'no_streaks')
        
        keyboard = [
            [
                InlineKeyboardButton(
                    get_streak_text(lang, 'ping_friend'),
                    callback_data='streak_ping'
                ),
                InlineKeyboardButton(
                    get_streak_text(lang, 'daily_question'),
                    callback_data='streak_daily_q'
                )
            ],
            [
                InlineKeyboardButton(
                    get_streak_text(lang, 'remember_friend'),
                    callback_data='streak_remember'
                ),
                InlineKeyboardButton(
                    get_streak_text(lang, 'guess_game'),
                    callback_data='streak_guess'
                )
            ],
            [
                InlineKeyboardButton(
                    get_streak_text(lang, 'quiz_retake'),
                    callback_data='streak_quiz'
                ),
                InlineKeyboardButton(
                    get_streak_text(lang, 'weekly_checkin'),
                    callback_data='streak_weekly'
                )
            ],
            [
                InlineKeyboardButton(
                    get_streak_text(lang, 'leaderboard'),
                    callback_data='streak_leaderboard'
                )
            ],
            [
                InlineKeyboardButton(
                    get_streak_text(lang, 'back'),
                    callback_data='back_to_menu'
                )
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if query:
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
            
    except Exception as e:
        logger.error(f"Error showing streaks menu: {e}")
        error_text = "❌ Error loading streaks"
        if query:
            await query.edit_message_text(error_text)
        else:
            await update.message.reply_text(error_text)

async def show_friend_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str):
    from main import get_text
    """Show friend selection for streak actions (NOT used for ping anymore)"""
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
    
    friends = await get_user_friends(user_id)
    
    if not friends:
        # No friends yet - show appropriate message based on action
        no_friends_messages = {
            'uz': "😔 <b>Hali do'stlar yo'q</b>\n\n💡 Do'stlar qo'shish uchun:\n1. Test yarating\n2. Do'stlaringizga ulashing\n3. Ular testni yechgandan keyin bu yerda ko'rinadi!",
            'ru': "😔 <b>Пока нет друзей</b>\n\n💡 Чтобы добавить друзей:\n1. Создайте тест\n2. Поделитесь с друзьями\n3. После того как они пройдут тест, они появятся здесь!",
            'en': "😔 <b>No friends yet</b>\n\n💡 To add friends:\n1. Create a test\n2. Share with friends\n3. After they take it, they'll appear here!"
        }
        
        text = no_friends_messages.get(lang, no_friends_messages['en'])
        
        keyboard = [
            [InlineKeyboardButton(get_text(lang, 'create_test'), callback_data='create_test')],
            [InlineKeyboardButton(get_streak_text(lang, 'back'), callback_data='streaks_menu')]
        ]
        
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
        return
    
    text = get_streak_text(lang, 'select_friend')
    keyboard = []
    
    for friend in friends[:10]:  # Limit to 10 friends
        keyboard.append([InlineKeyboardButton(
            f"{friend['name']} ({friend['score']}%)",
            callback_data=f'streak_friend_{action}_{friend["id"]}'
        )])
    
    keyboard.append([InlineKeyboardButton(get_streak_text(lang, 'back'), callback_data='streaks_menu')])
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)