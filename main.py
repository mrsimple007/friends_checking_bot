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
from config import supabase, model, TELEGRAM_BOT_TOKEN

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# Conversation states
CHOOSING_LANGUAGE = 0
ADDING_BIRTHDAY = 1
CREATING_TEST = 2
TAKING_TEST = 3

# Free tier limits
FREE_BIRTHDAY_LIMIT = 5
FREE_TEST_LIMIT = 1

# Load translations
from translations import TRANSLATIONS

# Helper Functions
def get_text(lang: str, key: str) -> str:
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

def save_user(telegram_id: int, username: str, language: str, is_premium: bool = False):
    """Save or update user in database"""
    try:
        user_data = {
            'telegram_id': str(telegram_id),
            'username': username,
            'language': language,
            'is_premium': is_premium,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Upsert user
        supabase.table('friends_users').upsert(user_data).execute()
        logger.info(f"User {telegram_id} saved with language {language}")
    except Exception as e:
        logger.error(f"Error saving user: {e}")

def parse_birthday_with_ai(text: str, lang: str) -> Optional[Dict]:
    """Parse birthday text using Gemini AI"""
    try:
        prompt = f"""
Extract the name and birthday from this text: "{text}"

Return ONLY a valid JSON object with this exact structure:
{{
    "name": "extracted name",
    "day": day_number,
    "month": month_number,
    "year": year_number_or_null
}}

Rules:
- day: 1-31
- month: 1-12
- year: full year (e.g., 1995) or null if not provided
- If you cannot extract valid information, return null

Examples:
Input: "Aziza 12.03"
Output: {{"name": "Aziza", "day": 12, "month": 3, "year": null}}

Input: "My brother born on April 7"
Output: {{"name": "My brother", "day": 7, "month": 4, "year": null}}

Input: "John 1999-07-04"
Output: {{"name": "John", "day": 4, "month": 7, "year": 1999}}

Now process the input text.
"""
        
        response = model.generate_content(prompt)
        result_text = response.text.strip()
        
        # Remove markdown code blocks if present
        result_text = result_text.replace('```json', '').replace('```', '').strip()
        
        # Parse JSON
        result = json.loads(result_text)
        
        # Validate
        if result and isinstance(result, dict):
            if 'name' in result and 'day' in result and 'month' in result:
                day = int(result['day'])
                month = int(result['month'])
                
                if 1 <= day <= 31 and 1 <= month <= 12:
                    return result
        
        return None
    except Exception as e:
        logger.error(f"Error parsing birthday with AI: {e}")
        return None

def generate_birthday_wish(name: str, lang: str) -> str:
    """Generate birthday wish using Gemini AI"""
    try:
        lang_names = {'uz': 'Uzbek', 'ru': 'Russian', 'en': 'English'}
        language_name = lang_names.get(lang, 'English')
        
        prompt = f"""
Generate a warm, heartfelt birthday wish for {name} in {language_name}.
Make it personal, positive, and sincere (2-3 sentences).
Do not use any markdown formatting or special characters.
"""
        
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Error generating birthday wish: {e}")
        return f"Happy Birthday, {name}! 🎉"

def get_user_birthday_count(user_id: int) -> int:
    """Get count of birthdays saved by user"""
    try:
        result = supabase.table('birthdays').select('id', count='exact').eq('user_id', str(user_id)).execute()
        return result.count if result.count else 0
    except Exception as e:
        logger.error(f"Error getting birthday count: {e}")
        return 0

def get_user_test_count(user_id: int) -> int:
    """Get count of tests created by user"""
    try:
        result = supabase.table('tests').select('id', count='exact').eq('user_id', str(user_id)).execute()
        return result.count if result.count else 0
    except Exception as e:
        logger.error(f"Error getting test count: {e}")
        return 0

def is_user_premium(user_id: int) -> bool:
    """Check if user is premium"""
    try:
        result = supabase.table('friends_users').select('is_premium').eq('telegram_id', str(user_id)).execute()
        if result.data:
            return result.data[0].get('is_premium', False)
    except Exception as e:
        logger.error(f"Error checking premium status: {e}")
    return False

# Bot Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    
    # Check if this is a test link
    if context.args and context.args[0].startswith('s_'):
        test_id = context.args[0][2:]
        # Start test taking flow
        await start_taking_test(update, context, test_id)
        return
    
    # Check if user exists
    try:
        result = supabase.table('friends_users').select('*').eq('telegram_id', str(user.id)).execute()
        
        if result.data:
            # User exists, show main menu
            lang = result.data[0]['language']
            await show_main_menu(update, context, lang)
        else:
            # New user, show language selection
            await show_language_selection(update, context)
    except Exception as e:
        logger.error(f"Error in start: {e}")
        await show_language_selection(update, context)

async def show_language_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show language selection keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("🇺🇿 O'zbek", callback_data='lang_uz'),
            InlineKeyboardButton("🇷🇺 Русский", callback_data='lang_ru'),
        ],
        [InlineKeyboardButton("🇬🇧 English", callback_data='lang_en')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = (
        "🌍 <b>Choose your language / Tilni tanlang / Выберите язык</b>\n\n"
        "This bot helps you remember birthdays and create fun friendship tests!"
    )
    
    if update.callback_query:
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

async def language_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle language selection"""
    query = update.callback_query
    await query.answer()
    
    lang = query.data.split('_')[1]
    user = update.effective_user
    
    # Save user with selected language
    save_user(user.id, user.username or user.first_name, lang)
    
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
            InlineKeyboardButton(get_text(lang, 'settings'), callback_data='settings'),
            InlineKeyboardButton(get_text(lang, 'premium'), callback_data='premium')
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

async def add_birthday_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start adding birthday"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    lang = get_user_language(user_id)
    
    # Check limits
    birthday_count = get_user_birthday_count(user_id)
    is_premium = is_user_premium(user_id)
    
    if not is_premium and birthday_count >= FREE_BIRTHDAY_LIMIT:
        limit_text = get_text(lang, 'birthday_limit_reached')
        await query.edit_message_text(limit_text, parse_mode=ParseMode.HTML)
        return ConversationHandler.END
    
    # Ask for birthday info
    prompt_text = get_text(lang, 'birthday_prompt')
    await query.edit_message_text(prompt_text, parse_mode=ParseMode.HTML)
    
    return ADDING_BIRTHDAY

async def process_birthday(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process birthday input"""
    user_id = update.effective_user.id
    lang = get_user_language(user_id)
    text = update.message.text
    
    # Parse with AI
    await update.message.reply_text(get_text(lang, 'processing'), parse_mode=ParseMode.HTML)
    
    parsed = parse_birthday_with_ai(text, lang)
    
    if not parsed:
        await update.message.reply_text(get_text(lang, 'birthday_parse_error'), parse_mode=ParseMode.HTML)
        return ADDING_BIRTHDAY
    
    # Save to database
    try:
        birthday_data = {
            'user_id': str(user_id),
            'name': parsed['name'],
            'day': parsed['day'],
            'month': parsed['month'],
            'year': parsed.get('year'),
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        supabase.table('birthdays').insert(birthday_data).execute()
        
        success_text = get_text(lang, 'birthday_saved').format(
            name=parsed['name'],
            day=parsed['day'],
            month=parsed['month']
        )
        await update.message.reply_text(success_text, parse_mode=ParseMode.HTML)
        
        # Show main menu
        await show_main_menu(update, context, lang)
        
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Error saving birthday: {e}")
        await update.message.reply_text(get_text(lang, 'error'), parse_mode=ParseMode.HTML)
        return ConversationHandler.END

async def my_birthdays(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's saved birthdays"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    lang = get_user_language(user_id)
    
    try:
        result = supabase.table('birthdays').select('*').eq('user_id', str(user_id)).execute()
        
        if not result.data:
            await query.edit_message_text(get_text(lang, 'no_birthdays'), parse_mode=ParseMode.HTML)
            return
        
        # Format birthday list
        text = get_text(lang, 'birthday_list') + "\n\n"
        for bd in result.data:
            year_str = f" ({bd['year']})" if bd.get('year') else ""
            text += f"🎂 <b>{bd['name']}</b>: {bd['day']}/{bd['month']}{year_str}\n"
        
        # Add back button
        keyboard = [[InlineKeyboardButton(get_text(lang, 'back'), callback_data='back_to_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Error fetching birthdays: {e}")
        await query.edit_message_text(get_text(lang, 'error'), parse_mode=ParseMode.HTML)

async def create_test_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start creating friendship test"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    lang = get_user_language(user_id)
    
    # Check limits
    test_count = get_user_test_count(user_id)
    is_premium = is_user_premium(user_id)
    
    if not is_premium and test_count >= FREE_TEST_LIMIT:
        limit_text = get_text(lang, 'test_limit_reached')
        await query.edit_message_text(limit_text, parse_mode=ParseMode.HTML)
        return ConversationHandler.END
    
    # Initialize test creation
    context.user_data['test_answers'] = {}
    context.user_data['current_question'] = 0
    
    # Show intro message
    intro_text = get_text(lang, 'test_intro_creator')
    await query.edit_message_text(intro_text, parse_mode=ParseMode.HTML)
    
    # Wait a bit, then show first question
    await asyncio.sleep(1)
    
    # Show first question
    await show_test_question(update, context, lang)
    
    return CREATING_TEST

async def show_test_question(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str):
    """Show test question"""
    from test_questions import get_questions
    
    questions = get_questions(lang)
    question_index = context.user_data['current_question']
    
    if question_index >= len(questions):
        # All questions answered, save test
        await save_test(update, context, lang)
        return ConversationHandler.END
    
    question = questions[question_index]
    
    # Create keyboard with options
    keyboard = []
    for i, option in enumerate(question['options']):
        keyboard.append([InlineKeyboardButton(option, callback_data=f'test_answer_{i}')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Add progress and formatting
    progress = f"<b>{get_text(lang, 'question')} {question_index + 1}/15</b>"
    
    if question_index == 0:
        # First question
        text = f"🎯 {progress}\n\n{question['text']}"
    elif question_index == 14:
        # Last question
        text = f"🏁 {progress} <i>({get_text(lang, 'last_question')})</i>\n\n{question['text']}"
    else:
        text = f"❓ {progress}\n\n{question['text']}"
    
    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        except:
            # If edit fails, send new message
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )

async def test_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle test answer"""
    query = update.callback_query
    await query.answer()
    
    lang = get_user_language(update.effective_user.id)
    answer_index = int(query.data.split('_')[2])
    
    # Save answer
    question_index = context.user_data['current_question']
    context.user_data['test_answers'][question_index] = answer_index
    
    # Move to next question
    context.user_data['current_question'] += 1
    
    await show_test_question(update, context, lang)

async def save_test(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str):
    """Save completed test"""
    user_id = update.effective_user.id
    test_id = str(uuid.uuid4())
    
    try:
        # Save test
        test_data = {
            'id': test_id,
            'user_id': str(user_id),
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        supabase.table('tests').insert(test_data).execute()
        
        # Save answers
        for question_index, answer_index in context.user_data['test_answers'].items():
            answer_data = {
                'test_id': test_id,
                'question_index': question_index,
                'answer_index': answer_index
            }
            supabase.table('test_answers_owner').insert(answer_data).execute()
        
        # Generate share link
        bot_username = context.bot.username
        share_link = f"https://t.me/{bot_username}?start=s_{test_id}"
        
        success_text = get_text(lang, 'test_created').format(link=share_link)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(success_text, parse_mode=ParseMode.HTML)
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=success_text,
                parse_mode=ParseMode.HTML
            )
        
    except Exception as e:
        logger.error(f"Error saving test: {e}")
        error_text = get_text(lang, 'error')
        if update.callback_query:
            await update.callback_query.edit_message_text(error_text, parse_mode=ParseMode.HTML)
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=error_text,
                parse_mode=ParseMode.HTML
            )

async def start_taking_test(update: Update, context: ContextTypes.DEFAULT_TYPE, test_id: str):
    """Start taking a friend's test"""
    user_id = update.effective_user.id
    
    # Check if test exists
    try:
        result = supabase.table('tests').select('*').eq('id', test_id).execute()
        
        if not result.data:
            await update.message.reply_text("❌ Test not found", parse_mode=ParseMode.HTML)
            return
        
        test = result.data[0]
        
        # Get user language
        lang = get_user_language(user_id)
        
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

async def show_taking_test_question(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str):
    """Show question for test taker"""
    from test_questions import get_questions
    
    questions = get_questions(lang)
    question_index = context.user_data['taking_test_question']
    
    if question_index >= len(questions):
        # All questions answered, calculate score
        await calculate_test_score(update, context, lang)
        return
    
    question = questions[question_index]
    
    # Create keyboard with options
    keyboard = []
    for i, option in enumerate(question['options']):
        keyboard.append([InlineKeyboardButton(option, callback_data=f'taking_answer_{i}')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Add progress
    progress = f"<b>{get_text(lang, 'question')} {question_index + 1}/15</b>"
    
    if question_index == 0:
        text = f"🎯 {progress}\n\n{question['text']}"
    elif question_index == 14:
        text = f"🏁 {progress} <i>({get_text(lang, 'last_question')})</i>\n\n{question['text']}"
    else:
        text = f"❓ {progress}\n\n{question['text']}"
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

async def taking_test_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle answer from test taker"""
    query = update.callback_query
    await query.answer()
    
    lang = get_user_language(update.effective_user.id)
    answer_index = int(query.data.split('_')[2])
    
    # Save answer
    question_index = context.user_data['taking_test_question']
    context.user_data['taking_test_answers'][question_index] = answer_index
    
    # Move to next question
    context.user_data['taking_test_question'] += 1
    
    await show_taking_test_question(update, context, lang)

async def calculate_test_score(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str):
    """Calculate and show test score"""
    user_id = update.effective_user.id
    test_id = context.user_data['taking_test_id']
    user_answers = context.user_data['taking_test_answers']
    
    try:
        # Get owner's answers
        result = supabase.table('test_answers_owner').select('*').eq('test_id', test_id).execute()
        owner_answers = {item['question_index']: item['answer_index'] for item in result.data}
        
        # Calculate score
        correct = sum(1 for q, a in user_answers.items() if owner_answers.get(q) == a)
        total = len(user_answers)
        percentage = int((correct / total) * 100)
        
        # Save result
        result_data = {
            'test_id': test_id,
            'user_id': str(user_id),
            'score': percentage,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        supabase.table('test_results').insert(result_data).execute()
        
        # Show result
        if percentage >= 80:
            level = get_text(lang, 'level_best_friend')
            emoji = "🌟"
        elif percentage >= 60:
            level = get_text(lang, 'level_close_friend')
            emoji = "💫"
        elif percentage >= 40:
            level = get_text(lang, 'level_friend')
            emoji = "✨"
        else:
            level = get_text(lang, 'level_acquaintance')
            emoji = "⭐"
        
        result_text = f"{emoji} <b>{get_text(lang, 'test_result_title')}</b>\n\n"
        result_text += get_text(lang, 'test_result').format(
            score=percentage,
            level=level
        )
        
        if update.callback_query:
            await update.callback_query.edit_message_text(result_text, parse_mode=ParseMode.HTML)
        else:
            await update.message.reply_text(result_text, parse_mode=ParseMode.HTML)
        
    except Exception as e:
        logger.error(f"Error calculating score: {e}")
        await update.message.reply_text(get_text(lang, 'error'), parse_mode=ParseMode.HTML)

async def my_tests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's tests and results"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    lang = get_user_language(user_id)
    
    try:
        # Get user's tests
        tests_result = supabase.table('tests').select('*').eq('user_id', str(user_id)).execute()
        
        if not tests_result.data:
            await query.edit_message_text(get_text(lang, 'no_tests'), parse_mode=ParseMode.HTML)
            return
        
        text = get_text(lang, 'test_list') + "\n\n"
        
        for test in tests_result.data:
            # Get results for this test
            results = supabase.table('test_results').select('*').eq('test_id', test['id']).execute()
            
            test_date = datetime.fromisoformat(test['created_at'].replace('Z', '+00:00'))
            text += f"📊 <b>Test created:</b> {test_date.strftime('%Y-%m-%d')}\n"
            text += f"   👥 <b>Participants:</b> {len(results.data)}\n"
            
            if results.data:
                avg_score = sum(r['score'] for r in results.data) / len(results.data)
                text += f"   📈 <b>Average score:</b> {avg_score:.0f}%\n"
            
            text += "\n"
        
        # Add back button
        keyboard = [[InlineKeyboardButton(get_text(lang, 'back'), callback_data='back_to_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        
    except Exception as e:
        logger.error(f"Error fetching tests: {e}")
        await query.edit_message_text(get_text(lang, 'error'), parse_mode=ParseMode.HTML)

async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show settings menu"""
    query = update.callback_query
    await query.answer()
    
    lang = get_user_language(update.effective_user.id)
    
    keyboard = [
        [InlineKeyboardButton(get_text(lang, 'change_language'), callback_data='change_language')],
        [InlineKeyboardButton(get_text(lang, 'back'), callback_data='back_to_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(get_text(lang, 'settings_menu'), reply_markup=reply_markup, parse_mode=ParseMode.HTML)

async def premium_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show premium information"""
    query = update.callback_query
    await query.answer()
    
    lang = get_user_language(update.effective_user.id)
    
    text = get_text(lang, 'premium_info')
    
    keyboard = [[InlineKeyboardButton(get_text(lang, 'back'), callback_data='back_to_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Go back to main menu"""
    query = update.callback_query
    await query.answer()
    
    lang = get_user_language(update.effective_user.id)
    await show_main_menu(update, context, lang)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel current operation"""
    lang = get_user_language(update.effective_user.id)
    await update.message.reply_text(get_text(lang, 'cancelled'), parse_mode=ParseMode.HTML)
    return ConversationHandler.END

# Birthday reminder job
async def check_birthdays(context: ContextTypes.DEFAULT_TYPE):
    """Check for birthdays and send reminders"""
    today = datetime.now(timezone.utc)
    
    try:
        # Get all birthdays for today
        result = supabase.table('birthdays').select('*').eq('day', today.day).eq('month', today.month).execute()
        
        for birthday in result.data:
            user_id = birthday['user_id']
            lang = get_user_language(int(user_id))
            
            # Send reminder
            reminder_text = get_text(lang, 'birthday_reminder').format(name=birthday['name'])
            
            # Add wish generation option
            keyboard = [[InlineKeyboardButton(get_text(lang, 'generate_wish'), callback_data=f"wish_{birthday['id']}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await context.bot.send_message(
                chat_id=int(user_id),
                text=reminder_text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
    except Exception as e:
        logger.error(f"Error checking birthdays: {e}")

async def generate_wish_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle wish generation request"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    lang = get_user_language(user_id)
    birthday_id = query.data.split('_')[1]
    
    # Get birthday info
    try:
        result = supabase.table('birthdays').select('*').eq('id', birthday_id).execute()
        if result.data:
            name = result.data[0]['name']
            
            await query.edit_message_text(get_text(lang, 'generating_wish'), parse_mode=ParseMode.HTML)
            
            # Generate wish
            wish = generate_birthday_wish(name, lang)
            
            await query.edit_message_text(f"✨ <i>{wish}</i>", parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Error generating wish: {e}")
        await query.edit_message_text(get_text(lang, 'error'), parse_mode=ParseMode.HTML)

# Main function
def main():
    """Start the bot"""
    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    
    # Birthday conversation handler
    birthday_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_birthday_start, pattern='^add_birthday$')],
        states={
            ADDING_BIRTHDAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_birthday)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    application.add_handler(birthday_conv)
    
    # Test creation conversation handler
    test_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(create_test_start, pattern='^create_test$')],
        states={
            CREATING_TEST: [CallbackQueryHandler(test_answer, pattern='^test_answer_')]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    application.add_handler(test_conv)
    
    # Callback query handlers
    application.add_handler(CallbackQueryHandler(language_selected, pattern='^lang_'))
    application.add_handler(CallbackQueryHandler(my_birthdays, pattern='^my_birthdays$'))
    application.add_handler(CallbackQueryHandler(my_tests, pattern='^my_tests$'))
    application.add_handler(CallbackQueryHandler(settings, pattern='^settings$'))
    application.add_handler(CallbackQueryHandler(premium_info, pattern='^premium$'))
    application.add_handler(CallbackQueryHandler(back_to_menu, pattern='^back_to_menu$'))
    application.add_handler(CallbackQueryHandler(show_language_selection, pattern='^change_language$'))
    application.add_handler(CallbackQueryHandler(generate_wish_handler, pattern='^wish_'))
    application.add_handler(CallbackQueryHandler(taking_test_answer, pattern='^taking_answer_'))
    
    # Set up daily birthday check (runs at 9 AM UTC)
    job_queue = application.job_queue
    job_queue.run_daily(check_birthdays, time=datetime.strptime("09:00", "%H:%M").time())
    
    # Start bot
    application.run_polling()

if __name__ == '__main__':
    main()