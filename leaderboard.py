import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Tuple
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from config import ADMIN_IDS, supabase
import urllib.parse
import asyncio

logger = logging.getLogger(__name__)

LEADERBOARD_TRANSLATIONS = {
    'uz': {
        'title': '🏆 <b>Liderlar jadvali</b>',
        'weekly_scores_results': '📊 <b>Haftalik eng yaxshi test natijalari: </b>',
        'longest_streaks': '🔥 <b>Eng uzun har kunlik muloqotlar: </b>',
        'your_rank': '📍 <b>Sizning o\'rningiz:</b>',
        'no_data': '😔 Ma\'lumotlar yo\'q',
        'back': '◀️ Orqaga',
        'rank': '#{rank}',
        'days': 'kun',
        'score': 'ball',
        'weekly_scores': '📊 <b>Haftalik eng ko\'p yechilgan testlar: </b>',
    },
    'ru': {
        'title': '🏆 <b>Таблица лидеров</b>',
        'weekly_scores_results': '📊 <b>Лучшие результаты тестов недели: </b>',
        'longest_streaks': '🔥 <b>Самые длинные ежедневные общения: </b>',
        'your_rank': '📍 <b>Ваше место:</b>',
        'no_data': '😔 Нет данных',
        'back': '◀️ Назад',
        'rank': '#{rank}',
        'days': 'дней',
        'score': 'балл',
        'weekly_scores': '📊 <b>Самые решаемые тесты недели: </b>',
    },
    'en': {
        'title': '🏆 <b>Leaderboard</b>',
        'weekly_scores_results': '📊 <b>Top Weekly Test Scores: </b>',
        'longest_streaks': '🔥 <b>Longest Daily Communications: </b>',
        'your_rank': '📍 <b>Your Rank:</b>',
        'no_data': '😔 No data available',
        'back': '◀️ Back',
        'rank': '#{rank}',
        'days': 'days',
        'score': 'score',
        'weekly_scores': '📊 <b>Top test owners this week: </b>', 
    }
}

def get_leaderboard_text(lang: str, key: str) -> str:
    """Get translated leaderboard text"""
    return LEADERBOARD_TRANSLATIONS.get(lang, LEADERBOARD_TRANSLATIONS['en']).get(key, key)


def get_weekly_top_scores() -> List[Dict]:
    """Get top 10 test owners whose tests were solved the most this week"""
    try:
        now = datetime.now(timezone.utc)
        start_of_week = now - timedelta(days=now.weekday())
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)

        results = supabase.table('test_results')\
            .select('test_id, created_at')\
            .gte('created_at', start_of_week.isoformat())\
            .limit(500)\
            .execute()

        if not results.data:
            return []

        # Count how many times each test was solved
        test_solve_counts = {}
        for result in results.data:
            test_id = result['test_id']
            test_solve_counts[test_id] = test_solve_counts.get(test_id, 0) + 1

        # Get test owners
        test_ids = list(test_solve_counts.keys())
        tests_result = supabase.table('tests')\
            .select('id, user_id')\
            .in_('id', test_ids)\
            .execute()

        if not tests_result.data:
            return []

        # Map test_id -> owner user_id, aggregate by owner
        owner_solve_counts = {}
        for test in tests_result.data:
            owner_id = test['user_id']
            count = test_solve_counts.get(test['id'], 0)
            owner_solve_counts[owner_id] = owner_solve_counts.get(owner_id, 0) + count

        # Sort by solve count descending, take top 10
        from config import ADMIN_IDS
        top_owners = sorted(owner_solve_counts.items(), key=lambda x: x[1], reverse=True)
        top_owners = [(uid, count) for uid, count in top_owners if str(uid) not in ADMIN_IDS]
        top_owners = top_owners[:10]

        # Batch fetch user info
        owner_ids = [str(uid) for uid, _ in top_owners]
        user_info_result = supabase.table('friends_users')\
            .select('telegram_id, first_name, last_name, username')\
            .in_('telegram_id', owner_ids)\
            .execute()

        user_info_map = {}
        if user_info_result.data:
            for user in user_info_result.data:
                user_info_map[user['telegram_id']] = user

        SKIP_NAMES = ['jimjitlik']  

        leaderboard = []
        for owner_id, solve_count in top_owners:
            user = user_info_map.get(str(owner_id))
            if user:
                name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
                if not name:
                    name = user.get('username', 'User')
            else:
                name = 'User'

            # Skip admin profiles
            if name.lower() in SKIP_NAMES:
                continue

            leaderboard.append({
                'user_id': owner_id,
                'name': name,
                'solve_count': solve_count
            })

        return leaderboard[:10]

    except Exception as e:
        logger.error(f"Error getting weekly top scores: {e}")
        return []

