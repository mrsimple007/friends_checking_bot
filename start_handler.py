import os
import logging
from datetime import datetime, timezone, timedelta
import asyncio
import json
import uuid
from typing import Dict, List, Optional

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ConversationHandler,
    CallbackQueryHandler, filters, ContextTypes
)
from telegram.constants import ParseMode
from config import supabase, model, TELEGRAM_BOT_TOKEN, FREE_BIRTHDAY_LIMIT, FREE_TEST_LIMIT
from share import share_main
from balance import premium_info_handler, subscribe_callback, approve_premium_payment, decline_premium_payment
import urllib.parse
from admin import *

async def notify_admin_new_user(context: ContextTypes.DEFAULT_TYPE, user_id: int, username: str, first_name: str, last_name: str):
    """Notify admin about new user registration"""
    try:
        # Get total counts
        total_users, total_streaks = await asyncio.gather(
            get_total_users(),
            get_total_streaks()
        )
        
        # Format user info
        full_name = f"{first_name or ''} {last_name or ''}".strip()
        username_str = f"@{username}" if username else "No username"
        
        admin_message = (
            "🆕 <b>New User Registered!</b>\n\n"
            f"👤 <b>Name:</b> {full_name or 'No name'}\n"
            f"🔤 <b>Username:</b> {username_str}\n"
            f"🆔 <b>User ID:</b> <code>{user_id}</code>\n\n"
            f"📊 <b>Total Users:</b> {total_users}\n"
            f"🔥 <b>Active Streaks:</b> {total_streaks}"
        )
        
        # Send to all notification admins
        for admin_id in NOTIFICATION_ADMIN_IDS:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=admin_message,
                    parse_mode=ParseMode.HTML
                )
            except Exception as e:
                logger.error(f"Error sending notification to admin {admin_id}: {e}")
    
    except Exception as e:
        logger.error(f"Error in notify_admin_new_user: {e}")



# Helper Functions
def get_text(lang: str, key: str) -> str:
    from translations import TRANSLATIONS
    """Get translated text"""
    return TRANSLATIONS.get(lang, TRANSLATIONS['en']).get(key, key)

def get_user_language(user_id: int) -> str:
    """Get user's language from database"""
    try:
        result = supabase.table('friends_users').select('language').eq('telegram_id', str(user_id)).execute()
        if result.data:
            return result.data[0]['language']
    except Exception as e:
        logger.error(f"Error getting user language: {e}")
    return 'en'


def save_user(telegram_id: int, username: str, language: str, is_premium: bool = False, first_name: str = None, last_name: str = None):
    """Save or update user in database"""
    try:
        user_data = {
            'telegram_id': str(telegram_id),
            'username': username,
            'first_name': first_name or '',
            'last_name': last_name or '',
            'language': language,
            'is_premium': is_premium,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        supabase.table('friends_users').upsert(user_data).execute()
        logger.info(f"User {telegram_id} saved with language {language}")
    except Exception as e:
        logger.error(f"Error saving user: {e}")


async def show_language_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show language selection keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("🇺🇿 O‘zbekcha", callback_data='lang_uz'),
            InlineKeyboardButton("🇷🇺 Русский", callback_data='lang_ru'),
        ],
        [InlineKeyboardButton("🇬🇧 English", callback_data='lang_en')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = (
        "🌍 <b>Tilni tanlang / Выберите язык / Choose your language</b>\n\n"
        "🇺🇿 Bu bot do‘stlaringizning tug‘ilgan kunlarini eslab qolishga 🎂 "
        "va qiziqarli do‘stlik testlarini yaratishga yordam beradi 🫶\n\n"
        "🇷🇺 Этот бот помогает запоминать дни рождения друзей 🎉 "
        "и создавать весёлые тесты на дружбу 🤝\n\n"
        "🇬🇧 This bot helps you remember your friends’ birthdays 🎈 "
        "and create fun friendship tests 💖\n\n"
        "👇 <i>Iltimos, davom etish uchun tilni tanlang</i>"
    )

    if update.callback_query:
        await update.callback_query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
    else:
        await update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )

