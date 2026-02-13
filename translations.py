import random

def get_friendship_level_message(score: int, lang: str) -> tuple:
    """
    Get friendship level emoji, title, and a random encouraging message
    Returns: (emoji, level_title, message)
    """
    
    if score >= 80:
        # Best Friend Level (80-100%)
        messages = {
            'uz': [
                "🌟 Siz bir-biringizni juda yaxshi bilasiz! Bunday do'stlik kamdan-kam uchraydi. Davom eting va bir-biringizni qo'llab-quvvatlashda davom eting! 💝",
                "🌟 Ajoyib! Siz haqiqiy do'stsiz! Bir-biringiz haqida bu darajada bilim - bu noyob va qimmatli narsa. Sizning do'stligingiz ilhom beradi! ✨",
                "🌟 Mukammal natija! Siz bir-biringizning eng sirli tomonlarini ham bilasiz. Bunday do'stlik - hayotning eng katta ne'matilaridan biri! 🎯"
            ],
            'ru': [
                "🌟 Вы очень хорошо знаете друг друга! Такая дружба встречается редко. Продолжайте поддерживать друг друга! 💝",
                "🌟 Потрясающе! Вы настоящие друзья! Знать друг о друге так много - это редкость и ценность. Ваша дружба вдохновляет! ✨",
                "🌟 Идеальный результат! Вы знаете даже самые тайные стороны друг друга. Такая дружба - одно из величайших благ в жизни! 🎯"
            ],
            'en': [
                "🌟 You know each other incredibly well! Such friendship is rare. Keep supporting each other! 💝",
                "🌟 Amazing! You're true friends! Knowing this much about each other is rare and precious. Your friendship is inspiring! ✨",
                "🌟 Perfect result! You even know each other's deepest secrets. Such friendship is one of life's greatest blessings! 🎯"
            ]
        }
        level_titles = {
            'uz': '💎 Eng yaqin do\'st',
            'ru': '💎 Лучший друг',
            'en': '💎 Best Friend'
        }
        
    elif score >= 60:
        # Close Friend Level (60-79%)
        messages = {
            'uz': [
                "💫 Siz yaxshi do'stsiz! Bir-biringiz haqida ko'p narsani bilasiz. Birga ko'proq vaqt o'tkazing va yanada yaqinroq bo'ling! 🤗",
                "💫 Ajoyib natija! Sizning do'stligingiz mustahkam. Yana bir necha suhbat va siz bir-biringizni mukammal bilib olasiz! 🌈",
                "💫 Zo'r! Siz bir-biringizni yaxshi tushunasiz. Davom eting, sizning do'stligingiz o'sishda davom etmoqda! 🚀"
            ],
            'ru': [
                "💫 Вы хорошие друзья! Вы много знаете друг о друге. Проводите больше времени вместе и станьте ещё ближе! 🤗",
                "💫 Отличный результат! Ваша дружба крепкая. Ещё несколько бесед, и вы будете знать друг друга идеально! 🌈",
                "💫 Здорово! Вы хорошо понимаете друг друга. Продолжайте, ваша дружба продолжает расти! 🚀"
            ],
            'en': [
                "💫 You're good friends! You know a lot about each other. Spend more time together and become even closer! 🤗",
                "💫 Great result! Your friendship is strong. A few more conversations and you'll know each other perfectly! 🌈",
                "💫 Awesome! You understand each other well. Keep going, your friendship keeps growing! 🚀"
            ]
        }
        level_titles = {
            'uz': '💫 Yaqin do\'st',
            'ru': '💫 Близкий друг',
            'en': '💫 Close Friend'
        }
        
    elif score >= 40:
        # Friend Level (40-59%)
        messages = {
            'uz': [
                "🤝 Siz do'stsiz va bu ajoyib! Bir-biringiz haqida ko'proq bilib olish uchun ko'proq suhbatlashing. Har bir suhbat sizni yaqinlashtiradi! 💬",
                "🤝 Yaxshi boshlash! Sizda do'stlik uchun yaxshi asos bor. Ko'proq savol bering, hikoyalar almashing - va siz yanada yaqinroq bo'lasiz! 🌟",
                "🤝 Zo'r yo'ldasiz! Bir-biringiz haqida yanada ko'proq bilib olish uchun birga vaqt o'tkazing. Do'stlik - bu sayohat! 🎈"
            ],
            'ru': [
                "🤝 Вы друзья, и это прекрасно! Общайтесь больше, чтобы узнать друг друга лучше. Каждый разговор сближает вас! 💬",
                "🤝 Хорошее начало! У вас есть хорошая база для дружбы. Задавайте больше вопросов, делитесь историями - и вы станете ещё ближе! 🌟",
                "🤝 Вы на правильном пути! Проводите больше времени вместе, чтобы узнать друг о друге больше. Дружба - это путешествие! 🎈"
            ],
            'en': [
                "🤝 You're friends, and that's wonderful! Talk more to learn about each other better. Every conversation brings you closer! 💬",
                "🤝 Good start! You have a solid foundation for friendship. Ask more questions, share stories - and you'll become even closer! 🌟",
                "🤝 You're on the right track! Spend more time together to learn more about each other. Friendship is a journey! 🎈"
            ]
        }
        level_titles = {
            'uz': '🤝 Do\'st',
            'ru': '🤝 Друг',
            'en': '🤝 Friend'
        }
        
    else:
        # Acquaintance Level (0-39%)
        messages = {
            'uz': [
                "👋 Siz tanishsiz, lekin bu - do'stlikning boshlanishi! Bir-biringiz haqida ko'proq bilib olish uchun savollar bering. Har qanday ajoyib do'stlik tanishlikdan boshlanadi! 🌱",
                "👋 Siz hozirgina tanishdingiz! Bu juda yaxshi boshlang'ich. Ko'proq suhbatlashing, umumiy qiziqishlarni toping - va tez orada siz yaxshi do'stlar bo'lasiz! ✨",
                "👋 Tanishlik - bu do'stlik zinapoyasining birinchi pog'onasi! Birga vaqt o'tkazing, hikoyalar almashing, va siz bir-biringizni yaxshiroq bilib olasiz. Omad! 🍀"
            ],
            'ru': [
                "👋 Вы знакомы, но это только начало дружбы! Задавайте вопросы, чтобы узнать друг о друге больше. Любая великая дружба начинается со знакомства! 🌱",
                "👋 Вы только познакомились! Это отличное начало. Общайтесь больше, находите общие интересы - и скоро вы станете хорошими друзьями! ✨",
                "👋 Знакомство - это первая ступень лестницы дружбы! Проводите время вместе, делитесь историями, и вы узнаете друг друга лучше. Удачи! 🍀"
            ],
            'en': [
                "👋 You're acquaintances, but this is just the beginning of friendship! Ask questions to learn more about each other. Every great friendship starts with getting to know each other! 🌱",
                "👋 You've just met! This is a great start. Talk more, find common interests - and soon you'll become good friends! ✨",
                "👋 Acquaintance is the first step on the ladder of friendship! Spend time together, share stories, and you'll get to know each other better. Good luck! 🍀"
            ]
        }
        level_titles = {
            'uz': '👋 Tanish',
            'ru': '👋 Знакомый',
            'en': '👋 Acquaintance'
        }
    
    # Get random message for the language
    message = random.choice(messages.get(lang, messages['en']))
    level_title = level_titles.get(lang, level_titles['en'])
    
    return level_title, message



