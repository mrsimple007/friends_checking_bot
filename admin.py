from config import *

async def get_total_users() -> int:
    try:
        result = supabase.table('friends_users').select('telegram_id', count='exact').execute()
        return result.count or 0
    except Exception as e:
        logger.error(f"Error getting total users: {e}")
        return 0

async def get_total_birthdays() -> int:
    try:
        result = supabase.table('birthdays').select('id', count='exact').execute()
        return result.count or 0
    except Exception as e:
        logger.error(f"Error getting total birthdays: {e}")
        return 0

async def get_total_tests() -> int:
    try:
        result = supabase.table('tests').select('id', count='exact').execute()
        return result.count or 0
    except Exception as e:
        logger.error(f"Error getting total tests: {e}")
        return 0

async def get_total_test_results() -> int:
    try:
        result = supabase.table('test_results').select('id', count='exact').execute()
        return result.count or 0
    except Exception as e:
        logger.error(f"Error getting total test results: {e}")
        return 0

async def get_todays_active_users() -> int:
    try:
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        # Count users who created a birthday or test or result today
        birthdays_today = supabase.table('birthdays').select('user_id').gte('created_at', today_start).execute()
        tests_today = supabase.table('tests').select('user_id').gte('created_at', today_start).execute()
        results_today = supabase.table('test_results').select('user_id').gte('created_at', today_start).execute()

        unique_users = set()
        for row in (birthdays_today.data or []):
            unique_users.add(row['user_id'])
        for row in (tests_today.data or []):
            unique_users.add(row['user_id'])
        for row in (results_today.data or []):
            unique_users.add(row['user_id'])
        return len(unique_users)
    except Exception as e:
        logger.error(f"Error getting today's active users: {e}")
        return 0

async def get_premium_users() -> int:
    try:
        result = supabase.table('friends_users').select('telegram_id', count='exact').eq('is_premium', True).execute()
        return result.count or 0
    except Exception as e:
        logger.error(f"Error getting premium users: {e}")
        return 0