"""
Friendship test questions in Uzbek, Russian, and English
"""

def get_questions(lang: str):
    """Get 15 test questions in the specified language"""
    
    questions = {
        'uz': [
            {
                'text': "Sevimli rangim qaysi?",
                'options': ["🔴 Qizil", "🔵 Ko'k", "🟢 Yashil", "🟡 Sariq", "🟣 Binafsha", "⚫ Qora", "⚪️ Oq"]
            },
            {
                'text': "Mening bo'yim taxminan qancha?",
                'options': ["📏 150-160 sm", "📏 160-170 sm", "📏 170-180 sm", "📏 180+ sm"]
            },
            {
                'text': "Mening ko'z rangim qanday?",
                'options': ["👁️ Qora", "👁️ Jigarrang", "👁️ Ko'k", "👁️ Yashil", "👁️ Kulrang"]
            },
            {
                'text': "Dam olishni qayerda o'tkazishni yaxshi ko'raman?",
                'options': ["🏖️ Dengiz bo'yida", "🏔️ Tog'larda", "🏙️ Shaharda", "🏡 Uyda", "🏕️ Tabiatda", "🏝️ Tropik orollarda"]
            },
            {
                'text': "Sevimli ovqatim?",
                'options': ["🍕 Pizza", "🍝 Pasta", "🍣 Sushi", "🍔 Burger", "🥗 Manti", "🍜 Osh"]
            },
            {
                'text': "Qaysi hayvonni uy hayvoni sifatida xohlayman?",
                'options': ["🐕 It", "🐈 Mushuk", "🐦 Qush", "🐠 Baliq", "🐴 Ot", "🐰 Quyon"]
            },
            {
                'text': "Bo'sh vaqtimda nima bilan shug'ullanaman?",
                'options': ["📚 Kitob o'qish", "🎮 O'yin o'ynash", "🎬 Kino ko'rish", "🎵 Musiqa tinglash", "🎨 Rasm chizish", "⚽ Sport"]
            },
            {
                'text': "Qaysi faslni yaxshi ko'raman?",
                'options': ["🌸 Bahor", "☀️ Yoz", "🍂 Kuz", "❄️ Qish", "🌦️ Hammasi yoqadi"]
            },
            {
                'text': "Ertalab yoki kechqurun nima ichaman?",
                'options': ["☕ Qahva", "🍵 Choy", "🥤 Sok", "💧 Suv", "🥛 Sut", "🧃 Energetik ichimlik"]
            },
            {
                'text': "Qaysi sport turi menga yoqadi?",
                'options': ["⚽ Futbol", "🏀 Basketbol", "🎾 Tennis", "🏊 Suzish", "🏋️ Fitnes", "♟ Shaxmat"]
            },
            {
                'text': "Sevimli musiqa janrim?",
                'options': ["🎸 Rok", "🎤 Pop", "🎵 Jazz", "🎹 Klassik", "🎧 Elektron", "🎺 Hip-hop"]
            },
            {
                'text': "Do'stlar bilan nima qilishni yaxshi ko'raman?",
                'options': ["🎉 Party", "🎬 Kino", "🍽️ Restoran", "🎲 O'yinlar", "🎤 Karaoke"]
            },
            {
                'text': "Qaysi vaqtda faolman?",
                'options': ["🌅 Erta tongda", "☀️ Kunduzi", "🌆 Kechqurun", "🌙 Tunda"]
            },
            {
                'text': "Sevimli filmlar janri?",
                'options': ["😂 Komediya", "😱 Qo'rqinchli", "❤️ Romantik", "🎬 Drama", "🚀 Fantastika", "🕵️ Detektiv"]
            },
            {
                'text': "Orzuim qayerga sayohat qilish?",
                'options': ["🗼 Parij", "🗽 Nyu-York", "🗾 Tokio", "🏛️ Rim", "🕌 Istanbul", "🕋 Saudiya Arabistoni"]
            }
        ],
        
        'ru': [
            {
                'text': "Мой любимый цвет?",
                'options': ["🔴 Красный", "🔵 Синий", "🟢 Зеленый", "🟡 Желтый", "🟣 Фиолетовый", "⚫ Черный", "⚪️ Белый"]
            },
            {
                'text': "Мой рост примерно?",
                'options': ["📏 150-160 sm", "📏 160-170 sm", "📏 170-180 sm", "📏 180+ sm"]
            },
            {
                'text': "Какой у меня цвет глаз?",
                'options': ["👁️ Черные", "👁️ Карие", "👁️ Голубые", "👁️ Зеленые", "👁️ Серые"]
            },
            {
                'text': "Где я люблю отдыхать?",
                'options': ["🏖️ На пляже", "🏔️ В горах", "🏙️ В городе", "🏡 Дома", "🏕️ На природе"]
            },
            {
                'text': "Моя любимая еда?",
                'options': ["🍕 Пицца", "🍝 Паста", "🍣 Суши", "🍔 Бургер", "🥗 Салат", "🍜 Плов"]
            },
            {
                'text': "Какое домашнее животное я хочу?",
                'options': ["🐕 Собака", "🐈 Кошка", "🐦 Птица", "🐠 Рыбка", "🐴 Лощадь", "🐰 Кролик"]
            },
            {
                'text': "Чем я занимаюсь в свободное время?",
                'options': ["📚 Читаю", "🎮 Играю", "🎬 Смотрю фильмы", "🎵 Слушаю музыку", "🎨 Рисую", "⚽ Спорт"]
            },
            {
                'text': "Какое время года я люблю?",
                'options': ["🌸 Весна", "☀️ Лето", "🍂 Осень", "❄️ Зима", "🌦️ Все нравятся"]
            },
            {
                'text': "Что я пью утром или вечером?",
                'options': ["☕ Кофе", "🍵 Чай", "🥤 Сок", "💧 Вода", "🥛 Молоко", "🧃 Энергетик"]
            },
            {
                'text': "Какой вид спорта мне нравится?",
                'options': ["⚽ Футбол", "🏀 Баскетбол", "🎾 Теннис", "🏊 Плавание", "🏋️ Фитнес", "♟ Шахматы"]
            },
            {
                'text': "Мой любимый жанр музыки?",
                'options': ["🎸 Рок", "🎤 Поп", "🎵 Джаз", "🎹 Классика", "🎧 Электронная", "🎺 Хип-хоп"]
            },
            {
                'text': "Что я люблю делать с друзьями?",
                'options': ["🎉 Вечеринки", "🎬 Кино", "🍽️ Рестораны", "🎲 Игры", "🎤 Караоке", "☕ Кофейни"]
            },
            {
                'text': "Когда я наиболее активен?",
                'options': ["🌅 Рано утром", "☀️ Днем", "🌆 Вечером", "🌙 Ночью", "🌤️ Всегда"]
            },
            {
                'text': "Мой любимый жанр фильмов?",
                'options': ["😂 Комедия", "😱 Ужасы", "❤️ Романтика", "🎬 Драма", "🚀 Фантастика", "🕵️ Детектив"]
            },
            {
                'text': "Куда я мечтаю поехать?",
                'options': ["🗼 Париж", "🗽 Нью-Йорк", "🗾 Токио", "🏛️ Рим", "🕌 Стамбул", "🕋 Саудия"]
            }
        ],
        
        'en': [
            {
                'text': "What's my favorite color?",
                'options': ["🔴 Red", "🔵 Blue", "🟢 Green", "🟡 Yellow", "🟣 Purple", "⚫ Black"]
            },
            {
                'text': "What's my approximate height?",
                'options': ["📏 150-160 cm", "📏 160-170 cm", "📏 170-180 cm", "📏 180+ cm"]
            },
            {
                'text': "What color are my eyes?",
                'options': ["👁️ Black", "👁️ Brown", "👁️ Blue", "👁️ Green", "👁️ Gray"]
            },
            {
                'text': "Where do I like to vacation?",
                'options': ["🏖️ Beach", "🏔️ Mountains", "🏙️ City", "🏡 Home", "🏕️ Nature", "🏝️ Tropical islands"]
            },
            {
                'text': "What's my favorite food?",
                'options': ["🍕 Pizza", "🍝 Pasta", "🍣 Sushi", "🍔 Burger", "🥗 Salad", "🍜 Plov"]
            },
            {
                'text': "What pet do I want?",
                'options': ["🐕 Dog", "🐈 Cat", "🐦 Bird", "🐠 Fish", "🐴 Horse", "🐰 Rabbit"]
            },
            {
                'text': "What do I do in my free time?",
                'options': ["📚 Reading", "🎮 Gaming", "🎬 Movies", "🎵 Music", "🎨 Drawing", "⚽ Sports"]
            },
            {
                'text': "What's my favorite season?",
                'options': ["🌸 Spring", "☀️ Summer", "🍂 Fall", "❄️ Winter", "🌦️ All seasons"]
            },
            {
                'text': "What do I drink in the morning/evening?",
                'options': ["☕ Coffee", "🍵 Tea", "🥤 Juice", "💧 Water", "🥛 Milk", "🧃 Energy drink"]
            },
            {
                'text': "What sport do I like?",
                'options': ["⚽ Soccer", "🏀 Basketball", "🎾 Tennis", "🏊 Swimming", "🏋️ Fitness", "♟ Chess"]
            },
            {
                'text': "What's my favorite music genre?",
                'options': ["🎸 Rock", "🎤 Pop", "🎵 Jazz", "🎹 Classical", "🎧 Electronic", "🎺 Hip-hop"]
            },
            {
                'text': "What do I like to do with friends?",
                'options': ["🎉 Parties", "🎬 Movies", "🍽️ Restaurants", "🎲 Games", "🎤 Karaoke", "☕ Coffee shops"]
            },
            {
                'text': "When am I most active?",
                'options': ["🌅 Early morning", "☀️ Daytime", "🌆 Evening", "🌙 Night", "🌤️ Always"]
            },
            {
                'text': "What's my favorite movie genre?",
                'options': ["😂 Comedy", "😱 Horror", "❤️ Romance", "🎬 Drama", "🚀 Sci-Fi", "🕵️ Mystery"]
            },
            {
                'text': "Where do I dream of traveling?",
                'options': ["🗼 Paris", "🗽 New York", "🗾 Tokyo", "🏛️ Rome", "🕌 Istanbul", "🕋 Saudia Arabia"]
            }
        ]
    }
    
    return questions.get(lang, questions['en'])