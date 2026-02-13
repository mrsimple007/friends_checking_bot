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
from start_handler import *
from friendship_streaks import show_streaks_menu, show_friend_selection
from leaderboard import show_leaderboard, leaderboard_command
from streak_actions import *

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

logging.getLogger("httpx").setLevel(logging.WARNING)



# Conversation states
CHOOSING_LANGUAGE = 0
ADDING_BIRTHDAY = 1
CREATING_TEST = 2
TAKING_TEST = 3

# Load translations
from translations import TRANSLATIONS, get_friendship_level_message

question0_img=os.environ.get("question0","")
question1_img=os.environ.get("question1","")
question2_img=os.environ.get("question2","")
question3_img=os.environ.get("question3","")
question4_img=os.environ.get("question4","")
question5_img=os.environ.get("question5","")
question6_img=os.environ.get("question6","")
question7_img=os.environ.get("question7","")
question8_img=os.environ.get("question8","")
question9_img=os.environ.get("question9","")
question10_img=os.environ.get("question10","")
question11_img=os.environ.get("question11","")
question12_img=os.environ.get("question12","")
question13_img=os.environ.get("question13","")
question14_img=os.environ.get("question14","")




def parse_birthday_with_ai(text: str, lang: str) -> Optional[List[Dict]]:
    """Parse birthday text using Gemini AI - can handle single or multiple birthdays"""
    try:
        prompt = f"""
Extract ALL names and birthdays from this text: "{text}"

Return ONLY a valid JSON array with this exact structure:
[
    {{
        "name": "extracted name",
        "day": day_number,
        "month": month_number,
        "year": year_number_or_null
    }}
]

Rules:
- day: 1-31
- month: 1-12
- year: full year (e.g., 1995) or null if not provided
- Month names in Uzbek/Russian/English should be converted to numbers:
  * yanvar/январь/january = 1
  * fevral/февраль/february = 2
  * mart/март/march = 3
  * april/апрель/april = 4
  * may/май/may = 5
  * iyun/июнь/june = 6
  * iyul/июль/july = 7
  * avgust/август/august = 8
  * sentabr/сентябрь/september = 9
  * oktabr/октябрь/october = 10
  * noyabr/ноябрь/november = 11
  * dekabr/декабрь/december = 12
- If the text contains multiple people, return an array with multiple objects
- If a line has a name but no date, skip it
- If you cannot extract valid information, return empty array []

Examples:
Input: "Aziza 12.03"
Output: [{{"name": "Aziza", "day": 12, "month": 3, "year": null}}]

Input: "Annam 15 yanvar\\nVohid ovam 21 mart"
Output: [{{"name": "Annam", "day": 15, "month": 1, "year": null}}, {{"name": "Vohid ovam", "day": 21, "month": 3, "year": null}}]

Now process the input text and extract ALL birthdays.
"""
        
        response = model.generate_content(prompt)
        result_text = response.text.strip()
        
        # Remove markdown code blocks if present
        result_text = result_text.replace('```json', '').replace('```', '').strip()
        
        # Parse JSON
        result = json.loads(result_text)
        
        # Validate
        if result and isinstance(result, list):
            validated_results = []
            for item in result:
                if isinstance(item, dict) and 'name' in item and 'day' in item and 'month' in item:
                    day = int(item['day'])
                    month = int(item['month'])
                    
                    if 1 <= day <= 31 and 1 <= month <= 12:
                        validated_results.append(item)
            
            return validated_results if validated_results else None
        
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


def format_display_name(row: dict) -> str:
    """Build: 'First Last (@username)' with fallbacks"""
    first = row.get('first_name') or ''
    last  = row.get('last_name')  or ''
    uname = row.get('username')   or ''

    full = f"{first} {last}".strip()

    if full and uname:
        return f"{full} (@{uname})"
    if full:
        return full
    if uname:
        return f"@{uname}"
    return f"User {row.get('telegram_id', '?')}"

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