async def language_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from main import show_taking_test_question
    """Handle language selection"""
    query = update.callback_query
    await query.answer()
    
    lang = query.data.split('_')[1]
    user = update.effective_user

    logger.info(f"LANGUAGE_SELECTED: User {user.id} (@{user.username}) selected language: {lang}")

    # Update user language (user already exists from start())
    try:
        supabase.table('friends_users').update({'language': lang}).eq('telegram_id', str(user.id)).execute()
        logger.info(f"User {user.id} language updated to {lang}")
    except Exception as e:
        logger.error(f"Error updating user language: {e}")
        # Fallback: save user again
        save_user(user.id, user.username or '', lang, first_name=user.first_name or '', last_name=user.last_name or '')
    
    # Check if there's a pending test
    if 'pending_test_id' in context.user_data:
        test_id = context.user_data.pop('pending_test_id')
        
        # Show welcome message
        welcome_text = get_text(lang, 'welcome')
        await query.edit_message_text(welcome_text, parse_mode=ParseMode.HTML)
        
        await asyncio.sleep(1)
        
        try:
            result = supabase.table('tests').select('*').eq('id', test_id).execute()
            
            if not result.data:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="❌ Test not found",
                    parse_mode=ParseMode.HTML
                )
                return
            
            # Check if user already took this test
            existing_result = supabase.table('test_results').select('score').eq('test_id', test_id).eq('user_id', str(user.id)).execute()
            
            if existing_result.data:
                score = existing_result.data[0]['score']
                logger.info(f"TEST_ALREADY_TAKEN: User {user.id} already took test {test_id} | Score: {score}%")

                already_taken_text = {
                    'uz': f"✅ Siz bu testni allaqachon topshirgansiz!\n\n📊 Sizning natijangiz: <b>{score}%</b>",
                    'ru': f"✅ Вы уже проходили этот тест!\n\n📊 Ваш результат: <b>{score}%</b>",
                    'en': f"✅ You have already taken this test!\n\n📊 Your score: <b>{score}%</b>"
                }
                
                keyboard = [
                    [InlineKeyboardButton(
                        get_text(lang, 'create_your_test'),
                        callback_data='create_test'
                    )],
                    [InlineKeyboardButton(
                        get_text(lang, 'add_birthday_button'),
                        callback_data='add_birthday'
                    )]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=already_taken_text.get(lang, already_taken_text['en']),
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.HTML
                )
                return
            
            # Initialize test taking
            context.user_data['taking_test_id'] = test_id
            context.user_data['taking_test_answers'] = {}
            context.user_data['taking_test_question'] = 0
            
            # Show intro
            intro_text = get_text(lang, 'test_intro')
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=intro_text,
                parse_mode=ParseMode.HTML
            )
            
            # Wait a bit before showing first question
            await asyncio.sleep(1)
            
            # Show first question
            await show_taking_test_question(update, context, lang)
            
        except Exception as e:
            logger.error(f"Error starting test after language selection: {e}")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ Error loading test",
                parse_mode=ParseMode.HTML
            )
        return
    
    # Show welcome message
    welcome_text = get_text(lang, 'welcome')
    await query.edit_message_text(welcome_text, parse_mode=ParseMode.HTML)
    
    # Show main menu
    await show_main_menu(update, context, lang)


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str):
    """Show main menu"""
    keyboard = [
        [
            InlineKeyboardButton(get_text(lang, 'add_birthday'), callback_data='add_birthday'),
            InlineKeyboardButton(get_text(lang, 'my_birthdays'), callback_data='my_birthdays')
        ],
        [
            InlineKeyboardButton(get_text(lang, 'create_test'), callback_data='create_test'),
            InlineKeyboardButton(get_text(lang, 'my_tests'), callback_data='my_tests')
        ],
        [
            InlineKeyboardButton(get_text(lang, 'streaks'), callback_data='streaks_menu'),  # More prominent
            InlineKeyboardButton(get_text(lang, 'leaderboard'), callback_data='streak_leaderboard')
        ],
        [
            InlineKeyboardButton(get_text(lang, 'premium'), callback_data='premium'),
            InlineKeyboardButton(get_text(lang, 'settings'), callback_data='settings')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    menu_text = get_text(lang, 'main_menu')
    
    if update.callback_query:
        await update.callback_query.edit_message_text(menu_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    else:
        # Send as new message
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=menu_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )



@log_user_action("BOT_START")
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    # Clear any ongoing conversation data
    context.user_data.clear()
    
    # NEW: Check if this is a streak link
    if context.args and context.args[0].startswith('streak_'):
        await handle_streak_link(update, context)
        return
    
    # Check if this is a test link
    if context.args and context.args[0].startswith('s_'):
        test_id = context.args[0][2:]
        logger.info(f"USER_ACTION: User {user.id} ({user.first_name} {user.last_name}) started taking test {test_id}")
        await start_taking_test(update, context, test_id)
        return
    
    # Regular start - check if user exists
    try:
        result = supabase.table('friends_users').select('*').eq('telegram_id', str(user.id)).execute()
        
        if result.data:
            # Existing user - get their language and show main menu directly
            lang = result.data[0]['language']
            logger.info(f"USER_ACTION: Existing user {user.id} started bot with language {lang}")
            
            # Show admin dashboard if admin
            if user.id in NOTIFICATION_ADMIN_IDS:
                total_users, total_birthdays, total_tests, total_results, todays_active, premium_count, total_streaks, longest_streak, avg_streak = await asyncio.gather(
                    get_total_users(),
                    get_total_birthdays(),
                    get_total_tests(),
                    get_total_test_results(),
                    get_todays_active_users(),
                    get_premium_users(),
                    get_total_streaks(),
                    get_longest_streak(),
                    get_average_streak()
                )

                admin_message = (
                    "👑 <b>Admin Dashboard</b>\n\n"
                    f"👤 <b>Total Users:</b> {total_users}\n"
                    f"💎 <b>Premium Users:</b> {premium_count}\n"
                    f"👥 <b>Active Today:</b> {todays_active}\n\n"
                    f"📈 <b>Content:</b>\n"
                    f"  🎂 Birthdays saved: {total_birthdays}\n"
                    f"  📝 Tests created: {total_tests}\n"
                    f"  ✅ Tests taken: {total_results}\n"
                    f"  🔥 Active streaks: {total_streaks}\n\n"
                    f"📊 <b>Averages:</b>\n"
                    f"  • Birthdays / user: {total_birthdays / total_users if total_users else 0:.1f}\n"
                    f"  • Tests taken / test: {total_results / total_tests if total_tests else 0:.1f}\n\n"
                    f"🏆 <b>Streak Stats:</b>\n"
                    f"  • Longest streak: {longest_streak} days\n"
                    f"  • Average streak: {avg_streak:.1f} days"
                )

                await update.message.reply_text(
                    text=admin_message,
                    parse_mode=ParseMode.HTML
                )
            
            # Show main menu directly for existing users
            await show_main_menu(update, context, lang)
        else:
            # New user - save with default language and show language selection
            save_user(
                telegram_id=user.id,
                username=user.username or '',
                language='uz',  # Default language
                is_premium=False,
                first_name=user.first_name or '',
                last_name=user.last_name or ''
            )
            logger.info(f"NEW_USER_AUTO_SAVED: User {user.id} auto-saved with default language 'uz'")
            await notify_admin_new_user(
                context=context,
                user_id=user.id,
                username=user.username or '',
                first_name=user.first_name or '',
                last_name=user.last_name or ''
            )
            
            # Show language selection for new users
            await show_language_selection(update, context)
            
    except Exception as e:
        logger.error(f"Error in start: {e}")
        await show_language_selection(update, context)


async def handle_streak_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle streak link clicks with dynamic messaging and share button"""
    from friendship_streaks import get_or_create_streak, update_streak, get_streak_text
    from streak_actions import log_interaction, get_streak_message
    
    user = update.effective_user
    user_id = user.id
    
    # Parse streak link: streak_{sender_id}
    try:
        parts = context.args[0].split('_')
        sender_id = int(parts[1])
        
        # Check if user is clicking their own link
        if user_id == sender_id:
            messages = {
                'uz': "😁 O'zingiz bilan har kunlik muloqot boshlay olmaysiz. Yaxshisi, u linkni do'stingizga yuboring! /start bilan botni qayta boshlang",
                'ru': "😁 Вы не можете начать ежедневное общение с собой. /start",
                'en': "😁 You cannot start a streak with yourself. /start"
            }
            lang = get_user_language(user_id)
            await update.message.reply_text(
                messages.get(lang, messages['en']),
                parse_mode=ParseMode.HTML
            )
            return
        
        # Get user language
        lang = get_user_language(user_id)
        
        # Get or create streak
        streak = get_or_create_streak(sender_id, user_id)
        if not streak:
            await update.message.reply_text("❌ Error creating streak")
            return
        
        # Update streak
        streak_days = update_streak(streak['id'], sender_id, user_id)
        
        # Log interaction
        log_interaction(streak['id'], sender_id, user_id, 'streak_link_clicked')
        
        # Get sender name and language
        sender_info = supabase.table('friends_users')\
            .select('first_name, last_name, language')\
            .eq('telegram_id', str(sender_id))\
            .execute()
        
        sender_name = 'Friend'
        sender_lang = 'en'
        if sender_info.data:
            sender_name = f"{sender_info.data[0].get('first_name', '')} {sender_info.data[0].get('last_name', '')}".strip()
            sender_lang = sender_info.data[0].get('language', 'en')
        
        # Get user name for sender notification
        user_name = f"{user.first_name} {user.last_name or ''}".strip()
        
        # Notify friend (the clicker) with dynamic message
        friend_message = get_streak_message(streak_days, lang)
        friend_message += f"\n\n👤 <b>{sender_name}</b>" + (" bilan" if lang == 'uz' else " с" if lang == 'ru' else " with")
        
        # Create share link for the clicker
        bot_username = context.bot.username
        clicker_streak_link = f"https://t.me/{bot_username}?start=streak_{user_id}"
        
        # Share messages for different languages
        share_messages = {
            'uz': f"👋 Salom! {user_name} siz bilan har kunlik muloqotni boshlashni xohlaydi!\n\n🔥 Boshlash uchun havolani bosing:\n{clicker_streak_link}",
            'ru': f"👋 Привет! {user_name} хочет начать ежедневное общение с вами!\n\n🔥 Нажмите ссылку, чтобы начать:\n{clicker_streak_link}",
            'en': f"👋 Hey! {user_name} wants to start daily communication with you!\n\n🔥 Click the link to start:\n{clicker_streak_link}"
        }
        
        share_text_encoded = urllib.parse.quote(share_messages.get(lang, share_messages['en']))
        
        # Button labels
        button_labels = {
            'uz': '📤 Siz ham do\'stingizga yuboring',
            'ru': '📤 Отправьте своим друзьям',
            'en': '📤 Share with your friends'
        }
        
        # Add share button
        keyboard = [
            [InlineKeyboardButton(
                button_labels.get(lang, button_labels['en']),
                url=f"https://t.me/share/url?url={clicker_streak_link}&text={share_text_encoded}"
            )]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            friend_message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
        
        # Notify sender with dynamic message
        sender_message = get_streak_message(streak_days, sender_lang, include_cta=False)
        sender_message += f"\n\n👤 <b>{user_name}</b>" + (" bilan" if sender_lang == 'uz' else " с" if sender_lang == 'ru' else " with")
        
        # Add additional context for sender
        sender_notif_prefix = {
            'uz': f"✅ <b>Do'stingiz havolani bosdi!</b>\n\n",
            'ru': f"✅ <b>Друг нажал на ссылку!</b>\n\n",
            'en': f"✅ <b>Your friend clicked the link!</b>\n\n"
        }
        
        await context.bot.send_message(
            chat_id=sender_id,
            text=sender_notif_prefix.get(sender_lang, sender_notif_prefix['en']) + sender_message,
            parse_mode=ParseMode.HTML
        )
        
        logger.info(f"STREAK_LINK_CLICKED: User {user_id} clicked streak link from {sender_id} | Streak: {streak_days} days")
        
    except Exception as e:
        logger.error(f"Error handling streak link: {e}")
        import traceback
        logger.error(traceback.format_exc())
        await update.message.reply_text("❌ Error processing streak link")

async def start_taking_test(update: Update, context: ContextTypes.DEFAULT_TYPE, test_id: str):
    from main import show_taking_test_question

    """Start taking a friend's test"""
    user_id = update.effective_user.id
    user = update.effective_user

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    # Check if user exists in database
    try:
        user_result = supabase.table('friends_users').select('*').eq('telegram_id', str(user_id)).execute()
        
        if not user_result.data:
            # New user - save with default language first
            save_user(
                telegram_id=user.id,
                username=user.username or '',
                language='uz',  # Default language
                is_premium=False,
                first_name=user.first_name or '',
                last_name=user.last_name or ''
            )
            logger.info(f"NEW_USER_AUTO_SAVED: User {user.id} auto-saved with default 'uz' before test")
            
            await notify_admin_new_user(
                context=context,
                user_id=user.id,
                username=user.username or '',
                first_name=user.first_name or '',
                last_name=user.last_name or ''
            )
            
            # Store test ID and show language selection
            context.user_data['pending_test_id'] = test_id
            await show_language_selection(update, context)
            return
        
        # Existing user - get their language
        lang = user_result.data[0]['language']
        
    except Exception as e:
        logger.error(f"Error checking user: {e}")
        # On error, save as new user and show language selection
        save_user(
            telegram_id=user.id,
            username=user.username or '',
            language='uz',
            is_premium=False,
            first_name=user.first_name or '',
            last_name=user.last_name or ''
        )
        await notify_admin_new_user(
            context=context,
            user_id=user.id,
            username=user.username or '',
            first_name=user.first_name or '',
            last_name=user.last_name or ''
        )
        
        context.user_data['pending_test_id'] = test_id
        await show_language_selection(update, context)
        return

    try:
        result = supabase.table('tests').select('*').eq('id', test_id).execute()
        
        if not result.data:
            await update.message.reply_text("❌ Test not found", parse_mode=ParseMode.HTML)
            return
        
        test = result.data[0]
        test_owner_id = test['user_id']
        
        # Check if user is taking their own test
        if str(user_id) == test_owner_id:
            own_test_messages = {
                'uz': (
                    "😄 <b>Bu o'zingizning testingiz!</b>\n\n"
                    "O'zingizni tekshirish yaxshi, lekin testni do'stlaringizga yuboring - "
                    "ular sizni qanchalik yaxshi bilishini bilib oling! 🎯\n\n"
                    "👇 Testni ulashing yoki boshqa test yarating:"
                ),
                'ru': (
                    "😄 <b>Это ваш собственный тест!</b>\n\n"
                    "Проверять себя - это хорошо, но лучше отправьте тест друзьям - "
                    "узнайте, насколько хорошо они вас знают! 🎯\n\n"
                    "👇 Поделитесь тестом или создайте новый:"
                ),
                'en': (
                    "😄 <b>This is your own test!</b>\n\n"
                    "Testing yourself is good, but better send it to your friends - "
                    "find out how well they know you! 🎯\n\n"
                    "👇 Share the test or create a new one:"
                )
            }
            
            bot_username = context.bot.username
            share_link = f"https://t.me/{bot_username}?start=s_{test_id}"
            
            from share import SHARE_TRANSLATIONS
            share_translations = SHARE_TRANSLATIONS.get(lang, SHARE_TRANSLATIONS['en'])
            share_text_full = f"{share_translations['share_test_intro']}\n\n{share_link}\n\n{share_translations['share_test_text']}"
            share_text_encoded = urllib.parse.quote(share_text_full)
            
            keyboard = [
                [InlineKeyboardButton(
                    get_text(lang, 'share_test'),
                    url=f"https://t.me/share/url?url={share_link}&text={share_text_encoded}"
                )],
                [InlineKeyboardButton(
                    get_text(lang, 'back'),
                    callback_data='back_to_menu'
                )]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                own_test_messages.get(lang, own_test_messages['en']),
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
            return
        
        # Check if user has already taken this test
        existing_result = supabase.table('test_results').select('score').eq('test_id', test_id).eq('user_id', str(user_id)).execute()
        
        if existing_result.data:
            # User already took the test
            score = existing_result.data[0]['score']
            logger.info(f"TEST_ALREADY_TAKEN: User {user_id} already took test {test_id} | Score: {score}%")

            # Get test creator's name
            creator_result = supabase.table('friends_users').select('first_name, username').eq('telegram_id', test_owner_id).execute()
            creator_name = creator_result.data[0]['first_name'] if creator_result.data else "friend"

            # Determine friendship level
            if score >= 80:
                level_emoji = "🌟"
                level_text = {
                    'uz': "Eng yaqin do'st",
                    'ru': "Лучший друг",
                    'en': "Best Friend"
                }
            elif score >= 60:
                level_emoji = "💫"
                level_text = {
                    'uz': "Yaqin do'st",
                    'ru': "Близкий друг",
                    'en': "Close Friend"
                }
            elif score >= 40:
                level_emoji = "✨"
                level_text = {
                    'uz': "Do'st",
                    'ru': "Друг",
                    'en': "Friend"
                }
            else:
                level_emoji = "⭐"
                level_text = {
                    'uz': "Tanish",
                    'ru': "Знакомый",
                    'en': "Acquaintance"
                }

            already_taken_text = {
                'uz': (
                    f"✅ <b>Siz bu testni allaqachon topshirgansiz!</b>\n\n"
                    f"👤 <b>Test egasi:</b> {creator_name}\n"
                    f"📊 <b>Sizning natijangiz:</b> {score}%\n"
                    f"{level_emoji} <b>Do'stlik darajasi:</b> {level_text['uz']}\n\n"
                    f"💡 <i>O'zingizning testingizni yaratib, do'stlaringizni sinab ko'ring!</i>"
                ),
                'ru': (
                    f"✅ <b>Вы уже проходили этот тест!</b>\n\n"
                    f"👤 <b>Автор теста:</b> {creator_name}\n"
                    f"📊 <b>Ваш результат:</b> {score}%\n"
                    f"{level_emoji} <b>Уровень дружбы:</b> {level_text['ru']}\n\n"
                    f"💡 <i>Создайте свой тест и проверьте своих друзей!</i>"
                ),
                'en': (
                    f"✅ <b>You have already taken this test!</b>\n\n"
                    f"👤 <b>Test creator:</b> {creator_name}\n"
                    f"📊 <b>Your score:</b> {score}%\n"
                    f"{level_emoji} <b>Friendship level:</b> {level_text['en']}\n\n"
                    f"💡 <i>Create your own test and challenge your friends!</i>"
                )
            }
            
            keyboard = [
                [InlineKeyboardButton(
                    get_text(lang, 'create_your_test'),
                    callback_data='create_test'
                )],
                [InlineKeyboardButton(
                    get_text(lang, 'add_birthday_button'),
                    callback_data='add_birthday'
                )]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                already_taken_text.get(lang, already_taken_text['en']),
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
            return
        
        # Initialize test taking
        context.user_data['taking_test_id'] = test_id
        context.user_data['taking_test_answers'] = {}
        context.user_data['taking_test_question'] = 0
        
        # Show intro
        intro_text = get_text(lang, 'test_intro')
        await update.message.reply_text(intro_text, parse_mode=ParseMode.HTML)
        
        # Wait a bit before showing first question
        await asyncio.sleep(1)
        
        # Show first question
        await show_taking_test_question(update, context, lang)
        
    except Exception as e:
        logger.error(f"Error starting test: {e}")
        await update.message.reply_text("❌ Error loading test", parse_mode=ParseMode.HTML)
