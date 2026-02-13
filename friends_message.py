import asyncio
from telegram import Bot
from telegram.error import TelegramError
import aiohttp
from dotenv import load_dotenv
import os
import logging
from supabase import create_client, Client
from config import *

load_dotenv(dotenv_path=".env")
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot token for Simple Friends
TOKEN_SIMPLE_FRIENDS = os.environ.get('BOT_TOKEN')

ADMIN_ID = int(os.environ.get("ADMIN_ID", "999932510"))

MAX_CONCURRENT = 30
BATCH_SIZE = 100
DELAY = 1.0

def fetch_users():
    """Fetch all users from friends_users table"""
    try:
        response = supabase.table("friends_users").select("telegram_id,first_name,language").execute()
        users = []
        for row in response.data:
            users.append({
                "id": row["telegram_id"],
                "name": row["first_name"] or "Friend",
                "language": row["language"] or "en"
            })
        return users
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        return []

def escape_markdown_v2(text):
    """Escape special characters for MarkdownV2"""
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text

def generate_message(name, language):
    """Generate personalized message based on user's language"""
    escaped_name = escape_markdown_v2(name)

    if language == "en":
        return (
            f"Hey {escaped_name}\\! 👋\n\n"
            "🏆 *Our record in solving friendship tests is 80%\\!*\n\n"
            "🤔 Do we have someone who can break this record?\n\n"
            "💪 *Challenge your best friend NOW:*\n"
            "• Create your unique friendship test\n"
            "• Send it to your closest friends\n"
            "• See who really knows you best\\!\n\n"
            "🔥 Can someone's friendship break the 80% record?\n\n"
            "⚡️ Start the challenge:\n"
            "/start\n\n"
            "🎯 *Test your friendship \\- prove you're the best\\!*"
        )

    elif language == "ru":
        return (
            f"Привет, {escaped_name}\\! 👋\n\n"
            "🏆 *Наш рекорд в тестах на дружбу \\— 80%\\!*\n\n"
            "🤔 Есть ли тот, кто сможет побить этот рекорд?\n\n"
            "💪 *Бросьте вызов своему лучшему другу СЕЙЧАС:*\n"
            "• Создайте свой уникальный тест на дружбу\n"
            "• Отправьте его самым близким друзьям\n"
            "• Узнайте, кто знает вас лучше всех\\!\n\n"
            "🔥 Сможет ли чья\\-то дружба побить рекорд 80%?\n\n"
            "⚡️ Начните испытание:\n"
            "/start\n\n"
            "🎯 *Проверьте свою дружбу \\- докажите, что вы лучшие\\!*"
        )

    elif language == "uz":
        return (
            f"Salom, {escaped_name}\\! 👋\n\n"
            "🏆 *Do'stlik testidagi yangi rekordimiz 80%\\!*\n\n"
            "🤔 Bu rekordni buzadiganlar bormi?\n\n"
            "• O'zingizning do'stlik testingizni yarating\n"
            "• Eng yaqin do'stlaringizga yuboring\n"
            "• Kim sizni yaxshiroq bilarkin, bilib oling\\!\n\n"
            "🔥 Kimningdir do'stligi 80% rekordni buzadimi?\n\n"
            "⚡️ Tezda sinab ko'ring:\n"
            "/start\n\n"
            "🎯 *Do'stligingizni sinab ko'ring \\- eng yaxshi ekanligingizni isbotlang\\!*"
        )
    
    # Default to English if language not recognized
    else:
        return generate_message(name, "en")

async def send_message_safe(session, bot_token, chat_id, message):
    """Send a single message with error handling"""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'MarkdownV2',
        'disable_web_page_preview': True
    }
    
    try:
        async with session.post(url, json=payload) as response:
            if response.status == 200:
                return {"success": True, "chat_id": chat_id}
            else:
                error_text = await response.text()
                return {"success": False, "chat_id": chat_id, "error": error_text}
    except Exception as e:
        return {"success": False, "chat_id": chat_id, "error": str(e)}

async def send_batch(batch, bot_token):
    """Send messages to a batch of users concurrently"""
    connector = aiohttp.TCPConnector(limit=MAX_CONCURRENT)
    timeout = aiohttp.ClientTimeout(total=30)
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        tasks = []
        for user in batch:
            message = generate_message(user["name"], user["language"])
            task = send_message_safe(session, bot_token, user["id"], message)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results

