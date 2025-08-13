import telebot
from telebot import types
import json
import os
import hashlib
from requests.exceptions import ConnectionError

# Конфигурация
TOKEN = '8257960150:AAEUC_EhgdOwFrIDKrfQ-iwn-jo0hlUxrhQ'
ADMIN_USERNAME = 'pleer'

class ShopBot:
    def __init__(self):
        self.bot = telebot.TeleBot(TOKEN)
        self.data_files = {
            'users': 'users.json',
            'shop': 'shop.json',
            'premium_shop': 'premium_shop.json',
            'auction': 'auction.json',
            'storage': 'storage.json',
            'pass': 'pass.json'
        }
        self.setup_handlers()
        self.initialize_data()

    def initialize_data(self):
        if not all(os.path.exists(f) for f in self.data_files.values()):
            self.reset_all_data()

    def reset_all_data(self):
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
        
        for key, filename in self.data_files.items():
            self.save_data(default_data[key], filename)

    def load_data(self, filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_data(self, data, filename):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def setup_handlers(self):
        @self.bot.message_handler(commands=['start', 'reset'])
        def handle_start(message):
            if message.text == '/reset' and self.is_admin(message.from_user.id):
                self.reset_all_data()
                self.bot.send_message(message.chat.id, "✅ Все данные сброшены!")
                return
            
            user_id = str(message.from_user.id)
            if self.get_user(user_id):
                self.show_main_menu(message.chat.id, self.is_admin(user_id))
            else:
                msg = self.bot.send_message(message.chat.id, "🔐 Для регистрации введите:\nЛогин Пароль\n(например: Ivan 12345)")
                self.bot.register_next_step_handler(msg, self.process_registration)

        @self.bot.message_handler(func=lambda m: m.text in ["🛍️ Магазин", "💎 Премиум", "🏆 Аукцион"])
        def handle_shop(message):
            user_id = str(message.from_user.id)
            user = self.get_user(user_id)
            
            if not user:
                self.bot.send_message(message.chat.id, "❌ Сначала зарегистрируйтесь через /start")
                return
            
            if message.text == "🛍️ Магазин":
                self.show_shop_menu(message.chat.id)
            elif message.text == "💎 Премиум":
                if not user['express_plus']:
                    self.bot.send_message(message.chat.id, "❌ Для доступа нужен Экспресс+!")
                    return
                self.show_premium_menu(message.chat.id)
            elif message.text == "🏆 Аукцион":
                if not user['express_plus']:
                    self.bot.send_message(message.chat.id, "❌ Для доступа нужен Экспресс+!")
                    return
                self.show_auction_menu(message.chat.id)

        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('buy_'))
        def handle_purchase(call):
            user_id = str(call.from_user.id)
            user = self.get_user(user_id)
            
            if not user:
                self.bot.answer_callback_query(call.id, "❌ Сначала зарегистрируйтесь!")
                return
            
            parts = call.data.split('_')
            shop_type = parts[1]
            item_id = parts[2]
            
            shop_data = self.load_data(self.data_files[shop_type + ('_shop' if shop_type != 'shop' else '')])
            
            if item_id not in shop_data:
                self.bot.answer_callback_query(call.id, "❌ Товар не найден!")
                return
            
            item = shop_data[item_id]
            
            if user['balance'] < item['price']:
                self.bot.answer_callback_query(call.id, "❌ Недостаточно ЭБ!")
                return
            
            # Обработка покупки
            update_data = {'balance': user['balance'] - item['price']}
            
            if shop_type == 'shop' and item_id == 'express_plus':
                update_data['express_plus'] = True
                msg = "✅ Экспресс+ активирован!"
            elif shop_type == 'premium':
                if item['type'] == 'subscription':
                    update_data['subscription'] = item_id.upper()
                    msg = f"✅ Подписка {item['name']} активирована!"
                elif item['type'] == 'pass':
                    update_data['super_pass'] = True
                    msg = "✅ Супер Пропуск активирован!"
            else:
                self.add_to_storage(user_id, item['name'])
                msg = f"✅ Товар '{item['name']}' куплен!"
            
            self.update_user(user_id, update_data)
            self.bot.answer_callback_query(call.id, msg)
            
            # Обновляем меню
            if shop_type == 'shop':
                self.show_shop_menu(call.message.chat.id, call.message.message_id)
            elif shop_type == 'premium':
                self.show_premium_menu(call.message.chat.id, call.message.message_id)
            elif shop_type == 'auction':
                self.show_auction_menu(call.message.chat.id, call.message.message_id)

    def show_main_menu(self, chat_id, is_admin=False):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row("👤 Профиль", "🛍️ Магазин")
        if is_admin:
            markup.row("👑 Админ-панель", "📢 Рассылка")
        else:
            markup.row("🏆 Аукцион", "💎 Премиум")
        markup.row("📦 Хранилище", "🎫 Пропуск")
        markup.row("🔁 Сменить аккаунт")
        self.bot.send_message(chat_id, "Главное меню:", reply_markup=markup)

    def show_shop_menu(self, chat_id, message_id=None):
        markup = types.InlineKeyboardMarkup()
        shop_items = self.load_data(self.data_files['shop'])
        for item_id, item in shop_items.items():
            markup.add(types.InlineKeyboardButton(
                text=f"{item['name']} - {item['price']} ЭБ",
                callback_data=f"buy_shop_{item_id}"
            ))
        
        if message_id:
            self.bot.edit_message_reply_markup(chat_id, message_id, reply_markup=markup)
        else:
            self.bot.send_message(chat_id, "🛍️ Магазин товаров:", reply_markup=markup)

    def show_premium_menu(self, chat_id, message_id=None):
        markup = types.InlineKeyboardMarkup()
        premium_items = self.load_data(self.data_files['premium_shop'])
        for item_id, item in premium_items.items():
            markup.add(types.InlineKeyboardButton(
                text=f"{item['name']} - {item['price']} ЭБ",
                callback_data=f"buy_premium_{item_id}"
            ))
        
        if message_id:
            self.bot.edit_message_reply_markup(chat_id, message_id, reply_markup=markup)
        else:
            self.bot.send_message(chat_id, "💎 Премиум магазин:", reply_markup=markup)

    def show_auction_menu(self, chat_id, message_id=None):
        markup = types.InlineKeyboardMarkup()
        auction_items = self.load_data(self.data_files['auction'])
        for item_id, item in auction_items.items():
            markup.add(types.InlineKeyboardButton(
                text=f"{item['name']} - {item['price']} ЭБ",
                callback_data=f"buy_auction_{item_id}"
            ))
        
        if message_id:
            self.bot.edit_message_reply_markup(chat_id, message_id, reply_markup=markup)
        else:
            self.bot.send_message(chat_id, "🏆 Аукцион:", reply_markup=markup)

    def get_user(self, user_id):
        users = self.load_data(self.data_files['users'])
        return users.get(user_id)

    def update_user(self, user_id, data):
        users = self.load_data(self.data_files['users'])
        if user_id in users:
            users[user_id].update(data)
            self.save_data(users, self.data_files['users'])
            return True
        return False

    def add_to_storage(self, user_id, item):
        storage = self.load_data(self.data_files['storage'])
        if user_id not in storage:
            storage[user_id] = []
        storage[user_id].append(item)
        self.save_data(storage, self.data_files['storage'])

    def is_admin(self, user_id):
        user = self.get_user(str(user_id))
        return user and user.get('is_admin', False)

    def process_registration(self, message):
        try:
            username, password = message.text.split(maxsplit=1)
            user_id = str(message.from_user.id)
            
            users = self.load_data(self.data_files['users'])
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
            
            self.save_data(users, self.data_files['users'])
            
            if is_admin:
                self.bot.send_message(message.chat.id, f"👑 Администратор {username}, добро пожаловать!", reply_markup=self.get_admin_menu())
            else:
                self.show_main_menu(message.chat.id)
        except Exception as e:
            self.bot.send_message(message.chat.id, f"❌ Ошибка регистрации: {str(e)}\nПопробуйте снова /start")

    def get_admin_menu(self):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row("➕ Добавить товар", "➖ Удалить товар")
        markup.row("💰 Начислить ЭБ", "💸 Списать ЭБ")
        markup.row("🎫 Управление пропуском", "📦 Управление хранилищем")
        markup.row("📝 Список пользователей", "📢 Рассылка")
        markup.row("◀️ В главное меню")
        return markup

    def run(self):
        while True:
            try:
                print("Бот запущен! Для остановки нажмите Ctrl+C")
                self.bot.polling(none_stop=True, interval=1, timeout=30)
            except ConnectionError:
                print("Ошибка подключения. Переподключение через 10 сек...")
                time.sleep(10)
            except Exception as e:
                print(f"Критическая ошибка: {str(e)}. Перезапуск через 30 сек...")
                time.sleep(30)

if __name__ == '__main__':
    bot = ShopBot()
    bot.run()