def get_weekly_top_score_results() -> List[Dict]:
    """Get top 10 individual test results this week with taker & owner names"""
    try:
        now = datetime.now(timezone.utc)
        start_of_week = now - timedelta(days=now.weekday())
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)

        results = supabase.table('test_results')\
            .select('user_id, score, test_id, created_at')\
            .gte('created_at', start_of_week.isoformat())\
            .order('score', desc=True)\
            .order('created_at', desc=False)\
            .limit(100)\
            .execute()

        if not results.data:
            return []

        # Best score per taker
        seen_takers = {}
        for r in results.data:
            uid = r['user_id']
            if uid not in seen_takers or r['score'] > seen_takers[uid]['score']:
                seen_takers[uid] = r

        top_results = sorted(seen_takers.values(), key=lambda x: x['score'], reverse=True)[:10]

        # Collect all user IDs and test IDs
        taker_ids = [r['user_id'] for r in top_results]
        test_ids = [r['test_id'] for r in top_results]

        # Fetch test owners
        tests = supabase.table('tests').select('id, user_id').in_('id', test_ids).execute()
        test_owner_map = {t['id']: t['user_id'] for t in (tests.data or [])}

        owner_ids = list(set(test_owner_map.values()))
        all_ids = list(set(taker_ids + owner_ids))

        # Batch fetch user info
        user_info_result = supabase.table('friends_users')\
            .select('telegram_id, first_name, last_name, username')\
            .in_('telegram_id', all_ids)\
            .execute()

        user_map = {}
        for u in (user_info_result.data or []):
            name = f"{u.get('first_name', '')} {u.get('last_name', '')}".strip()
            if not name:
                name = u.get('username', 'User')
            user_map[u['telegram_id']] = name

        leaderboard = []
        for r in top_results:
            taker_name = user_map.get(str(r['user_id']), 'User')
            owner_id = test_owner_map.get(r['test_id'])
            owner_name = user_map.get(str(owner_id), 'User') if owner_id else 'User'

            leaderboard.append({
                'taker_id': r['user_id'],
                'taker_name': taker_name,
                'owner_name': owner_name,
                'score': r['score']
            })

        return leaderboard

    except Exception as e:
        logger.error(f"Error getting weekly top score results: {e}")
        return []



def get_longest_streaks() -> List[Dict]:
    """Get top 10 longest current streaks (OPTIMIZED)"""
    try:
        # Get top 30 streaks (faster than 40)
        streaks = supabase.table('friendship_streaks')\
            .select('user_id, friend_id, current_streak')\
            .gt('current_streak', 0)\
            .order('current_streak', desc=True)\
            .limit(30)\
            .execute()
        
        if not streaks.data:
            return []
        
        leaderboard = []
        seen_pairs = set()
        
        # Collect all user IDs to batch fetch
        all_user_ids = set()
        valid_streaks = []
        
        for streak in streaks.data:
            user_id = int(streak['user_id'])
            friend_id = int(streak['friend_id'])
            current_streak = streak['current_streak']
            
            if current_streak == 0:
                continue
            
            pair = tuple(sorted([user_id, friend_id]))
            if pair in seen_pairs:
                continue
            
            seen_pairs.add(pair)
            valid_streaks.append((user_id, friend_id, current_streak))
            all_user_ids.add(str(user_id))
            all_user_ids.add(str(friend_id))
            
            if len(valid_streaks) >= 10:
                break
        
        # Batch fetch all user info at once
        user_info_result = supabase.table('friends_users')\
            .select('telegram_id, first_name, last_name, username')\
            .in_('telegram_id', list(all_user_ids))\
            .execute()
        
        # Create user info map
        user_info_map = {}
        if user_info_result.data:
            for user in user_info_result.data:
                user_info_map[user['telegram_id']] = user
        
        # Build leaderboard
        for user_id, friend_id, current_streak in valid_streaks:
            user1 = user_info_map.get(str(user_id))
            user2 = user_info_map.get(str(friend_id))
            
            if user1 and user2:
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
        
        logger.info(f"LEADERBOARD_STREAKS: Generated with {len(leaderboard)} entries")
        return leaderboard
        
    except Exception as e:
        logger.error(f"Error getting longest streaks: {e}")
        return []


def get_user_rank_in_weekly(user_id: int, weekly_scores: List[Dict]) -> Tuple[int, int]:
    for rank, entry in enumerate(weekly_scores, start=1):
        if int(entry['user_id']) == user_id:
            return rank, entry['solve_count']
    return 0, 0