@log_user_action("ADD_BIRTHDAY")
async def process_birthday(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process birthday input"""
    user_id = update.effective_user.id
    lang = get_user_language(user_id)
    text = update.message.text
    
    logger.info(f"BIRTHDAY_INPUT: User {user_id} submitted text: '{text[:50]}...'")
    
    await update.message.reply_text(get_text(lang, 'processing'), parse_mode=ParseMode.HTML)
    
    parsed = parse_birthday_with_ai(text, lang)
    
    if not parsed:
        logger.warning(f"BIRTHDAY_PARSE_FAILED: User {user_id} | Text: '{text[:50]}...'")
        await update.message.reply_text(get_text(lang, 'birthday_parse_error'), parse_mode=ParseMode.HTML)
        return ADDING_BIRTHDAY
    
    logger.info(f"BIRTHDAY_PARSED: User {user_id} | Count: {len(parsed)} | Names: {[b['name'] for b in parsed]}")
 
    # Check limits
    birthday_count = get_user_birthday_count(user_id)
    is_premium = is_user_premium(user_id)
    
    if not is_premium and (birthday_count + len(parsed)) > FREE_BIRTHDAY_LIMIT:
        remaining = FREE_BIRTHDAY_LIMIT - birthday_count
        if remaining > 0:
            await update.message.reply_text(
                f"⚠️ You can only add {remaining} more birthday(s) with the free plan.",
                parse_mode=ParseMode.HTML
            )
            return ADDING_BIRTHDAY
        else:
            await update.message.reply_text(get_text(lang, 'birthday_limit_reached'), parse_mode=ParseMode.HTML)
            return ConversationHandler.END
    
    # Save to database
    try:
        saved_count = 0
        for birthday in parsed:
            birthday_data = {
                'user_id': str(user_id),
                'name': birthday['name'],
                'day': birthday['day'],
                'month': birthday['month'],
                'year': birthday.get('year'),
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
            supabase.table('birthdays').insert(birthday_data).execute()
            saved_count += 1
        
        if saved_count == 1:
            success_text = get_text(lang, 'birthday_saved').format(
                name=parsed[0]['name'],
                day=parsed[0]['day'],
                month=parsed[0]['month']
            )
        else:
            success_text = f"✅ <b>Saqlandi!</b>\n\n🎂 {saved_count} ta tug'ilgan kun muvaffaqiyatli saqlandi!"
        
        await update.message.reply_text(success_text, parse_mode=ParseMode.HTML)
        logger.info(f"BIRTHDAY_SAVED: User {user_id} | Count: {saved_count} | Names: {[b['name'] for b in parsed]}")
        
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
            keyboard = [
                [InlineKeyboardButton(get_text(lang, 'add_birthday'), callback_data='add_birthday')],
                [InlineKeyboardButton(get_text(lang, 'back'), callback_data='back_to_menu')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                get_text(lang, 'no_birthdays'),
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
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
    
    # Clear any existing test creation data
    context.user_data.pop('test_answers', None)
    context.user_data.pop('current_question', None)
    context.user_data.pop('taking_test_id', None)
    context.user_data.pop('taking_test_answers', None)
    context.user_data.pop('taking_test_question', None)
    
    # Check limits
    test_count = get_user_test_count(user_id)
    is_premium = is_user_premium(user_id)
    
    if not is_premium and test_count >= FREE_TEST_LIMIT:
        # Still show existing test link so user can share it
        existing_test = supabase.table('tests').select('id').eq('user_id', str(user_id)).order('created_at', desc=True).limit(1).execute()

        limit_text = get_text(lang, 'test_limit_reached')

        keyboard = []

        if existing_test.data:
            bot_username = context.bot.username
            existing_link = f"https://t.me/{bot_username}?start=s_{existing_test.data[0]['id']}"

            from share import SHARE_TRANSLATIONS
            share_translations = SHARE_TRANSLATIONS.get(lang, SHARE_TRANSLATIONS['en'])
            share_text_full = f"{share_translations['share_test_intro']}\n\n{existing_link}\n\n{share_translations['share_test_text']}"
            share_text_encoded = urllib.parse.quote(share_text_full)

            limit_text += f"\n\n🔗 <b>{get_text(lang, 'link')}:</b>\n<code>{existing_link}</code>"

            keyboard.append([InlineKeyboardButton(
                get_text(lang, 'share_test'),
                url=f"https://t.me/share/url?url={existing_link}&text={share_text_encoded}"
            )])
            
            # Add recreate button
            keyboard.append([InlineKeyboardButton(
                get_text(lang, 'recreate_test'),
                callback_data='recreate_test'
            )])

        keyboard.append([InlineKeyboardButton(get_text(lang, 'premium'), callback_data='premium')])
        keyboard.append([InlineKeyboardButton(get_text(lang, 'back'), callback_data='back_to_menu')])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(limit_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
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

async def recreate_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete old test and start creating new one"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    lang = get_user_language(user_id)
    
    try:
        # Delete old test and its results
        old_test = supabase.table('tests').select('id').eq('user_id', str(user_id)).execute()
        if old_test.data:
            test_id = old_test.data[0]['id']
            # Delete test results first
            supabase.table('test_results').delete().eq('test_id', test_id).execute()
            # Delete test
            supabase.table('tests').delete().eq('id', test_id).execute()
        
        # Clear any existing test creation data
        context.user_data.pop('test_answers', None)
        context.user_data.pop('current_question', None)
        context.user_data.pop('taking_test_id', None)
        context.user_data.pop('taking_test_answers', None)
        context.user_data.pop('taking_test_question', None)
        
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
        
    except Exception as e:
        logger.error(f"Error recreating test: {e}")
        await query.edit_message_text(get_text(lang, 'error'), parse_mode=ParseMode.HTML)


async def show_test_question(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str):
    """Show test question"""
    from test_questions import get_questions
    
    questions = get_questions(lang)
    question_index = context.user_data['current_question']
    
    # Safety check - should never exceed 14 (0-14 = 15 questions)
    if question_index >= 15 or question_index >= len(questions):
        # All questions answered, save test
        await save_test(update, context, lang)
        return ConversationHandler.END
    
    question = questions[question_index]
    
    # Get the question image URL
    question_images = [
        question0_img, question1_img, question2_img, question3_img, question4_img,
        question5_img, question6_img, question7_img, question8_img, question9_img,
        question10_img, question11_img, question12_img, question13_img, question14_img
    ]
    
    # Create keyboard with options - 2 buttons per row
    keyboard = []
    for i in range(0, len(question['options']), 2):
        row = []
        row.append(InlineKeyboardButton(question['options'][i], callback_data=f'test_answer_{i}'))
        if i + 1 < len(question['options']):
            row.append(InlineKeyboardButton(question['options'][i + 1], callback_data=f'test_answer_{i + 1}'))
        keyboard.append(row)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Add progress and formatting
    progress = f"<b>{get_text(lang, 'question')} {question_index + 1}/15</b>"
    
    if question_index == 0:
        text = f"🎯 {progress}\n\n{question['text']}"
    elif question_index == 14:
        text = f"🏁 {progress} <i>({get_text(lang, 'last_question')})</i>\n\n{question['text']}"
    else:
        text = f"❓ {progress}\n\n{question['text']}"
    
    # Send photo with caption if image exists and is valid
    if question_index < len(question_images) and question_images[question_index] and question_images[question_index].strip():
        try:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=question_images[question_index],
                caption=text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
            return
        except Exception as e:
            logger.error(f"Error sending photo for question {question_index}: {e}")
            # Fall through to text message
    
    # Send as text message (fallback or no image)
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
    user_id = update.effective_user.id
    lang = get_user_language(update.effective_user.id)
    answer_index = int(query.data.split('_')[2])
    
    # Save answer
    question_index = context.user_data['current_question']
    context.user_data['test_answers'][question_index] = answer_index
    
    logger.info(f"Creating test - Question {question_index} answered with option {answer_index} by user {user_id}. Total answers so far: {len(context.user_data['test_answers'])}")
    
    # Move to next question
    context.user_data['current_question'] += 1
    
    # Check if we've completed all 15 questions (0-14)
    if len(context.user_data['test_answers']) >= 15:
        await save_test(update, context, lang)
        return ConversationHandler.END
    
    # Continue showing questions
    await show_test_question(update, context, lang)
    
    return CREATING_TEST

async def save_test(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str):
    """Save completed test with answers in JSONB format"""
    user_id = update.effective_user.id
    test_id = str(uuid.uuid4())
    
    try:
        # Validate we have exactly 15 answers (0-14)
        if len(context.user_data['test_answers']) != 15:
            logger.error(f"Invalid number of answers: {len(context.user_data['test_answers'])}")
            logger.error(f"Answers received: {context.user_data['test_answers']}")
            error_text = get_text(lang, 'error')
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=error_text + f"\n\nDebug: Only {len(context.user_data['test_answers'])} answers received.",
                parse_mode=ParseMode.HTML
            )
            return
        
        # Convert answers dict to proper format for JSONB
        answers_jsonb = {}
        for i in range(15):
            if i in context.user_data['test_answers']:
                answer_value = context.user_data['test_answers'][i]
                # Validate answer is 0-3
                if answer_value < 0 or answer_value > 6:
                    logger.error(f"Invalid answer_index at question {i}: {answer_value}")
                    continue
                answers_jsonb[str(i)] = answer_value
            else:
                logger.error(f"Missing answer for question {i}")
                error_text = get_text(lang, 'error')
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=error_text + f"\n\nDebug: Missing answer for question {i+1}.",
                    parse_mode=ParseMode.HTML
                )
                return
        
        # Save test with answers as JSONB
        test_data = {
            'id': test_id,
            'user_id': str(user_id),
            'answers': answers_jsonb,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"Saving test {test_id} with answers: {answers_jsonb}")
        supabase.table('tests').insert(test_data).execute()
        
        # Generate share link
        bot_username = context.bot.username
        share_link = f"https://t.me/{bot_username}?start=s_{test_id}"
        
        # Get share text from translations
        from share import SHARE_TRANSLATIONS
        translations = SHARE_TRANSLATIONS.get(lang, SHARE_TRANSLATIONS['en'])
        
        share_text_plain = translations['share_test_text']
        share_text_intro = translations['share_test_intro']
        share_text_full = f"{share_text_intro}\n\n{share_link}\n\n{share_text_plain}"
        share_text_encoded = urllib.parse.quote(share_text_full)
        
        success_text = get_text(lang, 'test_created').format(link=share_link)
        
        # Add share and back buttons
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
        
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=success_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
        
    except Exception as e:
        logger.error(f"Error saving test: {e}")
        import traceback
        logger.error(traceback.format_exc())
        error_text = get_text(lang, 'error')
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=error_text,
            parse_mode=ParseMode.HTML
        )

async def show_taking_test_question(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str):
    """Show question for test taker"""
    from test_questions import get_questions
    
    questions = get_questions(lang)
    question_index = context.user_data['taking_test_question']
    
    # FIXED: Strict check for 15 questions (0-14)
    if question_index >= 15:
        # All questions answered, calculate score
        await calculate_test_score(update, context, lang)
        return
    
    question = questions[question_index]
    
    # Get the question image URL
    question_images = [
        question0_img, question1_img, question2_img, question3_img, question4_img,
        question5_img, question6_img, question7_img, question8_img, question9_img,
        question10_img, question11_img, question12_img, question13_img, question14_img
    ]
    
    # Create keyboard with options - 2 buttons per row
    keyboard = []
    for i in range(0, len(question['options']), 2):
        row = []
        row.append(InlineKeyboardButton(question['options'][i], callback_data=f'taking_answer_{i}'))
        if i + 1 < len(question['options']):
            row.append(InlineKeyboardButton(question['options'][i + 1], callback_data=f'taking_answer_{i + 1}'))
        keyboard.append(row)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Add progress
    progress = f"<b>{get_text(lang, 'question')} {question_index + 1}/15</b>"
    
    if question_index == 0:
        text = f"🎯 {progress}\n\n{question['text']}"
    elif question_index == 14:
        text = f"🏁 {progress} <i>({get_text(lang, 'last_question')})</i>\n\n{question['text']}"
    else:
        text = f"❓ {progress}\n\n{question['text']}"
    
    # Send photo with caption if image exists
    if question_index < len(question_images) and question_images[question_index]:
        try:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=question_images[question_index],
                caption=text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Error sending photo: {e}")
            # Fallback to text message
            if update.callback_query:
                await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
            else:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.HTML
                )
    else:
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )


async def taking_test_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle answer from test taker"""
    query = update.callback_query
    await query.answer()
    
    lang = get_user_language(update.effective_user.id)
    answer_index = int(query.data.split('_')[2])
    user_id = update.effective_user.id
    
    # Save answer
    question_index = context.user_data['taking_test_question']
    context.user_data['taking_test_answers'][question_index] = answer_index
    
    logger.info(f"Taking test - Question {question_index} answered with option {answer_index} by user {user_id}. Total answers: {len(context.user_data['taking_test_answers'])}")
    
    # Move to next question
    context.user_data['taking_test_question'] += 1
    
    # FIXED: Check if we've completed exactly 15 questions (0-14)
    if context.user_data['taking_test_question'] >= 15:
        await calculate_test_score(update, context, lang)
        return
    
    await show_taking_test_question(update, context, lang)

async def calculate_test_score(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str):
    """Calculate and show test score with action buttons"""
    user_id = update.effective_user.id
    test_id = context.user_data['taking_test_id']
    user_answers = context.user_data['taking_test_answers']
    
    try:
        # FIXED: Validate exactly 15 answers before proceeding
        if len(user_answers) != 15:
            logger.error(f"Invalid answer count: {len(user_answers)}, expected 15")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=get_text(lang, 'error') + f"\n\nDebug: Invalid answer count ({len(user_answers)}/15)",
                parse_mode=ParseMode.HTML
            )
            return
        
        # Get owner's answers from JSONB column
        result = supabase.table('tests').select('answers, user_id').eq('id', test_id).execute()
        
        if not result.data or not result.data[0].get('answers'):
            logger.error("No answers found in test")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=get_text(lang, 'error'),
                parse_mode=ParseMode.HTML
            )
            return
        
        # Parse JSONB answers
        owner_answers_json = result.data[0]['answers']
        test_owner_id = result.data[0]['user_id']
        
        if isinstance(owner_answers_json, str):
            owner_answers_dict = json.loads(owner_answers_json)
        else:
            owner_answers_dict = owner_answers_json
        
        # Convert string keys to int for comparison
        owner_answers = {int(k): v for k, v in owner_answers_dict.items()}
        
        logger.info(f"Owner answers: {owner_answers}")
        logger.info(f"User answers: {user_answers}")
        
        # Calculate score - only use questions 0-14
        correct = sum(1 for q in range(15) if owner_answers.get(q) == user_answers.get(q))
        total = 15
        percentage = int((correct / total) * 100)
        
        logger.info(f"Score: {correct}/{total} = {percentage}%")
        logger.info(f"TEST_COMPLETED: User {user_id} | Test {test_id} | Score: {percentage}% ({correct}/{total})")
        
        # FIXED: Save result with upsert to prevent duplicate key error
        result_data = {
            'test_id': test_id,
            'user_id': str(user_id),
            'score': percentage,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        supabase.table('test_results').upsert(result_data).execute()
        
        # NEW: Create or update streak between test taker and test owner
        from friendship_streaks import get_or_create_streak, update_streak
        from streak_actions import log_interaction
        
        try:
            streak = get_or_create_streak(user_id, int(test_owner_id))
            if streak:
                streak_days = update_streak(streak['id'], user_id, int(test_owner_id))
                log_interaction(streak['id'], user_id, int(test_owner_id), 'test_completed', {
                    'test_id': test_id,
                    'score': percentage
                })
                logger.info(f"STREAK_UPDATED_ON_TEST: User {user_id} with owner {test_owner_id} | Streak: {streak_days} days")
        except Exception as e:
            logger.error(f"Error updating streak after test: {e}")
        
        # Notify test owner about the result
        try:
            owner_lang = get_user_language(int(test_owner_id))
            owner_notification = get_text(owner_lang, 'test_completed_notification').format(
                user_name=update.effective_user.first_name or "Someone",
                score=percentage
            )
            await context.bot.send_message(
                chat_id=int(test_owner_id),
                text=owner_notification,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Error notifying test owner: {e}")
        
        # Get friendship level and message
        level_title, level_message = get_friendship_level_message(percentage, lang)
        
        # Build result text with proper formatting
        result_labels = {
            'uz': {'score': 'Sizning natijangiz', 'level': 'Do\'stlik darajasi'},
            'ru': {'score': 'Ваш результат', 'level': 'Уровень дружбы'},
            'en': {'score': 'Your result', 'level': 'Friendship level'}
        }
        labels = result_labels.get(lang, result_labels['en'])
        
        result_text = (
            f"🎯 <b>{get_text(lang, 'test_result_title')}</b>\n\n"
            f"📊 <b>{labels['score']}:</b> {percentage}%\n"
            f"👤 <b>{labels['level']}:</b> {level_title}\n\n"
            f"💭 <i>{level_message}</i>"
        )
        
        # Add action buttons
        keyboard = [
            [
                InlineKeyboardButton(
                    get_text(lang, 'create_your_test'),
                    callback_data='create_test'
                )
            ],
            [
                InlineKeyboardButton(
                    get_text(lang, 'add_birthday_button'),
                    callback_data='add_birthday'
                )
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Always send as new message
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=result_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
        
    except Exception as e:
        logger.error(f"Error calculating score: {e}")
        import traceback
        logger.error(traceback.format_exc())
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=get_text(lang, 'error'),
            parse_mode=ParseMode.HTML
        )

async def my_tests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's tests with share and create buttons"""
    # Handle both callback query and regular message
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        user_id = update.effective_user.id
        lang = get_user_language(user_id)
    else:
        # Called from command
        user_id = update.effective_user.id
        lang = get_user_language(user_id)
        query = None
    
    try:
        # Get user's tests (limit to 1)
        tests_result = supabase.table('tests').select('*').eq('user_id', str(user_id)).order('created_at', desc=True).limit(1).execute()
        
        if not tests_result.data:
            keyboard = [
                [InlineKeyboardButton(get_text(lang, 'create_test'), callback_data='create_test')],
                [InlineKeyboardButton(get_text(lang, 'back'), callback_data='back_to_menu')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            no_tests_text = get_text(lang, 'no_tests')
            
            if query:
                try:
                    await query.edit_message_text(no_tests_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
                except Exception as e:
                    if "message is not modified" not in str(e).lower():
                        raise
            else:
                await update.message.reply_text(no_tests_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
            return
        
        test = tests_result.data[0]
        bot_username = context.bot.username
        share_link = f"https://t.me/{bot_username}?start=s_{test['id']}"
        
        # Get share text from translations
        from share import SHARE_TRANSLATIONS
        translations = SHARE_TRANSLATIONS.get(lang, SHARE_TRANSLATIONS['en'])
        
        share_text_plain = translations['share_test_text']
        share_text_intro = translations['share_test_intro']
        share_text_full = f"{share_text_intro}\n\n{share_link}\n\n{share_text_plain}"
        share_text_encoded = urllib.parse.quote(share_text_full)
        
        text = get_text(lang, 'test_list') + "\n\n"
        
        # Get results ordered by score descending, then created_at ascending
        results = supabase.table('test_results').select('score, user_id, created_at').eq('test_id', test['id']).order('score', desc=True).order('created_at', desc=False).execute()

        # Format test date
        test_date = datetime.fromisoformat(test['created_at'].replace('Z', '+00:00'))
        date_str = test_date.strftime('%d.%m.%Y')

        # Build test info
        total_participants = len(results.data)
        text += f"📝 <b>{get_text(lang, 'your_test')}</b> ({date_str})\n"
        text += f"🔗 <b>{get_text(lang, 'link')}:</b> <code>{share_link}</code>\n"
        text += f"👥 <b>{get_text(lang, 'participants')}:</b> {total_participants}\n\n"

        if results.data:
            scores = [r['score'] for r in results.data]
            avg_score = sum(scores) / len(scores)
            max_score = max(scores)
            min_score = min(scores)

            text += f"📊 <b>{get_text(lang, 'avg_score')}:</b> {avg_score:.0f}%\n"
            text += f"🏆 <b>{get_text(lang, 'highest_score')}:</b> {max_score}%\n"
            text += f"📉 <b>{get_text(lang, 'lowest_score')}:</b> {min_score}%\n\n"

            # Limit to top 30 participants
            display_limit = 30
            displayed_results = results.data[:display_limit]
            
            text += f"<b>👤 {get_text(lang, 'participants')}"
            if total_participants > display_limit:
                text += f" (Top {display_limit})"
            text += ":</b>\n"
            
            for rank, r in enumerate(displayed_results, start=1):
                try:
                    user_row = supabase.table('friends_users').select('first_name, last_name, username, telegram_id').eq('telegram_id', r['user_id']).execute()
                    display_name = format_display_name(user_row.data[0]) if user_row.data else f"User {r['user_id']}"
                except Exception:
                    display_name = f"User {r['user_id']}"
                text += f"  {rank}. <b>{display_name}</b> — {r['score']}%\n"
            
            if total_participants > display_limit:
                text += f"\n<i>... and {total_participants - display_limit} more</i>\n"
        else:
            text += f"<i>{get_text(lang, 'no_participants')}</i>\n"
        
        # Add share button
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
        
        if query:
            try:
                await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
            except Exception as e:
                # Ignore "message is not modified" error
                if "message is not modified" not in str(e).lower():
                    raise
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        
    except Exception as e:
        # Don't log "message is not modified" errors
        if "message is not modified" not in str(e).lower():
            logger.error(f"Error fetching tests: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        error_text = get_text(lang, 'error')
        
        if query:
            try:
                await query.edit_message_text(error_text, parse_mode=ParseMode.HTML)
            except Exception:
                pass  # Silently ignore if we can't edit
        else:
            await update.message.reply_text(error_text, parse_mode=ParseMode.HTML)

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
            
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
            
            # Generate wish
            wish = generate_birthday_wish(name, lang)
            
            await query.edit_message_text(f"✨ <i>{wish}</i>", parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Error generating wish: {e}")
        await query.edit_message_text(get_text(lang, 'error'), parse_mode=ParseMode.HTML)


async def my_test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /my_test command"""
    await my_tests(update, context)

async def premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /premium command"""
    user_id = update.effective_user.id
    lang = get_user_language(user_id)
    
    # Check if user is already premium
    try:
        result = supabase.table('friends_users').select('is_premium, premium_until').eq('telegram_id', str(user_id)).execute()
        if result.data and result.data[0].get('is_premium'):
            from balance import PREMIUM_TRANSLATIONS
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
                await update.message.reply_text(
                    text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode=ParseMode.HTML
                )
                return
    except Exception as e:
        logger.error(f"Error checking premium status: {e}")
    
    # Show premium plans
    from balance import PREMIUM_TRANSLATIONS
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
    
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )



def main():
    """Start the bot"""
    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("my_test", my_test_command))
    application.add_handler(CommandHandler("premium", premium_command))
   # Commands
    application.add_handler(CommandHandler("streaks", lambda u, c: show_streaks_menu(u, c)))
    application.add_handler(CommandHandler("leaderboard", leaderboard_command))


    # Daily question conversation
    daily_q_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_daily_question_answer_prompt, pattern='^daily_q_answer_')],
        states={
            ANSWERING_DAILY_Q: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_daily_question_answer_text)]
        },
        fallbacks=[CommandHandler('cancel', cancel), CommandHandler('start', start)],
        allow_reentry=True,
        per_message=False
    )
    application.add_handler(daily_q_conv)
    
    # Remember friend conversation
    remember_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_remember_friend_start, pattern='^streak_friend_remember_')],
        states={
            REMEMBERING_FRIEND: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_remember_friend_answer)]
        },
        fallbacks=[CommandHandler('cancel', cancel), CommandHandler('start', start)],
        allow_reentry=True,
        per_message=False
    )
    application.add_handler(remember_conv)

    # Conversation handlers
    application.add_handler(daily_q_conv)
    application.add_handler(remember_conv)


    # Birthday conversation handler
    birthday_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_birthday_start, pattern='^add_birthday$')],
        states={
            ADDING_BIRTHDAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_birthday)]
        },
        fallbacks=[CommandHandler('cancel', cancel), CommandHandler('start', start)],
        allow_reentry=True,
        per_message=False
    )
    application.add_handler(birthday_conv)
    
    # Test creation conversation handler
    test_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(create_test_start, pattern='^create_test$')],
        states={
            CREATING_TEST: [CallbackQueryHandler(test_answer, pattern='^test_answer_')]
        },
        fallbacks=[CommandHandler('cancel', cancel), CommandHandler('start', start)],
        allow_reentry=True,
        per_message=False
    )
    application.add_handler(test_conv)
    
    # Callback query handlers
    application.add_handler(CallbackQueryHandler(language_selected, pattern='^lang_'))
    application.add_handler(CallbackQueryHandler(my_birthdays, pattern='^my_birthdays$'))
    application.add_handler(CallbackQueryHandler(my_tests, pattern='^my_tests$'))
    application.add_handler(CallbackQueryHandler(settings, pattern='^settings$'))
    application.add_handler(CallbackQueryHandler(premium_info_handler, pattern='^premium$'))
    application.add_handler(CallbackQueryHandler(back_to_menu, pattern='^back_to_menu$'))
    application.add_handler(CallbackQueryHandler(show_language_selection, pattern='^change_language$'))
    application.add_handler(CallbackQueryHandler(generate_wish_handler, pattern='^wish_'))
    application.add_handler(CallbackQueryHandler(taking_test_answer, pattern='^taking_answer_'))
    application.add_handler(CallbackQueryHandler(approve_premium_payment, pattern='^approve_premium_'))
    application.add_handler(CallbackQueryHandler(decline_premium_payment, pattern='^decline_premium_'))
    # NEW: Share and Premium handlers
    application.add_handler(CallbackQueryHandler(share_main, pattern='^share_bot$'))
    application.add_handler(CallbackQueryHandler(subscribe_callback, pattern='^subscribe_'))
    application.add_handler(CallbackQueryHandler(recreate_test, pattern='^recreate_test$'))
    # Streaks menu and actions
    application.add_handler(CallbackQueryHandler(show_streaks_menu, pattern='^streaks_menu$'))
    application.add_handler(CallbackQueryHandler(show_leaderboard, pattern='^streak_leaderboard$'))
    
    # Friend selection for different actions
    application.add_handler(CallbackQueryHandler(handle_ping_friend, pattern='^streak_ping$'))
    application.add_handler(CallbackQueryHandler(lambda u, c: show_friend_selection(u, c, 'daily_q'), pattern='^streak_daily_q$'))
    application.add_handler(CallbackQueryHandler(lambda u, c: show_friend_selection(u, c, 'remember'), pattern='^streak_remember$'))
    application.add_handler(CallbackQueryHandler(lambda u, c: show_friend_selection(u, c, 'guess'), pattern='^streak_guess$'))
    application.add_handler(CallbackQueryHandler(lambda u, c: show_friend_selection(u, c, 'quiz'), pattern='^streak_quiz$'))
    application.add_handler(CallbackQueryHandler(lambda u, c: show_friend_selection(u, c, 'weekly'), pattern='^streak_weekly$'))
    
    # Specific streak actions

    application.add_handler(CallbackQueryHandler(handle_ping_friend, pattern='^streak_friend_ping_'))
    application.add_handler(CallbackQueryHandler(handle_daily_question_start, pattern='^streak_friend_daily_q_'))
    application.add_handler(CallbackQueryHandler(handle_daily_question_send, pattern='^daily_q_send_'))
    application.add_handler(CallbackQueryHandler(handle_guess_game, pattern='^streak_friend_guess_'))
    application.add_handler(CallbackQueryHandler(handle_guess_answer, pattern='^guess_answer_'))
    application.add_handler(CallbackQueryHandler(handle_weekly_checkin, pattern='^streak_friend_weekly_'))
    application.add_handler(CallbackQueryHandler(handle_weekly_yes, pattern='^weekly_yes_'))
    application.add_handler(CallbackQueryHandler(handle_weekly_no, pattern='^weekly_no_'))
    application.add_handler(CallbackQueryHandler(handle_quiz_retake, pattern='^streak_friend_quiz_'))

    # Set up daily birthday check (runs at 9 AM UTC)
    job_queue = application.job_queue
    job_queue.run_daily(check_birthdays, time=datetime.strptime("09:00", "%H:%M").time())
    
    # Start bot
    application.run_polling()

if __name__ == '__main__':
    main()
