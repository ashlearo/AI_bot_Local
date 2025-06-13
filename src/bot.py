import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests  # Для запросов к Ollama API

# Конфигурация
OLLAMA_HOST = "http://localhost:11434"
MODEL_NAME = "deepseek-r1:7b"  # Выберите подходящую модель (1.5b, 7b, 14b и т.д.)

# Хранилище истории диалогов
user_sessions = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я локальный AI-бот. Задай вопрос:")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat.id
    user_input = update.message.text

    # Инициализация сессии
    if user_id not in user_sessions:
        user_sessions[user_id] = []

    # Формируем промпт с историей
    messages = [
        {"role": "system", "content": "Ты полезный ассистент. Отвечай на русском языке."},
        *user_sessions[user_id][-3:],  # Берём последние 3 сообщения
        {"role": "user", "content": user_input}
    ]

    try:
        # Отправляем запрос к Ollama API
        response = requests.post(
            f"{OLLAMA_HOST}/api/chat",
            json={
                "model": MODEL_NAME,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 500
                }
            }
        )

        if response.status_code == 200:
            answer = response.json()["message"]["content"]
            # Сохраняем историю
            user_sessions[user_id].extend([
                {"role": "user", "content": user_input},
                {"role": "assistant", "content": answer}
            ])
            await update.message.reply_text(answer)
        else:
            await update.message.reply_text(f"Ошибка: {response.text}")

    except Exception as e:
        await update.message.reply_text(f"Ошибка: {str(e)}")
        del user_sessions[user_id]

def main():
    app = Application.builder().token(os.getenv("TELEGRAM_TOKEN")).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
