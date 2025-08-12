import telebot
from telebot import types
import json
import os
import time
import hashlib
import random
from requests.exceptions import ConnectionError

# Конфигурация
TOKEN = '8257960150:AAEUC_EhgdOwFrIDKrfQ-iwn-jo0hlUxrhQ'
ADMIN_USERNAME = 'pleer'
DATA_FILES = {
    'users': 'users.json',
    'shop': 'shop.json',
    'premium_shop': 'premium_shop.json',
    'auction': 'auction.json',
    'storage': 'storage.json',
    'pass': 'pass.json'
}

# Инициализация бота
bot = telebot.TeleBot(TOKEN)

class DataManager:
    @staticmethod
    def load(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    @staticmethod
    def save(data, filename):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    @staticmethod
    def reset_all():
        default_data = {
            'users': {},
            'shop': {
                "express_plus": {"name": "Экспресс+", "price": 10000, "description": "Доступ к аукционам и премиум функциям"}
            },
            'premium_shop': {
                "premium": {"name": "Premium", "price": 15000, "description": "Кэшбэк 5%", "type": "subscription"},
                "platinum": {"name": "Platinum", "price": 25000, "description": "Кэшбэк 10%", "type": "subscription"},
                "silver": {"name": "Silver", "price": 50000, "description": "Кэшбэк 15% + бонусы", "type": "subscription"},
                "gold": {"name": "Gold", "price": 100000, "description": "Кэшбэк 25% + все бонусы", "type": "subscription"},
                "super_pass": {"name": "Супер Пропуск", "price": 15000, "description": "Дополнительные награды", "type": "pass"}
            },
            'auction': {
                "1": {"name": "Редкий предмет", "price": 5000, "description": "Эксклюзивный предмет аукциона"}
            },
            'storage': {},
            'pass': {
                "levels": [
                    {"points_required": 10, "rewards": [f"Обычная награда {i}" for i in range(1, 11)]},
                    {"points_required": 15, "rewards": [f"Обычная награда {i}" for i in range(11, 21)]},
                    {"points_required": 15, "rewards": [f"Обычная награда {i}" for i in range(21, 31)]},
                    {"points_required": 20, "rewards": [f"Обычная награда {i}" for i in range(31, 41)]}
                ],
                "super_rewards": [8, 9, 10, 19, 20, 28, 29, 30, 39, 40],
                "luckydrops": ["Редкий предмет 1", "Редкий предмет 2", "Уникальный предмет"]
            }
        }
        
        for key, filename in DATA_FILES.items():
            DataManager.save(default_data[key], filename)

# Инициализация данных
if not all(os.path.exists(f) for f in DATA_FILES.values()):
    DataManager.reset_all()

class UserManager:
    @staticmethod
    def register(user_id, username, password):
        users = DataManager.load(DATA_FILES['users'])
        is_admin = username.lower() == ADMIN_USERNAME
        
        users[user_id] = {
            'username': username,
            'password': hashlib.sha256(password.encode()).hexdigest(),
            'balance': 1000000 if is_admin else 0,
            'express_plus': is_admin,
            'subscription': 'GOLD' if is_admin else 'None',
            'super_pass': is_admin,
            'pass_points': 0,
            'pass_level': 1,
            'luckydrop_points': 0,
            'is_admin': is_admin,
            'storage': []
        }
        
        DataManager.save(users, DATA_FILES['users'])
        return users[user_id]

    @staticmethod
    def get_user(user_id):
        users = DataManager.load(DATA_FILES['users'])
        return users.get(user_id)

    @staticmethod
    def update_user(user_id, data):
        users = DataManager.load(DATA_FILES['users'])
        if user_id in users:
            users[user_id].update(data)
            DataManager.save(users, DATA_FILES['users'])
            return True
        return False

    @staticmethod
    def get_all_users():
        return DataManager.load(DATA_FILES['users'])

    @staticmethod
    def add_to_storage(user_id, item):
        storage = DataManager.load(DATA_FILES['storage'])
        if user_id not in storage:
            storage[user_id] = []
        storage[user_id].append(item)
        DataManager.save(storage, DATA_FILES['storage'])

class KeyboardManager:
    @staticmethod
    def main_menu(is_admin=False):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row("👤 Профиль", "🛍️ Магазин")
        if is_admin:
            markup.row("👑 Админ-панель", "📢 Рассылка")
        else:
            markup.row("🏆 Аукцион", "💎 Премиум")
        markup.row("📦 Хранилище", "🎫 Пропуск")
        markup.row("🔁 Сменить аккаунт")
        return markup

    @staticmethod
    def admin_menu():
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row("➕ Добавить товар", "➖ Удалить товар")
        markup.row("💰 Начислить ЭБ", "💸 Списать ЭБ")
        markup.row("🎫 Управление пропуском", "📦 Управление хранилищем")
        markup.row("📝 Список пользователей", "📢 Рассылка")
        markup.row("◀️ В главное меню")
        return markup

    @staticmethod
    def admin_shop_menu():
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row("Добавить обычный товар", "Удалить обычный товар")
        markup.row("Добавить премиум товар", "Удалить премиум товар")
        markup.row("Добавить аукцион лот", "Удалить аукцион лот")
        markup.row("◀️ Назад в админ-панель")
        return markup

    @staticmethod
    def admin_subscription_menu():
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row("Выдать Экспресс+", "Выдать Супер Пропуск")
        markup.row("Выдать Premium", "Выдать Platinum")
        markup.row("Выдать Silver", "Выдать GOLD")
        markup.row("◀️ Назад в админ-панель")
        return markup

    @staticmethod
    def back_to_menu(is_admin=False):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row("◀️ В главное меню")
        return markup

    @staticmethod
    def shop_menu():
        markup = types.InlineKeyboardMarkup()
        shop_items = DataManager.load(DATA_FILES['shop'])
        for item_id, item in shop_items.items():
            markup.add(types.InlineKeyboardButton(
                text=f"{item['name']} - {item['price']} ЭБ",
                callback_data=f"shop_{item_id}"
            ))
        return markup

    @staticmethod
    def premium_shop_menu():
        markup = types.InlineKeyboardMarkup()
        premium_items = DataManager.load(DATA_FILES['premium_shop'])
        for item_id, item in premium_items.items():
            markup.add(types.InlineKeyboardButton(
                text=f"{item['name']} - {item['price']} ЭБ",
                callback_data=f"premium_{item_id}"
            ))
        return markup

    @staticmethod
    def auction_menu():
        markup = types.InlineKeyboardMarkup()
        auction_items = DataManager.load(DATA_FILES['auction'])
        for item_id, item in auction_items.items():
            markup.add(types.InlineKeyboardButton(
                text=f"{item['name']} - {item['price']} ЭБ",
                callback_data=f"auction_{item_id}"
            ))
        return markup

    @staticmethod
    def storage_menu(user_id):
        markup = types.InlineKeyboardMarkup()
        storage = DataManager.load(DATA_FILES['storage']).get(user_id, [])
        for i, item in enumerate(storage, 1):
            markup.add(types.InlineKeyboardButton(
                text=f"{i}. {item}",
                callback_data=f"view_item_{i}"
            ))
        markup.add(types.InlineKeyboardButton("Очистить хранилище", callback_data="clear_storage"))
        return markup

    @staticmethod
    def admin_storage_menu():
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row("Добавить предмет", "Удалить предмет")
        markup.row("Просмотреть хранилище", "Очистить хранилище")
        markup.row("◀️ Назад в админ-панель")
        return markup

    @staticmethod
    def admin_pass_menu():
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row("Добавить очки", "Изменить уровень")
        markup.row("Изменить награды", "Добавить лакидроп")
        markup.row("◀️ Назад в админ-панель")
        return markup

class BotHandler:
    @staticmethod
    def show_main_menu(chat_id, is_admin=False):
        bot.send_message(chat_id, "Главное меню:", reply_markup=KeyboardManager.main_menu(is_admin))

    @staticmethod
    @bot.message_handler(commands=['start', 'reset'])
    def handle_start(message):
        if message.text == '/reset' and UserManager.get_user(str(message.from_user.id)) and UserManager.get_user(str(message.from_user.id))['is_admin']:
            DataManager.reset_all()
            bot.send_message(message.chat.id, "✅ Все данные сброшены!")
            return
        
        user_id = str(message.from_user.id)
        user = UserManager.get_user(user_id)
        
        if user:
            BotHandler.show_main_menu(message.chat.id, user['is_admin'])
        else:
            msg = bot.send_message(message.chat.id, "🔐 Для регистрации введите:\nЛогин Пароль\n(например: Ivan 12345)")
            bot.register_next_step_handler(msg, BotHandler.process_registration)

    @staticmethod
    @bot.message_handler(commands=['login'])
    def handle_login(message):
        user_id = str(message.from_user.id)
        msg = bot.send_message(message.chat.id, "🔐 Для входа введите:\nЛогин Пароль\n(например: Ivan 12345)", 
                             reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, BotHandler.process_login)

    @staticmethod
    def process_login(message):
        try:
            username, password = message.text.split(maxsplit=1)
            user_id = str(message.from_user.id)
            users = DataManager.load(DATA_FILES['users'])
            
            for uid, user_data in users.items():
                if (user_data['username'] == username and 
                    user_data['password'] == hashlib.sha256(password.encode()).hexdigest()):
                    users[user_id] = user_data
                    if uid != user_id:
                        del users[uid]
                    DataManager.save(users, DATA_FILES['users'])
                    
                    if users[user_id]['is_admin']:
                        bot.send_message(message.chat.id, f"👑 Администратор {username}, с возвращением!", 
                                       reply_markup=KeyboardManager.admin_menu())
                    else:
                        BotHandler.show_main_menu(message.chat.id)
                    return
            
            msg = bot.send_message(message.chat.id, "🔐 Аккаунт не найден. Хотите зарегистрироваться? (да/нет)")
            bot.register_next_step_handler(msg, lambda m: BotHandler.handle_register_prompt(m, username, password))
            
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Ошибка входа: {str(e)}\nПопробуйте снова /login")

    @staticmethod
    def handle_register_prompt(message, username, password):
        if message.text.lower() in ['да', 'yes']:
            user_id = str(message.from_user.id)
            user = UserManager.register(user_id, username, password)
            if user['is_admin']:
                bot.send_message(message.chat.id, f"👑 Администратор {username}, добро пожаловать!", 
                               reply_markup=KeyboardManager.admin_menu())
            else:
                BotHandler.show_main_menu(message.chat.id)
        else:
            bot.send_message(message.chat.id, "Регистрация отменена")

    @staticmethod
    @bot.message_handler(func=lambda message: message.text == "🔁 Сменить аккаунт")
    def handle_switch_account(message):
        BotHandler.handle_login(message)

    @staticmethod
    def process_registration(message):
        try:
            username, password = message.text.split(maxsplit=1)
            user_id = str(message.from_user.id)
            
            user = UserManager.register(user_id, username, password)
            if user['is_admin']:
                bot.send_message(message.chat.id, f"👑 Администратор {username}, добро пожаловать!", reply_markup=KeyboardManager.admin_menu())
            else:
                BotHandler.show_main_menu(message.chat.id)
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Ошибка регистрации: {str(e)}\nПопробуйте снова /start")

    @staticmethod
    @bot.message_handler(func=lambda message: message.text == "👤 Профиль")
    def show_profile(message):
        user_id = str(message.from_user.id)
        user = UserManager.get_user(user_id)
        
        if not user:
            bot.send_message(message.chat.id, "❌ Сначала зарегистрируйтесь через /start")
            return
        
        profile_text = (
            f"✨ Имя: {user['username']}\n"
            f"💵 Баланс: {user['balance']} ЭБ\n"
            f"☄️ Экспресс+: {'✅ Активен' if user['express_plus'] else '❌ Неактивен'}\n"
            f"💎 Подписка: {user['subscription']}\n"
            f"💠 Супер Пропуск: {'✅ Активен' if user['super_pass'] else '❌ Неактивен'}"
        )
        
        bot.send_message(message.chat.id, profile_text, reply_markup=KeyboardManager.back_to_menu(user['is_admin']))

    @staticmethod
    @bot.message_handler(func=lambda message: message.text == "🛍️ Магазин")
    def show_shop(message):
        user_id = str(message.from_user.id)
        user = UserManager.get_user(user_id)
        
        if not user:
            bot.send_message(message.chat.id, "❌ Сначала зарегистрируйтесь через /start")
            return
        
        bot.send_message(message.chat.id, "🛍️ Магазин товаров:", reply_markup=KeyboardManager.shop_menu())

    @staticmethod
    @bot.callback_query_handler(func=lambda call: call.data.startswith('shop_'))
    def handle_shop_callback(call):
        user_id = str(call.from_user.id)
        user = UserManager.get_user(user_id)
        item_id = call.data.split('_')[1]
        
        shop_items = DataManager.load(DATA_FILES['shop'])
        if item_id not in shop_items:
            bot.answer_callback_query(call.id, "❌ Товар не найден!")
            return
        
        item = shop_items[item_id]
        if user['balance'] < item['price']:
            bot.answer_callback_query(call.id, "❌ Недостаточно ЭБ!")
            return
        
        if item_id == "express_plus":
            UserManager.update_user(user_id, {'express_plus': True, 'balance': user['balance'] - item['price']})
            bot.answer_callback_query(call.id, "✅ Экспресс+ активирован!")
        else:
            UserManager.update_user(user_id, {'balance': user['balance'] - item['price']})
            UserManager.add_to_storage(user_id, item['name'])
            bot.answer_callback_query(call.id, f"✅ Куплено: {item['name']}!")
        
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=KeyboardManager.shop_menu())

    @staticmethod
    @bot.message_handler(func=lambda message: message.text == "💎 Премиум")
    def show_premium_shop(message):
        user_id = str(message.from_user.id)
        user = UserManager.get_user(user_id)
        
        if not user:
            bot.send_message(message.chat.id, "❌ Сначала зарегистрируйтесь через /start")
            return
        
        if not user['express_plus']:
            bot.send_message(message.chat.id, "❌ Необходимо купить Экспресс+ для доступа к премиум магазину!")
            return
        
        bot.send_message(message.chat.id, "💎 Премиум магазин:", reply_markup=KeyboardManager.premium_shop_menu())

    @staticmethod
    @bot.callback_query_handler(func=lambda call: call.data.startswith('premium_'))
    def handle_premium_shop_callback(call):
        user_id = str(call.from_user.id)
        user = UserManager.get_user(user_id)
        item_id = call.data.split('_')[1]
        
        premium_items = DataManager.load(DATA_FILES['premium_shop'])
        if item_id not in premium_items:
            bot.answer_callback_query(call.id, "❌ Товар не найден!")
            return
        
        item = premium_items[item_id]
        if user['balance'] < item['price']:
            bot.answer_callback_query(call.id, "❌ Недостаточно ЭБ!")
            return
        
        update_data = {'balance': user['balance'] - item['price']}
        if item['type'] == 'subscription':
            update_data['subscription'] = item_id.upper()
        elif item['type'] == 'pass':
            update_data['super_pass'] = True
        
        UserManager.update_user(user_id, update_data)
        bot.answer_callback_query(call.id, f"✅ Куплено: {item['name']}!")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=KeyboardManager.premium_shop_menu())

    @staticmethod
    @bot.message_handler(func=lambda message: message.text == "🏆 Аукцион")
    def show_auction(message):
        user_id = str(message.from_user.id)
        user = UserManager.get_user(user_id)
        
        if not user:
            bot.send_message(message.chat.id, "❌ Сначала зарегистрируйтесь через /start")
            return
        
        if not user['express_plus']:
            bot.send_message(message.chat.id, "❌ Необходимо купить Экспресс+ для доступа к аукциону!")
            return
        
        bot.send_message(message.chat.id, "🏆 Аукцион:", reply_markup=KeyboardManager.auction_menu())

    @staticmethod
    @bot.callback_query_handler(func=lambda call: call.data.startswith('auction_'))
    def handle_auction_callback(call):
        user_id = str(call.from_user.id)
        user = UserManager.get_user(user_id)
        item_id = call.data.split('_')[1]
        
        auction_items = DataManager.load(DATA_FILES['auction'])
        if item_id not in auction_items:
            bot.answer_callback_query(call.id, "❌ Лот не найден!")
            return
        
        item = auction_items[item_id]
        if user['balance'] < item['price']:
            bot.answer_callback_query(call.id, "❌ Недостаточно ЭБ!")
            return
        
        UserManager.update_user(user_id, {'balance': user['balance'] - item['price']})
        UserManager.add_to_storage(user_id, item['name'])
        bot.answer_callback_query(call.id, f"✅ Поздравляем с покупкой: {item['name']}!")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=KeyboardManager.auction_menu())

    @staticmethod
    @bot.message_handler(func=lambda message: message.text == "📦 Хранилище")
    def show_storage(message):
        user_id = str(message.from_user.id)
        user = UserManager.get_user(user_id)
        
        if not user:
            bot.send_message(message.chat.id, "❌ Сначала зарегистрируйтесь через /start")
            return
        
        storage = DataManager.load(DATA_FILES['storage']).get(user_id, [])
        if not storage:
            bot.send_message(message.chat.id, "📭 Ваше хранилище пусто", reply_markup=KeyboardManager.back_to_menu(user['is_admin']))
            return
        
        storage_text = "📦 Ваше хранилище:\n\n" + "\n".join(f"{i+1}. {item}" for i, item in enumerate(storage))
        bot.send_message(message.chat.id, storage_text, reply_markup=KeyboardManager.storage_menu(user_id))

    @staticmethod
    @bot.callback_query_handler(func=lambda call: call.data.startswith('view_item_'))
    def handle_view_item(call):
        user_id = str(call.from_user.id)
        storage = DataManager.load(DATA_FILES['storage']).get(user_id, [])
        item_index = int(call.data.split('_')[2]) - 1
        
        if 0 <= item_index < len(storage):
            bot.answer_callback_query(call.id, f"🔍 {storage[item_index]}")
        else:
            bot.answer_callback_query(call.id, "❌ Предмет не найден!")

    @staticmethod
    @bot.callback_query_handler(func=lambda call: call.data == "clear_storage")
    def handle_clear_storage(call):
        user_id = str(call.from_user.id)
        storage = DataManager.load(DATA_FILES['storage'])
        if user_id in storage and storage[user_id]:
            storage[user_id] = []
            DataManager.save(storage, DATA_FILES['storage'])
            bot.answer_callback_query(call.id, "✅ Хранилище очищено!")
            bot.edit_message_text("📭 Ваше хранилище пусто", call.message.chat.id, call.message.message_id)
        else:
            bot.answer_callback_query(call.id, "❌ Хранилище уже пусто!")

    @staticmethod
    @bot.message_handler(func=lambda message: message.text == "🎫 Пропуск")
    def show_pass(message):
        user_id = str(message.from_user.id)
        user = UserManager.get_user(user_id)
        
        if not user:
            bot.send_message(message.chat.id, "❌ Сначала зарегистрируйтесь через /start")
            return
        
        pass_data = DataManager.load(DATA_FILES['pass'])
        current_level = user['pass_level']
        level_info = pass_data['levels'][current_level-1] if current_level <= len(pass_data['levels']) else None
        
        pass_text = (
            f"🎫 Ваш пропуск:\n"
            f"🏆 Уровень: {current_level}/{len(pass_data['levels'])}\n"
            f"⭐ Очки: {user['pass_points']}/{level_info['points_required'] if level_info else 'MAX'}\n"
            f"🍀 Очки лакидропов: {user['luckydrop_points']}/30\n\n"
            f"Текущие награды:\n"
        )
        
        if level_info:
            for i, reward in enumerate(level_info['rewards'], 1):
                reward_emoji = "✨" if i in pass_data['super_rewards'] and user['super_pass'] else "•"
                pass_text += f"{reward_emoji} {reward}\n"
        
        bot.send_message(message.chat.id, pass_text, reply_markup=KeyboardManager.back_to_menu(user['is_admin']))

    @staticmethod
    @bot.message_handler(func=lambda message: message.text == "👑 Админ-панель")
    def show_admin_panel(message):
        user_id = str(message.from_user.id)
        user = UserManager.get_user(user_id)
        
        if not user or not user['is_admin']:
            bot.send_message(message.chat.id, "❌ У вас нет доступа к админ-панели!")
            return
        
        bot.send_message(message.chat.id, "👑 Админ-панель:", reply_markup=KeyboardManager.admin_menu())

    @staticmethod
    @bot.message_handler(func=lambda message: message.text in ["➕ Добавить товар", "➖ Удалить товар"])
    def handle_shop_management(message):
        user_id = str(message.from_user.id)
        user = UserManager.get_user(user_id)
        
        if not user or not user['is_admin']:
            bot.send_message(message.chat.id, "❌ У вас нет прав для этой операции!")
            return
        
        bot.send_message(message.chat.id, "🛍️ Управление магазином:", reply_markup=KeyboardManager.admin_shop_menu())

    @staticmethod
    @bot.message_handler(func=lambda message: message.text == "💰 Начислить ЭБ")
    def add_balance(message):
        user_id = str(message.from_user.id)
        user = UserManager.get_user(user_id)
        
        if not user or not user['is_admin']:
            bot.send_message(message.chat.id, "❌ У вас нет прав для этой операции!")
            return
        
        msg = bot.send_message(message.chat.id, "Введите ID пользователя и сумму через пробел:", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, BotHandler.process_add_balance)

    @staticmethod
    def process_add_balance(message):
        try:
            target_id, amount = message.text.split()
            amount = int(amount)
            
            users = UserManager.get_all_users()
            if target_id in users:
                users[target_id]['balance'] += amount
                DataManager.save(users, DATA_FILES['users'])
                bot.send_message(message.chat.id, f"✅ Пользователю {users[target_id]['username']} начислено {amount} ЭБ", reply_markup=KeyboardManager.admin_menu())
            else:
                bot.send_message(message.chat.id, "❌ Пользователь не найден", reply_markup=KeyboardManager.admin_menu())
        except:
            bot.send_message(message.chat.id, "❌ Неверный формат ввода", reply_markup=KeyboardManager.admin_menu())

    @staticmethod
    @bot.message_handler(func=lambda message: message.text == "💸 Списать ЭБ")
    def remove_balance(message):
        user_id = str(message.from_user.id)
        user = UserManager.get_user(user_id)
        
        if not user or not user['is_admin']:
            bot.send_message(message.chat.id, "❌ У вас нет прав для этой операции!")
            return
        
        msg = bot.send_message(message.chat.id, "Введите ID пользователя и сумму для списания через пробел:", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, BotHandler.process_remove_balance)

    @staticmethod
    def process_remove_balance(message):
        try:
            target_id, amount = message.text.split()
            amount = int(amount)
            
            users = UserManager.get_all_users()
            if target_id in users:
                if users[target_id]['balance'] >= amount:
                    users[target_id]['balance'] -= amount
                    DataManager.save(users, DATA_FILES['users'])
                    bot.send_message(message.chat.id, f"✅ У пользователя {users[target_id]['username']} списано {amount} ЭБ", reply_markup=KeyboardManager.admin_menu())
                else:
                    bot.send_message(message.chat.id, "❌ У пользователя недостаточно средств", reply_markup=KeyboardManager.admin_menu())
            else:
                bot.send_message(message.chat.id, "❌ Пользователь не найден", reply_markup=KeyboardManager.admin_menu())
        except:
            bot.send_message(message.chat.id, "❌ Неверный формат ввода", reply_markup=KeyboardManager.admin_menu())

    @staticmethod
    @bot.message_handler(func=lambda message: message.text in [
        "Добавить обычный товар", "Добавить премиум товар", "Добавить аукцион лот",
        "Удалить обычный товар", "Удалить премиум товар", "Удалить аукцион лот"
    ])
    def handle_item_management(message):
        user_id = str(message.from_user.id)
        user = UserManager.get_user(user_id)
        
        if not user or not user['is_admin']:
            bot.send_message(message.chat.id, "❌ У вас нет прав для этой операции!")
            return
        
        action = "add" if "Добавить" in message.text else "remove"
        shop_type = {
            "обычный товар": "shop",
            "премиум товар": "premium_shop",
            "аукцион лот": "auction"
        }[message.text.split()[1] + " " + message.text.split()[2]]
        
        if action == "add":
            if shop_type == "premium_shop":
                text = "Введите данные товара в формате:\nID_товара Название Цена Описание Тип\n(например: premium Premium 15000 Кэшбэк 5% subscription)"
            else:
                text = "Введите данные товара в формате:\nID_товара Название Цена Описание\n(например: express_plus Экспресс+ 10000 Доступ к аукционам)"
            
            msg = bot.send_message(message.chat.id, text, reply_markup=types.ReplyKeyboardRemove())
            bot.register_next_step_handler(msg, lambda m: process_add_item(m, shop_type))
        else:
            data = DataManager.load(DATA_FILES[shop_type])
            if not data:
                bot.send_message(message.chat.id, f"❌ В {shop_type} нет товаров!", reply_markup=KeyboardManager.admin_shop_menu())
                return
            
            items_text = "\n".join(f"{id}: {item['name']}" for id, item in data.items())
            msg = bot.send_message(message.chat.id, f"Выберите ID товара для удаления:\n\n{items_text}", reply_markup=types.ReplyKeyboardRemove())
            bot.register_next_step_handler(msg, lambda m: process_remove_item(m, shop_type))

    def process_add_item(message, shop_type):
        try:
            parts = message.text.split(maxsplit=3)
            if shop_type == 'premium_shop':
                if len(parts) < 4:
                    raise ValueError("Недостаточно данных")
                item_id, name, price, description = parts[0], parts[1], int(parts[2]), parts[3]
                item_type = description.split()[-1]
                description = ' '.join(description.split()[:-1])
                item = {
                    "name": name,
                    "price": price,
                    "description": description,
                    "type": item_type
                }
            else:
                if len(parts) < 3:
                    raise ValueError("Недостаточно данных")
                item_id, name, price, *description = parts[0], parts[1], int(parts[2]), ' '.join(parts[3:]) if len(parts) > 3 else ""
                item = {
                    "name": name,
                    "price": price,
                    "description": description
                }
            
            data = DataManager.load(DATA_FILES[shop_type])
            data[item_id] = item
            DataManager.save(data, DATA_FILES[shop_type])
            bot.send_message(message.chat.id, f"✅ Товар успешно {'добавлен' if shop_type != 'auction' else 'лот добавлен'} в {shop_type}!", reply_markup=KeyboardManager.admin_shop_menu())
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)}\nПопробуйте снова", reply_markup=KeyboardManager.admin_shop_menu())

    def process_remove_item(message, shop_type):
        try:
            item_id = message.text.strip()
            data = DataManager.load(DATA_FILES[shop_type])
            
            if item_id in data:
                del data[item_id]
                DataManager.save(data, DATA_FILES[shop_type])
                bot.send_message(message.chat.id, f"✅ Товар успешно удален из {shop_type}!", reply_markup=KeyboardManager.admin_shop_menu())
            else:
                bot.send_message(message.chat.id, "❌ Товар с таким ID не найден!", reply_markup=KeyboardManager.admin_shop_menu())
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)}", reply_markup=KeyboardManager.admin_shop_menu())

    @staticmethod
    @bot.message_handler(func=lambda message: message.text == "📝 Список пользователей")
    def show_user_list(message):
        user_id = str(message.from_user.id)
        user = UserManager.get_user(user_id)
        
        if not user or not user['is_admin']:
            bot.send_message(message.chat.id, "❌ У вас нет прав для этой операции!")
            return
        
        users = UserManager.get_all_users()
        if not users:
            bot.send_message(message.chat.id, "❌ Нет зарегистрированных пользователей", reply_markup=KeyboardManager.admin_menu())
            return
        
        users_text = "📝 Список пользователей:\n\n" + "\n".join(
            f"ID: {uid} | Имя: {data['username']} | Баланс: {data['balance']} ЭБ"
            for uid, data in users.items()
        )
        
        for i in range(0, len(users_text), 4096):
            bot.send_message(message.chat.id, users_text[i:i+4096], reply_markup=KeyboardManager.admin_menu())

    @staticmethod
    @bot.message_handler(func=lambda message: message.text == "📢 Рассылка")
    def start_broadcast(message):
        user_id = str(message.from_user.id)
        user = UserManager.get_user(user_id)
        
        if not user or not user['is_admin']:
            bot.send_message(message.chat.id, "❌ У вас нет прав для этой операции!")
            return
        
        msg = bot.send_message(message.chat.id, "Введите сообщение для рассылки:", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, BotHandler.process_broadcast)

    @staticmethod
    def process_broadcast(message):
        users = UserManager.get_all_users()
        success = 0
        failed = 0
        
        for user_id in users:
            try:
                bot.send_message(user_id, f"📢 Рассылка от администратора:\n\n{message.text}")
                success += 1
            except:
                failed += 1
        
        bot.send_message(message.chat.id, f"✅ Рассылка завершена!\nДоставлено: {success}\nНе доставлено: {failed}", reply_markup=KeyboardManager.admin_menu())

    @staticmethod
    @bot.message_handler(func=lambda message: message.text == "🎫 Управление пропуском")
    def manage_pass(message):
        user_id = str(message.from_user.id)
        user = UserManager.get_user(user_id)
        
        if not user or not user['is_admin']:
            bot.send_message(message.chat.id, "❌ У вас нет прав для этой операции!")
            return
        
        bot.send_message(message.chat.id, "🎫 Управление пропуском:", reply_markup=KeyboardManager.admin_pass_menu())

    @staticmethod
    @bot.message_handler(func=lambda message: message.text == "📦 Управление хранилищем")
    def manage_storage(message):
        user_id = str(message.from_user.id)
        user = UserManager.get_user(user_id)
        
        if not user or not user['is_admin']:
            bot.send_message(message.chat.id, "❌ У вас нет прав для этой операции!")
            return
        
        bot.send_message(message.chat.id, "📦 Управление хранилищем:", reply_markup=KeyboardManager.admin_storage_menu())

    @staticmethod
    @bot.message_handler(func=lambda message: message.text in [
        "Добавить предмет", "Удалить предмет",
        "Просмотреть хранилище", "Очистить хранилище"
    ])
    def handle_storage_management(message):
        user_id = str(message.from_user.id)
        user = UserManager.get_user(user_id)
        
        if not user or not user['is_admin']:
            bot.send_message(message.chat.id, "❌ У вас нет прав для этой операции!")
            return
        
        if message.text == "Просмотреть хранилище":
            msg = bot.send_message(message.chat.id, "Введите ID пользователя для просмотра хранилища:", reply_markup=types.ReplyKeyboardRemove())
            bot.register_next_step_handler(msg, process_view_storage_admin)
        elif message.text == "Очистить хранилище":
            msg = bot.send_message(message.chat.id, "Введите ID пользователя для очистки хранилища:", reply_markup=types.ReplyKeyboardRemove())
            bot.register_next_step_handler(msg, process_clear_storage_admin)
        elif message.text == "Добавить предмет":
            msg = bot.send_message(message.chat.id, "Введите ID пользователя и название предмета через пробел:", reply_markup=types.ReplyKeyboardRemove())
            bot.register_next_step_handler(msg, process_add_item_storage_admin)
        elif message.text == "Удалить предмет":
            msg = bot.send_message(message.chat.id, "Введите ID пользователя для просмотра хранилища:", reply_markup=types.ReplyKeyboardRemove())
            bot.register_next_step_handler(msg, process_select_user_for_remove_item)

    def process_view_storage_admin(message):
        try:
            target_id = message.text.strip()
            storage = DataManager.load(DATA_FILES['storage'])
            
            if target_id in storage and storage[target_id]:
                items_text = "📦 Хранилище пользователя:\n\n" + "\n".join(f"{i+1}. {item}" for i, item in enumerate(storage[target_id]))
                bot.send_message(message.chat.id, items_text, reply_markup=KeyboardManager.admin_storage_menu())
            else:
                bot.send_message(message.chat.id, "📭 Хранилище пользователя пусто", reply_markup=KeyboardManager.admin_storage_menu())
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)}", reply_markup=KeyboardManager.admin_storage_menu())

    def process_clear_storage_admin(message):
        try:
            target_id = message.text.strip()
            storage = DataManager.load(DATA_FILES['storage'])
            
            if target_id in storage and storage[target_id]:
                storage[target_id] = []
                DataManager.save(storage, DATA_FILES['storage'])
                bot.send_message(message.chat.id, "✅ Хранилище пользователя очищено!", reply_markup=KeyboardManager.admin_storage_menu())
            else:
                bot.send_message(message.chat.id, "❌ Хранилище пользователя уже пусто!", reply_markup=KeyboardManager.admin_storage_menu())
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)}", reply_markup=KeyboardManager.admin_storage_menu())

    def process_add_item_storage_admin(message):
        try:
            target_id, item = message.text.split(maxsplit=1)
            storage = DataManager.load(DATA_FILES['storage'])
            
            if target_id not in storage:
                storage[target_id] = []
            
            storage[target_id].append(item)
            DataManager.save(storage, DATA_FILES['storage'])
            bot.send_message(message.chat.id, f"✅ Предмет '{item}' добавлен в хранилище пользователя!", reply_markup=KeyboardManager.admin_storage_menu())
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)}", reply_markup=KeyboardManager.admin_storage_menu())

    def process_select_user_for_remove_item(message):
        try:
            target_id = message.text.strip()
            storage = DataManager.load(DATA_FILES['storage'])
            
            if target_id in storage and storage[target_id]:
                items_text = "\n".join(f"{i+1}. {item}" for i, item in enumerate(storage[target_id]))
                msg = bot.send_message(message.chat.id, f"Выберите номер предмета для удаления:\n\n{items_text}", reply_markup=types.ReplyKeyboardRemove())
                bot.register_next_step_handler(msg, lambda m: process_remove_item_storage_admin(m, target_id))
            else:
                bot.send_message(message.chat.id, "❌ Хранилище пользователя пусто!", reply_markup=KeyboardManager.admin_storage_menu())
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)}", reply_markup=KeyboardManager.admin_storage_menu())

    def process_remove_item_storage_admin(message, target_id):
        try:
            item_index = int(message.text.strip()) - 1
            storage = DataManager.load(DATA_FILES['storage'])
            
            if 0 <= item_index < len(storage[target_id]):
                removed_item = storage[target_id].pop(item_index)
                DataManager.save(storage, DATA_FILES['storage'])
                bot.send_message(message.chat.id, f"✅ Предмет '{removed_item}' удален из хранилища!", reply_markup=KeyboardManager.admin_storage_menu())
            else:
                bot.send_message(message.chat.id, "❌ Неверный номер предмета!", reply_markup=KeyboardManager.admin_storage_menu())
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)}", reply_markup=KeyboardManager.admin_storage_menu())

    @staticmethod
    @bot.message_handler(func=lambda message: message.text in [
        "Выдать Экспресс+", "Выдать Супер Пропуск",
        "Выдать Premium", "Выдать Platinum", "Выдать Silver", "Выдать GOLD"
    ])
    def handle_give_subscription(message):
        user_id = str(message.from_user.id)
        user = UserManager.get_user(user_id)
        
        if not user or not user['is_admin']:
            bot.send_message(message.chat.id, "❌ У вас нет прав для этой операции!")
            return
        
        subscription_type = {
            "Выдать Экспресс+": "express_plus",
            "Выдать Супер Пропуск": "super_pass",
            "Выдать Premium": "premium",
            "Выдать Platinum": "platinum",
            "Выдать Silver": "silver",
            "Выдать GOLD": "gold"
        }[message.text]
        
        msg = bot.send_message(message.chat.id, f"Введите ID пользователя для выдачи {message.text.split()[1]}:", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, lambda m: process_give_subscription(m, subscription_type))

    def process_give_subscription(message, sub_type):
        try:
            target_id = message.text.strip()
            users = UserManager.get_all_users()
            
            if target_id in users:
                if sub_type == "express_plus":
                    users[target_id]['express_plus'] = True
                elif sub_type == "super_pass":
                    users[target_id]['super_pass'] = True
                else:
                    users[target_id]['subscription'] = sub_type.upper()
                
                DataManager.save(users, DATA_FILES['users'])
                bot.send_message(message.chat.id, f"✅ Пользователю {users[target_id]['username']} выдана подписка {sub_type}!", reply_markup=KeyboardManager.admin_menu())
            else:
                bot.send_message(message.chat.id, "❌ Пользователь не найден", reply_markup=KeyboardManager.admin_menu())
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)}", reply_markup=KeyboardManager.admin_menu())

    @staticmethod
    @bot.message_handler(func=lambda message: message.text == "◀️ В главное меню")
    def back_to_main_menu(message):
        user_id = str(message.from_user.id)
        user = UserManager.get_user(user_id)
        
        if not user:
            bot.send_message(message.chat.id, "❌ Сначала зарегистрируйтесь через /start")
            return
        
        BotHandler.show_main_menu(message.chat.id, user['is_admin'])

    @staticmethod
    @bot.message_handler(func=lambda message: message.text == "◀️ Назад в админ-панель")
    def back_to_admin_panel(message):
        user_id = str(message.from_user.id)
        user = UserManager.get_user(user_id)
        
        if not user or not user['is_admin']:
            bot.send_message(message.chat.id, "❌ У вас нет прав для этой операции!")
            return
        
        bot.send_message(message.chat.id, "👑 Админ-панель:", reply_markup=KeyboardManager.admin_menu())

    @staticmethod
    def run():
        while True:
            try:
                print("Бот запущен! Для остановки нажмите Ctrl+C")
                bot.polling(none_stop=True, interval=1, timeout=30)
            except ConnectionError:
                print("Ошибка подключения. Переподключение через 10 сек...")
                time.sleep(10)
            except Exception as e:
                print(f"Критическая ошибка: {str(e)}. Перезапуск через 30 сек...")
                time.sleep(30)

if __name__ == '__main__':
    BotHandler.run()
