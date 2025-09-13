import os
import telebot
import requests

# 🔑 Токены
TELEGRAM_TOKEN = "8437821713:AAG04IHxcuZ2xT_InhsVKCHnS8VUBIRQT0A"
HF_TOKEN = "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"

# Модель (легкая и бесплатная)
MODEL = "google/gemma-2b-it"

# Системное сообщение (характер Экспрессика)
expressik_prompt = """
Ты — Экспрессик, лёгкий помощник.
- Отвечай кратко и понятно.
- Если пользователь просит "подробнее", дай развернутый ответ.
- Поддерживай русский и английский.
- Будь дружелюбным и безопасным.
"""

# Функция общения с HuggingFace
def ask_expressik(user_message: str, detailed: bool = False) -> str:
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }

    prompt = expressik_prompt + "\n\nПользователь: " + user_message
    if detailed:
        prompt += "\nПоясни подробнее."

    data = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": 200, "temperature": 0.7}
    }

    response = requests.post(
        f"https://api-inference.huggingface.co/models/{MODEL}",
        headers=headers,
        json=data
    )

    try:
        result = response.json()
        if isinstance(result, dict) and "error" in result:
            return "⚠️ Ошибка: " + result["error"]
        return result[0]["generated_text"].replace(prompt, "").strip()
    except Exception as e:
        return f"⚠️ Ошибка при обработке: {e}"


# Создаём Telegram-бота
bot = telebot.TeleBot(TELEGRAM_TOKEN)

@bot.message_handler(commands=["start"])
def start_message(message):
    bot.reply_to(
        message,
        "Привет! Я Экспрессик 🤖✨\n"
        "Пиши вопросы, и я отвечу кратко.\n"
        "Если хочешь длинное объяснение — добавь слово 'подробнее'."
    )

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    text = message.text.strip()
    detailed = "подробнее" in text.lower() or "detail" in text.lower()
    answer = ask_expressik(text, detailed=detailed)
    bot.reply_to(message, answer)

print("✅ Экспрессик запущен!")
bot.infinity_polling()