async def send_to_all_users():
    """Send broadcast message to all users"""
    users = fetch_users()
    
    if not users:
        print("No users found")
        return
    
    print(f"Sending to {len(users)} users...")
    
    successful = 0
    failed = 0
    
    for i in range(0, len(users), BATCH_SIZE):
        batch = users[i:i + BATCH_SIZE]
        batch_num = (i // BATCH_SIZE) + 1
        total_batches = (len(users) + BATCH_SIZE - 1) // BATCH_SIZE
        
        print(f"Batch {batch_num}/{total_batches}...")
        
        try:
            results = await send_batch(batch, TOKEN_SIMPLE_FRIENDS)
            
            for result in results:
                if isinstance(result, Exception):
                    failed += 1
                    logger.error(f"Exception: {result}")
                    continue
                
                if result["success"]:
                    successful += 1
                else:
                    failed += 1
                    logger.warning(f"Failed to send to {result['chat_id']}: {result.get('error', 'Unknown error')}")
            
            if i + BATCH_SIZE < len(users):
                await asyncio.sleep(DELAY)
                
        except Exception as e:
            print(f"Error in batch {batch_num}: {e}")
            logger.error(f"Batch error: {e}")
            failed += len(batch)
    
    print(f"\n{'='*50}")
    print(f"BROADCAST COMPLETED")
    print(f"{'='*50}")
    print(f"✅ Successfully sent: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Success rate: {(successful/(successful+failed)*100):.1f}%")

async def send_test_message(user_id, language="en"):
    """Send a test message to a specific user"""
    bot = Bot(token=TOKEN_SIMPLE_FRIENDS)
    
    users = fetch_users()
    user = next((u for u in users if u["id"] == user_id), None)
    
    if not user:
        name = "Friend"
    else:
        name = user["name"]
        language = user["language"]
    
    message = generate_message(name, language)
    
    try:
        await bot.send_message(
            chat_id=user_id,
            text=message,
            parse_mode='MarkdownV2',
            disable_web_page_preview=True
        )
        print(f"✅ Test message sent to {user_id}")
    except TelegramError as e:
        print(f"❌ Failed to send: {e}")
        logger.error(f"Test message error: {e}")

async def main():
    """Main menu for broadcast operations"""
    users = fetch_users()
    
    print("=" * 50)
    print("SIMPLE FRIENDS BROADCAST")
    print("=" * 50)
    print(f"Total users: {len(users)}")
    
    print("\nWhat would you like to do?")
    print("1. Send messages to all users")
    print("2. Send test message to one user")
    print("3. Send test message to admin")
    print("4. Exit")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        print(f"\n⚠️  You are about to send messages to {len(users)} users")
        
        # Show language distribution
        lang_count = {"en": 0, "ru": 0, "uz": 0, "other": 0}
        for user in users:
            lang = user.get("language", "en")
            if lang in lang_count:
                lang_count[lang] += 1
            else:
                lang_count["other"] += 1
        
        print(f"\n📊 Language distribution:")
        print(f"   English: {lang_count['en']} users")
        print(f"   Russian: {lang_count['ru']} users")
        print(f"   Uzbek: {lang_count['uz']} users")
        if lang_count['other'] > 0:
            print(f"   Other: {lang_count['other']} users (will receive English)")
        
        print("\n📝 Message previews (personalized by language):")
        print("=" * 50)
        
        # Show English preview
        print("\n🇬🇧 ENGLISH VERSION:")
        print("-" * 50)
        preview_en = generate_message("Friend", "en").replace("\\", "")
        print(preview_en)
        
        # Show Russian preview
        print("\n🇷🇺 RUSSIAN VERSION:")
        print("-" * 50)
        preview_ru = generate_message("Друг", "ru").replace("\\", "")
        print(preview_ru)
        
        # Show Uzbek preview
        print("\n🇺🇿 UZBEK VERSION:")
        print("-" * 50)
        preview_uz = generate_message("Do'stim", "uz").replace("\\", "")
        print(preview_uz)
        print("=" * 50)
        
        confirm = input(f"\n✅ Send personalized messages to {len(users)} users? (yes/no): ").lower().strip()
        if confirm in ["yes", "y"]:
            await send_to_all_users()
        else:
            print("❌ Cancelled")
    
    elif choice == "2":
        test_user_id = input("Enter user ID: ").strip()
        try:
            test_user_id = int(test_user_id)
            test_language = input("Enter language (en/ru/uz) [default: en]: ").lower().strip()
            if test_language not in ["en", "ru", "uz"]:
                test_language = "en"
            await send_test_message(test_user_id, test_language)
        except ValueError:
            print("❌ Invalid user ID")
    
    elif choice == "3":
        if ADMIN_ID == 0:
            print("❌ Admin ID not set in environment")
        else:
            test_language = input("Enter language (en/ru/uz) [default: en]: ").lower().strip()
            if test_language not in ["en", "ru", "uz"]:
                test_language = "en"
            await send_test_message(ADMIN_ID, test_language)
    
    elif choice == "4":
        print("👋 Goodbye")
    
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.error(f"Main error: {e}")