def get_user_rank_in_streaks(user_id: int, longest_streaks: List[Dict]) -> Tuple[int, int]:
    """Get user's best streak rank. Returns (rank, streak_days) or (0, 0)"""
    for rank, entry in enumerate(longest_streaks, start=1):
        if int(entry['user1_id']) == user_id or int(entry['user2_id']) == user_id:
            return rank, entry['streak']
    return 0, 0

async def show_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show leaderboard: top solved counts + top scores"""
    query = update.callback_query
    if query:
        await query.answer()

    user_id = update.effective_user.id
    lang = context.user_data.get('language', 'en')

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        weekly_scores, score_results = await asyncio.gather(
            asyncio.to_thread(get_weekly_top_scores),
            asyncio.to_thread(get_weekly_top_score_results),
            return_exceptions=True
        )

        if isinstance(weekly_scores, Exception):
            logger.error(f"Error getting weekly scores: {weekly_scores}")
            weekly_scores = []
        if isinstance(score_results, Exception):
            logger.error(f"Error getting score results: {score_results}")
            score_results = []

        text = get_leaderboard_text(lang, 'title') + '\n\n'

        # Section 1: Most solved tests
        times_label = {'uz': 'marta', 'ru': 'раз', 'en': 'times'}.get(lang, 'times')
        most_solved_titles = {
            'uz': '🎯 <b>Eng ko\'p yechilgan testlar:</b>',
            'ru': '🎯 <b>Самые решаемые тесты:</b>',
            'en': '🎯 <b>Most Solved Tests:</b>'
        }
        text += most_solved_titles.get(lang, most_solved_titles['en']) + '\n'

        if weekly_scores:
            for rank, entry in enumerate(weekly_scores[:10], start=1):
                emoji = '🥇' if rank == 1 else '🥈' if rank == 2 else '🥉' if rank == 3 else '  '
                text += f'{emoji} {rank}. <b>{entry["name"]}</b> — {entry["solve_count"]} {times_label}\n'

            user_rank, user_count = get_user_rank_in_weekly(user_id, weekly_scores)
            if user_rank > 10 and user_rank > 0:
                text += f'\n{get_leaderboard_text(lang, "your_rank")} #{user_rank} ({user_count} {times_label})\n'
        else:
            text += f'<i>{get_leaderboard_text(lang, "no_data")}</i>\n'

        text += '\n'

        # Section 2: Top scores (taker & owner)
        text += get_leaderboard_text(lang, 'weekly_scores_results') + '\n'

        if score_results:
            for rank, entry in enumerate(score_results[:10], start=1):
                emoji = '🥇' if rank == 1 else '🥈' if rank == 2 else '🥉' if rank == 3 else '  '
                text += f'{emoji} {rank}. <b>{entry["taker_name"]}</b> & <b>{entry["owner_name"]}</b> — {entry["score"]}%\n'
        else:
            text += f'<i>{get_leaderboard_text(lang, "no_data")}</i>\n'

        # Share link
        bot_username = context.bot.username
        streak_link = f"https://t.me/{bot_username}?start=streak_{user_id}"

        user_info = supabase.table('friends_users')\
            .select('first_name, last_name')\
            .eq('telegram_id', str(user_id))\
            .execute()

        user_name = 'Friend'
        if user_info.data:
            user_name = f"{user_info.data[0].get('first_name', '')} {user_info.data[0].get('last_name', '')}".strip()

        share_messages = {
            'uz': f"👋 Salom! Men {user_name} siz bilan har kunlik muloqotni boshlashni xohlayman!\n\n🔥 Boshlash uchun havolani bosing:\n{streak_link}",
            'ru': f"👋 Привет! {user_name} хочет начать ежедневное общение с вами!\n\n🔥 Нажмите ссылку, чтобы начать:\n{streak_link}",
            'en': f"👋 Hey! {user_name} wants to start daily communication with you!\n\n🔥 Click the link to start:\n{streak_link}"
        }
        share_text_encoded = urllib.parse.quote(share_messages.get(lang, share_messages['en']))

        button_labels = {
            'uz': {'share': '📤 Do\'stingizga yuboring', 'my_test': '📝 Mening testim'},
            'ru': {'share': '📤 Отправьте друзьям', 'my_test': '📝 Мой тест'},
            'en': {'share': '📤 Share with friends', 'my_test': '📝 My test'}
        }
        labels = button_labels.get(lang, button_labels['en'])

        keyboard = [
            [InlineKeyboardButton(labels['share'], url=f"https://t.me/share/url?url={streak_link}&text={share_text_encoded}")],
            [InlineKeyboardButton(labels['my_test'], callback_data='my_tests')],
            [InlineKeyboardButton(get_leaderboard_text(lang, 'back'), callback_data='streaks_menu')]
        ]
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