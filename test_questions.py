"""
Friendship test questions in Uzbek, Russian, and English
"""

def get_questions(lang: str):
    """Get 15 test questions in the specified language"""
    
    questions = {
        'uz': [
            {
                'text': "Sevimli rangim qaysi?",
                'options': ["🔴 Qizil", "🔵 Ko'k", "🟢 Yashil", "🟡 Sariq"]
            },
            {
                'text': "Mening bo'yim taxminan qancha?",
                'options': ["📏 150-160 sm", "📏 160-170 sm", "📏 170-180 sm", "📏 180+ sm"]
            },
            {
                'text': "Mening ko'z rangim qanday?",
                'options': ["👁️ Qo'ng'ir", "👁️ Ko'k", "👁️ Yashil", "👁️ Kulrang"]
            },
            {
                'text': "Dam olishni qayerda o'tkazishni yaxshi ko'raman?",
                'options': ["🏖️ Dengiz bo'yida", "🏔️ Tog'larda", "🏙️ Shaharda", "🏡 Uyda"]
            },
            {
                'text': "Sevimli ovqatim?",
                'options': ["🍕 Pizza", "🍝 Pasta", "🍣 Sushi", "🍔 Burger"]
            },
            {
                'text': "Qaysi hayvonni uy hayvoni sifatida xohlayman?",
                'options': ["🐕 It", "🐈 Mushuk", "🐦 Qush", "🐠 Baliq"]
            },
            {
                'text': "Bo'sh vaqtimda nima bilan shug'ullanaman?",
                'options': ["📚 Kitob o'qish", "🎮 O'yin o'ynash", "🎬 Kino ko'rish", "🎵 Musiqa tinglash"]
            },
            {
                'text': "Qaysi faslni yaxshi ko'raman?",
                'options': ["🌸 Bahor", "☀️ Yoz", "🍂 Kuz", "❄️ Qish"]
            },
            {
                'text': "Ertalab yoki kechqurun nima ichaman?",
                'options': ["☕ Qahva", "🍵 Choy", "🥤 Sok", "💧 Suv"]
            },
            {
                'text': "Qaysi sport turi menga yoqadi?",
                'options': ["⚽ Futbol", "🏀 Basketbol", "🎾 Tennis", "🏊 Suzish"]
            },
            {
                'text': "Sevimli musiqa janrim?",
                'options': ["🎸 Rok", "🎤 Pop", "🎵 Jazz", "🎹 Klassik"]
            },
            {
                'text': "Do'stlar bilan nima qilishni yaxshi ko'raman?",
                'options': ["🎉 Party", "🎬 Kino", "🍽️ Restoran", "🎲 O'yinlar"]
            },
            {
                'text': "Qaysi vaqtda faolman?",
                'options': ["🌅 Erta tongda", "☀️ Kunduzi", "🌆 Kechqurun", "🌙 Tunda"]
            },
            {
                'text': "Sevimli filmlar janri?",
                'options': ["😂 Komediya", "😱 Qo'rqinchli", "❤️ Romantik", "🎬 Drama"]
            },
            {
                'text': "Orzuim qayerga sayohat qilish?",
                'options': ["🗼 Parij", "🗽 Nyu-York", "🗾 Yaponiya", "🏛️ Italiya"]
            }
        ],
        
        'ru': [
            {
                'text': "Мой любимый цвет?",
                'options': ["🔴 Красный", "🔵 Синий", "🟢 Зеленый", "🟡 Желтый"]
            },
            {
                'text': "Мой рост примерно?",
                'options': ["📏 150-160 см", "📏 160-170 см", "📏 170-180 см", "📏 180+ см"]
            },
            {
                'text': "Какой у меня цвет глаз?",
                'options': ["👁️ Карие", "👁️ Голубые", "👁️ Зеленые", "👁️ Серые"]
            },
            {
                'text': "Где я люблю отдыхать?",
                'options': ["🏖️ На пляже", "🏔️ В горах", "🏙️ В городе", "🏡 Дома"]
            },
            {
                'text': "Моя любимая еда?",
                'options': ["🍕 Пицца", "🍝 Паста", "🍣 Суши", "🍔 Бургер"]
            },
            {
                'text': "Какое домашнее животное я хочу?",
                'options': ["🐕 Собака", "🐈 Кошка", "🐦 Птица", "🐠 Рыбка"]
            },
            {
                'text': "Чем я занимаюсь в свободное время?",
                'options': ["📚 Читаю", "🎮 Играю", "🎬 Смотрю фильмы", "🎵 Слушаю музыку"]
            },
            {
                'text': "Какое время года я люблю?",
                'options': ["🌸 Весна", "☀️ Лето", "🍂 Осень", "❄️ Зима"]
            },
            {
                'text': "Что я пью утром или вечером?",
                'options': ["☕ Кофе", "🍵 Чай", "🥤 Сок", "💧 Вода"]
            },
            {
                'text': "Какой вид спорта мне нравится?",
                'options': ["⚽ Футбол", "🏀 Баскетбол", "🎾 Теннис", "🏊 Плавание"]
            },
            {
                'text': "Мой любимый жанр музыки?",
                'options': ["🎸 Рок", "🎤 Поп", "🎵 Джаз", "🎹 Классика"]
            },
            {
                'text': "Что я люблю делать с друзьями?",
                'options': ["🎉 Вечеринки", "🎬 Кино", "🍽️ Рестораны", "🎲 Игры"]
            },
            {
                'text': "Когда я наиболее активен?",
                'options': ["🌅 Рано утром", "☀️ Днем", "🌆 Вечером", "🌙 Ночью"]
            },
            {
                'text': "Мой любимый жанр фильмов?",
                'options': ["😂 Комедия", "😱 Ужасы", "❤️ Романтика", "🎬 Драма"]
            },
            {
                'text': "Куда я мечтаю поехать?",
                'options': ["🗼 Париж", "🗽 Нью-Йорк", "🗾 Япония", "🏛️ Италия"]
            }
        ],
        
        'en': [
            {
                'text': "What's my favorite color?",
                'options': ["🔴 Red", "🔵 Blue", "🟢 Green", "🟡 Yellow"]
            },
            {
                'text': "What's my approximate height?",
                'options': ["📏 150-160 cm", "📏 160-170 cm", "📏 170-180 cm", "📏 180+ cm"]
            },
            {
                'text': "What color are my eyes?",
                'options': ["👁️ Brown", "👁️ Blue", "👁️ Green", "👁️ Gray"]
            },
            {
                'text': "Where do I like to vacation?",
                'options': ["🏖️ Beach", "🏔️ Mountains", "🏙️ City", "🏡 Home"]
            },
            {
                'text': "What's my favorite food?",
                'options': ["🍕 Pizza", "🍝 Pasta", "🍣 Sushi", "🍔 Burger"]
            },
            {
                'text': "What pet do I want?",
                'options': ["🐕 Dog", "🐈 Cat", "🐦 Bird", "🐠 Fish"]
            },
            {
                'text': "What do I do in my free time?",
                'options': ["📚 Reading", "🎮 Gaming", "🎬 Movies", "🎵 Music"]
            },
            {
                'text': "What's my favorite season?",
                'options': ["🌸 Spring", "☀️ Summer", "🍂 Fall", "❄️ Winter"]
            },
            {
                'text': "What do I drink in the morning/evening?",
                'options': ["☕ Coffee", "🍵 Tea", "🥤 Juice", "💧 Water"]
            },
            {
                'text': "What sport do I like?",
                'options': ["⚽ Soccer", "🏀 Basketball", "🎾 Tennis", "🏊 Swimming"]
            },
            {
                'text': "What's my favorite music genre?",
                'options': ["🎸 Rock", "🎤 Pop", "🎵 Jazz", "🎹 Classical"]
            },
            {
                'text': "What do I like to do with friends?",
                'options': ["🎉 Parties", "🎬 Movies", "🍽️ Restaurants", "🎲 Games"]
            },
            {
                'text': "When am I most active?",
                'options': ["🌅 Early morning", "☀️ Daytime", "🌆 Evening", "🌙 Night"]
            },
            {
                'text': "What's my favorite movie genre?",
                'options': ["😂 Comedy", "😱 Horror", "❤️ Romance", "🎬 Drama"]
            },
            {
                'text': "Where do I dream of traveling?",
                'options': ["🗼 Paris", "🗽 New York", "🗾 Japan", "🏛️ Italy"]
            }
        ]
    }
    
    return questions.get(lang, questions['en'])