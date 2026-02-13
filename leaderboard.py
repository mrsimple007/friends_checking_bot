import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Tuple
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from config import supabase

logger = logging.getLogger(__name__)

LEADERBOARD_TRANSLATIONS = {
    'uz': {
        'title': '🏆 <b>Liderlar jadvali</b>',
        'weekly_scores': '📊 <b>Haftalik eng yaxshi natijalar</b>',
        'longest_streaks': '🔥 <b>Eng uzun streaklar</b>',
        'your_rank': '📍 <b>Sizning o\'rningiz:</b>',
        'no_data': '😔 Ma\'lumotlar yo\'q',
        'back': '◀️ Orqaga',
        'rank': '#{rank}',
        'days': 'kun',
        'score': 'ball',
    },
    'ru': {
        'title': '🏆 <b>Таблица лидеров</b>',
        'weekly_scores': '📊 <b>Лучшие результаты недели</b>',
        'longest_streaks': '🔥 <b>Самые длинные полосы</b>',
        'your_rank': '📍 <b>Ваше место:</b>',
        'no_data': '😔 Нет данных',
        'back': '◀️ Назад',
        'rank': '#{rank}',
        'days': 'дней',
        'score': 'балл',
    },
    'en': {
        'title': '🏆 <b>Leaderboard</b>',
        'weekly_scores': '📊 <b>Top Weekly Scores</b>',
        'longest_streaks': '🔥 <b>Longest Streaks</b>',
        'your_rank': '📍 <b>Your Rank:</b>',
        'no_data': '😔 No data available',
        'back': '◀️ Back',
        'rank': '#{rank}',
        'days': 'days',
        'score': 'score',
    }
}

def get_leaderboard_text(lang: str, key: str) -> str:
    """Get translated leaderboard text"""
    return LEADERBOARD_TRANSLATIONS.get(lang, LEADERBOARD_TRANSLATIONS['en']).get(key, key)


def get_weekly_top_scores() -> List[Dict]:
    """Get top test scores from this week"""
    try:
        # Calculate start of week (Monday)
        now = datetime.now(timezone.utc)
        start_of_week = now - timedelta(days=now.weekday())
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Get test results from this week
        results = supabase.table('test_results')\
            .select('user_id, score, created_at')\
            .gte('created_at', start_of_week.isoformat())\
            .order('score', desc=True)\
            .order('created_at', desc=False)\
            .limit(50)\
            .execute()
        
        # Group by user and get their best score
        user_scores = {}
        for result in results.data:
            user_id = result['user_id']
            score = result['score']
            
            if user_id not in user_scores or score > user_scores[user_id]:
                user_scores[user_id] = score
        
        # Get user info and format leaderboard
        leaderboard = []
        for user_id, score in sorted(user_scores.items(), key=lambda x: x[1], reverse=True)[:10]:
            try:
                user_info = supabase.table('friends_users')\
                    .select('first_name, last_name, username')\
                    .eq('telegram_id', user_id)\
                    .execute()
                
                if user_info.data:
                    user = user_info.data[0]
                    name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
                    if not name:
                        name = user.get('username', 'User')
                    
                    leaderboard.append({
                        'user_id': user_id,
                        'name': name,
                        'score': score
                    })
            except Exception as e:
                logger.error(f"Error getting user info for leaderboard: {e}")
                continue
        
        logger.info(f"LEADERBOARD_WEEKLY: Generated with {len(leaderboard)} entries")
        return leaderboard
        
    except Exception as e:
        logger.error(f"Error getting weekly top scores: {e}")
        return []


def get_longest_streaks() -> List[Dict]:
    """Get top 10 longest current streaks"""
    try:
        streaks = supabase.table('friendship_streaks')\
            .select('user_id, friend_id, current_streak')\
            .order('current_streak', desc=True)\
            .limit(20)\
            .execute()
        
        leaderboard = []
        seen_pairs = set()
        
        for streak in streaks.data:
            user_id = int(streak['user_id'])
            friend_id = int(streak['friend_id'])
            current_streak = streak['current_streak']
            
            # Skip if no streak
            if current_streak == 0:
                continue
            
            # Create a sorted tuple to avoid duplicates
            pair = tuple(sorted([user_id, friend_id]))
            
            if pair in seen_pairs:
                continue
            
            seen_pairs.add(pair)
            
            try:
                # Get both users' info
                user1_info = supabase.table('friends_users')\
                    .select('first_name, last_name, username')\
                    .eq('telegram_id', str(user_id))\
                    .execute()
                
                user2_info = supabase.table('friends_users')\
                    .select('first_name, last_name, username')\
                    .eq('telegram_id', str(friend_id))\
                    .execute()
                
                if user1_info.data and user2_info.data:
                    user1 = user1_info.data[0]
                    user2 = user2_info.data[0]
                    
                    name1 = f"{user1.get('first_name', '')} {user1.get('last_name', '')}".strip()
                    if not name1:
                        name1 = user1.get('username', 'User')
                    
                    name2 = f"{user2.get('first_name', '')} {user2.get('last_name', '')}".strip()
                    if not name2:
                        name2 = user2.get('username', 'User')
                    
                    leaderboard.append({
                        'user1_id': user_id,
                        'user2_id': friend_id,
                        'name1': name1,
                        'name2': name2,
                        'streak': current_streak
                    })
                    
                    if len(leaderboard) >= 10:
                        break
                        
            except Exception as e:
                logger.error(f"Error getting user info for streak leaderboard: {e}")
                continue
        
        logger.info(f"LEADERBOARD_STREAKS: Generated with {len(leaderboard)} entries")
        return leaderboard
        
    except Exception as e:
        logger.error(f"Error getting longest streaks: {e}")
        return []