TRANSLATIONS = {
    'uz': {
        'welcome': (
            '👋 <b>Xush kelibsiz!</b>\n\n'
            'Bu bot sizga do‘stlaringiz bilan munosabatlarni yanada mustahkamlashga yordam beradi 💙\n\n'
            '🎂 Tug‘ilgan kunlarni unutmaslik\n'
            '✨ Qiziqarli do‘stlik testlari yaratish\n'
            '📊 Natijalarni ko‘rib borish\n\n'
            '<i>Keling, birgalikda boshlaylik! 🎉</i>'
        ),

        'main_menu': (
            '🏠 <b>Asosiy menyu</b>\n\n'
            'Bu yerdan barcha asosiy funksiyalarga kirishingiz mumkin 👇\n\n'
            '🎂 <b>Tug‘ilgan kunlar</b> — do‘stlaringiz va yaqinlaringiz muhim kunlarini saqlang\n'
            '✨ <b>Do‘stlik testlari</b> — o‘zingiz haqingizda test yarating yoki boshqalarnikini yeching\n'
            '📊 <b>Mening testlarim</b> — natijalar va statistika\n'
            '⚙️ <b>Sozlamalar</b> — til va boshqa qulayliklar\n'
            '⭐ <b>Premium</b> — cheklovlarsiz foydalanish\n\n'
            '<i>Davom etish uchun bo‘limni tanlang 🙂</i>'
        ),
        
        'add_birthday': '🎂 Tug\'ilgan kun',
        'my_birthdays': '📋 Mening ro\'yxatim',
        'create_test': '✨ Do\'stlik testi',
        'my_tests': '📊 Mening testlarim',
        'settings': '⚙️ Sozlamalar',
        'premium': '⭐ Premium',
        'back': '◀️ Orqaga',
        
        'birthday_prompt': '📝 <b>Tug\'ilgan kun qo\'shish</b>\n\nIsm va sanani yozing. Bir nechta odamni ham qo\'shishingiz mumkin!\n\n<b>Misol:</b>\n• Aziza 12.03\n• Akam 7-aprel\n• John 1999-07-04\n\n<i>💡 Maslahat: Har bir qatorga bitta odam ma\'lumotini kiriting</i>',
        
        'processing': '⏳ <i>Qayta ishlanmoqda...</i>',
        
        'birthday_parse_error': '❌ <b>Ma\'lumot noto\'g\'ri kiritildi</b>\n\nAfsus, tug\'ilgan kun ma\'lumotini tushunib bo\'lmadi. Iltimos, to\'g\'ri formatda qaytadan kiriting. /start\n\n<b>To\'g\'ri formatlar:</b>\n• Ism 12.03\n• Ism 12-mart\n• Ism 1999-07-04',
        
        'birthday_saved': '✅ <b>Muvaffaqiyatli saqlandi!</b>\n\n🎂 <b>{name}</b> — {day}.{month}\n\n<i>Tug\'ilgan kun yaqinlashganda sizga eslatma yuboraman!</i>',
        
        'birthday_list': '📋 <b>Tug\'ilgan kunlar ro\'yxati</b>\n\nSiz saqlagan barcha tug\'ilgan kunlar:',
        
        'no_birthdays': '📭 <b>Ro\'yxat hali bo\'sh</b>\n\nSiz hali hech qanday tug\'ilgan kun qo\'shmagansiz.\n\n<i>Birinchi tug\'ilgan kunni qo\'shish uchun pastdagi tugmani bosing! 👇</i>',
        
        'birthday_limit_reached': '⚠️ <b>Bepul rejadagi chegara tugadi</b>\n\nSiz maksimal <b>5 ta</b> tug\'ilgan kun saqlashingiz mumkin.\n\nKo\'proq qo\'shish va qo\'shimcha imkoniyatlardan foydalanish uchun <b>Premium</b>ga o\'ting! ⭐',
        
        'test_limit_reached': '⚠️ <b>Bepul rejadagi chegara tugadi</b>\n\nSiz maksimal <b>1 ta</b> test yaratishingiz mumkin.\n\nCheksiz testlar yaratish uchun <b>Premium</b>ga o\'ting! ⭐',
        
        'test_intro_creator': '🎯 <b>Ajoyib tanlov!</b>\n\nEndi siz haqingizda 15 ta savolga javob bering. Do\'stlaringiz bu savollar orqali sizni qanchalik yaxshi bilishlarini sinab ko\'rishadi.\n\n<i>Tayyor bo\'lsangiz, boshlaymiz! Har bir savol uchun o\'zingizga mos javobni tanlang.</i>',
        
        'test_intro': '🎮 <b>Do\'stlik testiga xush kelibsiz!</b>\n\nSizning do\'stingiz o\'zi haqida 15 ta savolga javob bergan. Endi navbat sizda — u haqida qanchalik ko\'p bilishingizni tekshirib ko\'ring!\n\n<i>Har bir to\'g\'ri javob uchun ball olasiz. Omad yor bo\'lsin! 🍀</i>',
        
        'question': 'Savol',
        'last_question': 'So\'nggi savol',
        
        'test_created': '🎊 <b>Testingiz tayyor!</b>\n\nAjoyib! Sizning do\'stlik testingiz muvaffaqiyatli yaratildi.\n\n📎 <b>Testni ulashish uchun:</b>\n<code>{link}</code>\n\n<i>💡 Ushbu havolani do\'stlaringizga yuboring. Ular testni topshirib, sizni qanchalik yaxshi bilishlarini bilib olishadi!</i>',
        
        'test_result_title': 'Natija',
        'test_result': '🎯 <b>Sizning natijangiz:</b> {score}%\n\n👤 <b>Do\'stlik darajasi:</b> {level}\n\n<i>Do\'stingiz siz haqingizda {score}% to\'g\'ri javob berdi!</i>',
        
        'level_best_friend': '💎 Eng yaqin do\'st',
        'level_close_friend': '💫 Yaqin do\'st',
        'level_friend': '🤝 Do\'st',
        'level_acquaintance': '👋 Tanish',
        
        'test_list': '📊 <b>Sizning testlaringiz</b>\n\nYaratilgan testlaringiz va statistika:',
        
        'no_tests': '📭 <b>Hali testlar yo\'q</b>\n\nSiz hali do\'stlik testi yaratmagansiz.\n\n<i>Birinchi testingizni yarating va do\'stlaringiz bilan ulashing! 🎯</i>',
        
        'settings_menu': '⚙️ <b>Sozlamalar</b>\n\nO\'zingizga qulay sozlamalarni tanlang:',
        
        'change_language': '🌍 Tilni o\'zgartirish',
        
        'premium_info': '⭐ <b>Premium obuna</b>\n\nPremium a\'zolar uchun maxsus imkoniyatlar:\n\n🎂 <b>Cheksiz tug\'ilgan kunlar</b> — istalgancha qo\'shing\n✨ <b>Cheksiz testlar</b> — yaratishda chegara yo\'q\n🎨 <b>Maxsus dizaynlar</b> — o\'ziga xos ko\'rinish\n📊 <b>Batafsil statistika</b> — har bir testning to\'liq tahlili\n\n<i>Premium rejalar tez orada!</i> 🚀',
        
        'error': '❌ <b>Xatolik yuz berdi</b>\n\nAfsus, nimadir noto\'g\'ri ketdi. Iltimos, bir ozdan so\'ng qaytadan urinib ko\'ring. /start \n\n<i>Agar muammo takrorlansa, yordam xizmatiga murojaat qiling.</i>',
        
        'cancelled': '❌ <b>Bekor qilindi</b>\n\n<i>Bosh menyuga qaytdingiz.</i>',
        
        'birthday_reminder': '🎉 <b>Bugun muhim kun!</b>\n\n🎂 <b>{name}</b> bugun tug\'ilgan kunini nishonlamoqda!\n\n<i>Unutmang va chiroyli tabrik yuboring! 🎁</i>',
        
        'generate_wish': '✨ Tabrik yaratish',
        'generating_wish': '⏳ <i>Maxsus tabrik tayyorlanmoqda...</i>',
        
        'create_your_test': '✨ O\'zimning testim',
        'add_birthday_button': '🎂 Tug\'ilgan kun qo\'shish',
        'share_bot': '📤 Testni Ulashish',
        'share_tests': '📤 Testni ulashish',
        'create_new_test': '➕ Yangi test',
        'test_number': 'Test #{num}',
        'link': 'Havola',
        'participants': 'Ishtirokchilar',
        'avg_score': 'O\'rtacha',
        'highest_score': 'Eng yuqori',
        'lowest_score': 'Eng past',
        'top_scorer': 'Eng yaxshi',
        'no_participants': 'Hali hech kim yechmagan',
        'test_completed_notification': '🎉 <b>Yangi natija!</b>\n\n<b>{user_name}</b> sizning testingizni yechdi.\n\n📊 <b>Natija:</b> {score}%',
        'your_test': 'Sizning testingiz',
        'share_test': '📤 Testni Ulashish',
"recreate_test": '🔄 Testni qayta yaratish',
'streaks': '🔥 Streaklar',
        'leaderboard': '🏆 Liderlar jadvali',










    },
    
    'ru': {
        'welcome': (
            '👋 <b>Добро пожаловать!</b>\n\n'
            'Этот бот поможет вам стать ближе к друзьям 💙\n\n'
            '🎂 Не забывать дни рождения\n'
            '✨ Создавать интересные тесты о дружбе\n'
            '📊 Смотреть результаты и статистику\n\n'
            '<i>Давайте начнем! 🎉</i>'
        ),

        'main_menu': (
            '🏠 <b>Главное меню</b>\n\n'
            'Здесь собраны все основные функции бота 👇\n\n'
            '🎂 <b>Дни рождения</b> — сохраняйте важные даты\n'
            '✨ <b>Тесты на дружбу</b> — создавайте и проходите тесты\n'
            '📊 <b>Мои тесты</b> — результаты и статистика\n'
            '⚙️ <b>Настройки</b> — язык и удобства\n'
            '⭐ <b>Premium</b> — без ограничений\n\n'
            '<i>Выберите нужный раздел 🙂</i>'
        ),
        
        'add_birthday': '🎂 День рождения',
        'my_birthdays': '📋 Мой список',
        'create_test': '✨ Тест на дружбу',
        'my_tests': '📊 Мои тесты',
        'settings': '⚙️ Настройки',
        'premium': '⭐ Premium',
        'back': '◀️ Назад',
        
        'birthday_prompt': '📝 <b>Добавить день рождения</b>\n\nНапишите имя и дату. Можете добавить сразу несколько человек!\n\n<b>Пример:</b>\n• Азиза 12.03\n• Брат 7-апреля\n• Джон 1999-07-04\n\n<i>💡 Совет: Вводите данные каждого человека с новой строки</i>',
        
        'processing': '⏳ <i>Обрабатывается...</i>',
        
        'birthday_parse_error': '❌ <b>Данные введены неверно</b>\n\nК сожалению, не удалось распознать информацию о дне рождения. Пожалуйста, введите в правильном формате.\n\n<b>Правильные форматы:</b>\n• Имя 12.03\n• Имя 12-марта\n• Имя 1999-07-04',
        
        'birthday_saved': '✅ <b>Успешно сохранено!</b>\n\n🎂 <b>{name}</b> — {day}.{month}\n\n<i>Я напомню вам, когда приблизится день рождения!</i>',
        
        'birthday_list': '📋 <b>Список дней рождения</b>\n\nВсе сохраненные вами дни рождения:',
        
        'no_birthdays': '📭 <b>Список пока пуст</b>\n\nВы еще не добавили ни одного дня рождения.\n\n<i>Нажмите кнопку ниже, чтобы добавить первый! 👇</i>',
        
        'birthday_limit_reached': '⚠️ <b>Лимит бесплатного плана исчерпан</b>\n\nВы можете сохранить максимум <b>5</b> дней рождения.\n\nЧтобы добавить больше и получить дополнительные возможности, перейдите на <b>Premium</b>! ⭐',
        
        'test_limit_reached': '⚠️ <b>Лимит бесплатного плана исчерпан</b>\n\nВы можете создать максимум <b>1</b> тест.\n\nДля неограниченного количества тестов перейдите на <b>Premium</b>! ⭐',
        
        'test_intro_creator': '🎯 <b>Отличный выбор!</b>\n\nТеперь ответьте на 15 вопросов о себе. Ваши друзья пройдут эти вопросы и узнают, насколько хорошо они вас знают.\n\n<i>Готовы? Начинаем! Для каждого вопроса выберите подходящий для вас ответ.</i>',
        
        'test_intro': '🎮 <b>Добро пожаловать в тест на дружбу!</b>\n\nВаш друг ответил на 15 вопросов о себе. Теперь ваша очередь — проверьте, насколько хорошо вы его знаете!\n\n<i>За каждый правильный ответ вы получите балл. Удачи! 🍀</i>',
        
        'question': 'Вопрос',
        'last_question': 'Последний вопрос',
        
        'test_created': '🎊 <b>Ваш тест готов!</b>\n\nОтлично! Ваш тест на дружбу успешно создан.\n\n📎 <b>Ссылка для друзей:</b>\n<code>{link}</code>\n\n<i>💡 Отправьте эту ссылку друзьям. Они пройдут тест и узнают, насколько хорошо вас знают!</i>',
        
        'test_result_title': 'Результат',
        'test_result': '🎯 <b>Ваш результат:</b> {score}%\n\n👤 <b>Уровень дружбы:</b> {level}\n\n<i>Ваш друг правильно ответил на {score}% вопросов о вас!</i>',
        
        'level_best_friend': '💎 Лучший друг',
        'level_close_friend': '💫 Близкий друг',
        'level_friend': '🤝 Друг',
        'level_acquaintance': '👋 Знакомый',
        
        'test_list': '📊 <b>Ваши тесты</b>\n\nСозданные вами тесты и статистика:',
        
        'no_tests': '📭 <b>Тестов пока нет</b>\n\nВы еще не создали ни одного теста на дружбу.\n\n<i>Создайте свой первый тест и поделитесь с друзьями! 🎯</i>',
        
        'settings_menu': '⚙️ <b>Настройки</b>\n\nВыберите удобные для вас настройки:',
        
        'change_language': '🌍 Изменить язык',
        
        'premium_info': '⭐ <b>Premium подписка</b>\n\nСпециальные возможности для Premium пользователей:\n\n🎂 <b>Неограниченные дни рождения</b> — добавляйте сколько угодно\n✨ <b>Неограниченные тесты</b> — создавайте без ограничений\n🎨 <b>Специальные дизайны</b> — уникальный вид\n📊 <b>Подробная статистика</b> — полный анализ каждого теста\n\n<i>Premium планы скоро!</i> 🚀',
        
        'error': '❌ <b>Произошла ошибка</b>\n\nК сожалению, что-то пошло не так. Пожалуйста, попробуйте снова через некоторое время.\n\n<i>Если проблема повторяется, обратитесь в службу поддержки.</i>',
        
        'cancelled': '❌ <b>Отменено</b>\n\n<i>Вы вернулись в главное меню.</i>',
        
        'birthday_reminder': '🎉 <b>Сегодня важный день!</b>\n\n🎂 <b>{name}</b> сегодня отмечает день рождения!\n\n<i>Не забудьте отправить красивое поздравление! 🎁</i>',
        
        'generate_wish': '✨ Создать поздравление',
        'generating_wish': '⏳ <i>Готовлю особое поздравление...</i>',
        
        'create_your_test': '✨ Мой тест',
        'add_birthday_button': '🎂 Добавить',
        'share_bot': '📤 Поделиться',
        'share_tests': '📤 Поделиться тестом',
        'create_new_test': '➕ Новый тест',
        'test_number': 'Тест #{num}',
        'link': 'Ссылка',
        'participants': 'Участники',
        'avg_score': 'Средний',
        'highest_score': 'Лучший',
        'lowest_score': 'Худший',
        'top_scorer': 'Лидер',
        'no_participants': 'Тест еще никто не прошел',
        'test_completed_notification': '🎉 <b>Новый результат!</b>\n\n<b>{user_name}</b> прошел ваш тест.\n\n📊 <b>Результат:</b> {score}%',
        'your_test': 'Ваш тест',
        'share_test': '📤 Поделиться',
"recreate_test": '🔄 Пересоздать тест',
'streaks': '🔥 Стрики',
        'leaderboard': '🏆 Таблица лидеров',






    },
    
    'en': {
        'welcome': (
            '👋 <b>Welcome!</b>\n\n'
            'This bot helps you stay closer to your friends 💙\n\n'
            '🎂 Never forget birthdays\n'
            '✨ Create fun friendship tests\n'
            '📊 Track results and stats\n\n'
            '<i>Let’s get started! 🎉</i>'
        ),

        'main_menu': (
            '🏠 <b>Main Menu</b>\n\n'
            'All main features are available here 👇\n\n'
            '🎂 <b>Birthdays</b> — save important dates\n'
            '✨ <b>Friendship Tests</b> — create or take tests\n'
            '📊 <b>My Tests</b> — view results and statistics\n'
            '⚙️ <b>Settings</b> — language and preferences\n'
            '⭐ <b>Premium</b> — unlock all features\n\n'
            '<i>Select a section to continue 🙂</i>'
        ),
        
        'add_birthday': '🎂 Birthday',
        'my_birthdays': '📋 My List',
        'create_test': '✨ Friendship Test',
        'my_tests': '📊 My Tests',
        'settings': '⚙️ Settings',
        'premium': '⭐ Premium',
        'back': '◀️ Back',
        
        'birthday_prompt': '📝 <b>Add a Birthday</b>\n\nWrite the name and date. You can add multiple people at once!\n\n<b>Example:</b>\n• Aziza 12.03\n• My brother April 7\n• John 1999-07-04\n\n<i>💡 Tip: Enter each person\'s details on a new line</i>',
        
        'processing': '⏳ <i>Processing...</i>',
        
        'birthday_parse_error': '❌ <b>Invalid data entered</b>\n\nSorry, couldn\'t recognize the birthday information. Please enter it in the correct format.\n\n<b>Correct formats:</b>\n• Name 12.03\n• Name 12-March\n• Name 1999-07-04',
        
        'birthday_saved': '✅ <b>Successfully saved!</b>\n\n🎂 <b>{name}</b> — {day}.{month}\n\n<i>I\'ll remind you when the birthday approaches!</i>',
        
        'birthday_list': '📋 <b>Birthday List</b>\n\nAll your saved birthdays:',
        
        'no_birthdays': '📭 <b>List is empty</b>\n\nYou haven\'t added any birthdays yet.\n\n<i>Click the button below to add your first one! 👇</i>',
        
        'birthday_limit_reached': '⚠️ <b>Free plan limit reached</b>\n\nYou can save up to <b>5</b> birthdays.\n\nTo add more and get additional features, upgrade to <b>Premium</b>! ⭐',
        
        'test_limit_reached': '⚠️ <b>Free plan limit reached</b>\n\nYou can create up to <b>1</b> test.\n\nFor unlimited tests, upgrade to <b>Premium</b>! ⭐',
        
        'test_intro_creator': '🎯 <b>Great choice!</b>\n\nNow answer 15 questions about yourself. Your friends will go through these questions to find out how well they know you.\n\n<i>Ready? Let\'s begin! For each question, choose the answer that fits you best.</i>',
        
        'test_intro': '🎮 <b>Welcome to the Friendship Test!</b>\n\nYour friend answered 15 questions about themselves. Now it\'s your turn — check how well you know them!\n\n<i>You\'ll get points for each correct answer. Good luck! 🍀</i>',
        
        'question': 'Question',
        'last_question': 'Last question',
        
        'test_created': '🎊 <b>Your test is ready!</b>\n\nAwesome! Your friendship test has been successfully created.\n\n📎 <b>Share link:</b>\n<code>{link}</code>\n\n<i>💡 Send this link to your friends. They\'ll take the test and find out how well they know you!</i>',
        
"recreate_test": '🔄 Recreate Test',


        
        'test_result_title': 'Result',
        'test_result': '🎯 <b>Your result:</b> {score}%\n\n👤 <b>Friendship level:</b> {level}\n\n<i>Your friend answered {score}% correctly about you!</i>',
        
        'level_best_friend': '💎 Best Friend',
        'level_close_friend': '💫 Close Friend',
        'level_friend': '🤝 Friend',
        'level_acquaintance': '👋 Acquaintance',
        
        'test_list': '📊 <b>Your Tests</b>\n\nYour created tests and statistics:',
        
        'no_tests': '📭 <b>No tests yet</b>\n\nYou haven\'t created any friendship tests yet.\n\n<i>Create your first test and share it with friends! 🎯</i>',
        
        'settings_menu': '⚙️ <b>Settings</b>\n\nChoose your preferred settings:',
        
        'change_language': '🌍 Change Language',
        
        'premium_info': '⭐ <b>Premium Subscription</b>\n\nSpecial features for Premium users:\n\n🎂 <b>Unlimited birthdays</b> — add as many as you want\n✨ <b>Unlimited tests</b> — create without restrictions\n🎨 <b>Special designs</b> — unique appearance\n📊 <b>Detailed statistics</b> — full analysis of each test\n\n<i>Premium plans coming soon!</i> 🚀',
        
        'error': '❌ <b>An error occurred</b>\n\nSorry, something went wrong. Please try again in a moment.\n\n<i>If the problem persists, contact support.</i>',
        
        'cancelled': '❌ <b>Cancelled</b>\n\n<i>You\'ve returned to the main menu.</i>',
        
        'birthday_reminder': '🎉 <b>Important day today!</b>\n\n🎂 <b>{name}</b> is celebrating their birthday today!\n\n<i>Don\'t forget to send a nice greeting! 🎁</i>',
        
        'generate_wish': '✨ Generate Wish',
        'generating_wish': '⏳ <i>Preparing a special wish...</i>',
        
        'create_your_test': '✨ My Test',
        'add_birthday_button': '🎂 Add',
        'share_bot': '📤 Share',
        'share_tests': '📤 Share Test',
        'create_new_test': '➕ New Test',
        'test_number': 'Test #{num}',
        'link': 'Link',
        'participants': 'Participants',
        'avg_score': 'Average',
        'highest_score': 'Highest',
        'lowest_score': 'Lowest',
        'top_scorer': 'Top',
        'no_participants': 'No one has taken this test yet',
        'test_completed_notification': '🎉 <b>New result!</b>\n\n<b>{user_name}</b> completed your test.\n\n📊 <b>Result:</b> {score}%',
        'your_test': 'Your test',
        'share_test': '📤 Share',
'streaks': '🔥 Streaks',
        'leaderboard': '🏆 Leaderboard',





















    }
}