def get_user_rank_in_weekly(user_id: int, weekly_scores: List[Dict]) -> Tuple[int, int]:
    """Get user's rank and score in weekly leaderboard. Returns (rank, score) or (0, 0)"""
    for rank, entry in enumerate(weekly_scores, start=1):
        if int(entry['user_id']) == user_id:
            return rank, entry['score']
    return 0, 0


def get_user_rank_in_streaks(user_id: int, longest_streaks: List[Dict]) -> Tuple[int, int]:
    """Get user's best streak rank. Returns (rank, streak_days) or (0, 0)"""
    for rank, entry in enumerate(longest_streaks, start=1):
        if int(entry['user1_id']) == user_id or int(entry['user2_id']) == user_id:
            return rank, entry['streak']
    return 0, 0


async def show_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show leaderboard with weekly scores and longest streaks"""
    query = update.callback_query
    if query:
        await query.answer()
    
    user_id = update.effective_user.id
    lang = context.user_data.get('language', 'en')
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        # Get leaderboards
        weekly_scores = get_weekly_top_scores()
        longest_streaks = get_longest_streaks()
        
        # Build message
        text = get_leaderboard_text(lang, 'title') + '\n\n'
        
        # Weekly scores section
        text += get_leaderboard_text(lang, 'weekly_scores') + '\n'
        
        if weekly_scores:
            for rank, entry in enumerate(weekly_scores[:10], start=1):
                emoji = '🥇' if rank == 1 else '🥈' if rank == 2 else '🥉' if rank == 3 else '  '
                text += f'{emoji} {rank}. <b>{entry["name"]}</b> — {entry["score"]}%\n'
            
            # Show user's rank if not in top 10
            user_rank, user_score = get_user_rank_in_weekly(user_id, weekly_scores)
            if user_rank > 10:
                text += f'\n{get_leaderboard_text(lang, "your_rank")} #{user_rank} ({user_score}%)\n'
        else:
            text += f'<i>{get_leaderboard_text(lang, "no_data")}</i>\n'
        
        text += '\n'
        
        # Longest streaks section
        text += get_leaderboard_text(lang, 'longest_streaks') + '\n'
        
        if longest_streaks:
            for rank, entry in enumerate(longest_streaks[:10], start=1):
                emoji = '🔥' if rank == 1 else '🌟' if rank == 2 else '✨' if rank == 3 else '  '
                text += f'{emoji} {rank}. <b>{entry["name1"]}</b> & <b>{entry["name2"]}</b> — {entry["streak"]} {get_leaderboard_text(lang, "days")}\n'
            
            # Show user's best streak if not in top 10
            streak_rank, streak_days = get_user_rank_in_streaks(user_id, longest_streaks)
            if streak_rank > 10:
                text += f'\n{get_leaderboard_text(lang, "your_rank")} #{streak_rank} ({streak_days} {get_leaderboard_text(lang, "days")})\n'
        else:
            text += f'<i>{get_leaderboard_text(lang, "no_data")}</i>\n'
        
        keyboard = [[InlineKeyboardButton(
            get_leaderboard_text(lang, 'back'),
            callback_data='streaks_menu'
        )]]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if query:
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
            
    except Exception as e:
        logger.error(f"Error showing leaderboard: {e}")
        import traceback
        logger.error(traceback.format_exc())
        error_text = "❌ Error loading leaderboard"
        if query:
            await query.edit_message_text(error_text)
        else:
            await update.message.reply_text(error_text)


async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /leaderboard command"""
    # Get user language
    user_id = update.effective_user.id
    try:
        result = supabase.table('friends_users').select('language').eq('telegram_id', str(user_id)).execute()
        if result.data:
            context.user_data['language'] = result.data[0]['language']
    except Exception:
        context.user_data['language'] = 'en'
    
    await show_leaderboard(update, context)