import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import logging

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = "8136958130:AAGtpXee4gdbmvEaTuIE00Vo9O8Xs6hk1Do"
WEATHER_API_KEY = "f220c36b6d3de34ef2082f3d53c82742"

# Главное меню
def get_main_menu():
    return ReplyKeyboardMarkup([
        ["🌤️ Погода", "💵 Курсы валют"],
        ["🎲 Рандомное число", "📆 Дата и время"],
        ["ℹ️ Помощь"]
    ], resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🔹 Выберите функцию в меню:",
        reply_markup=get_main_menu()
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text

    if text == "🌤️ Погода":
        await update.message.reply_text(
            "Введите название города на английском или русском:\n(Например: Moscow или Москва)",
            reply_markup=ReplyKeyboardMarkup([["Отмена"]], resize_keyboard=True)
        )
        context.user_data["awaiting_city"] = True

    elif text == "💵 Курсы валют":
        rates = get_currency_rates()
        await update.message.reply_text(rates, reply_markup=get_main_menu())

    elif text == "🎲 Рандомное число":
        import random
        await update.message.reply_text(
            f"🎯 Ваше число: {random.randint(1, 100)}",
            reply_markup=get_main_menu()
        )

    elif text == "📆 Дата и время":
        from datetime import datetime
        now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        await update.message.reply_text(
            f"📅 Текущая дата и время:\n{now}",
            reply_markup=get_main_menu()
        )

    elif text == "ℹ️ Помощь":
        await update.message.reply_text(
            "ℹ️ Доступные функции:\n\n"
            "• Погода - узнать погоду в любом городе\n"
            "• Курсы валют - актуальные курсы доллара и евро\n"
            "• Рандомное число - генератор чисел от 1 до 100\n"
            "• Дата и время - текущие дата и время",
            reply_markup=get_main_menu()
        )

    elif text == "Отмена":
        await update.message.reply_text(
            "Действие отменено",
            reply_markup=get_main_menu()
        )
        context.user_data["awaiting_city"] = False

    elif context.user_data.get("awaiting_city"):
        weather = get_weather(text)
        await update.message.reply_text(weather, reply_markup=get_main_menu())
        context.user_data["awaiting_city"] = False

    else:
        await update.message.reply_text(
            "Используйте кнопки меню для навигации",
            reply_markup=get_main_menu()
        )

def get_weather(city: str) -> str:
    try:
        # Пробуем найти город сначала с русским языком
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
        response = requests.get(url, timeout=5)
        data = response.json()

        # Если город не найден, пробуем английский
        if data.get("cod") != 200:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
            response = requests.get(url, timeout=5)
            data = response.json()

        if data.get("cod") != 200:
            error_msg = data.get("message", "Неизвестная ошибка")
            return f"❌ Город '{city}' не найден. Ошибка: {error_msg}\nПопробуйте другое название."

        # Успешный ответ
        weather_icons = {
            "clear": "☀️",
            "clouds": "⛅",
            "rain": "🌧️",
            "snow": "❄️",
            "thunderstorm": "⛈️",
            "drizzle": "🌦️",
            "mist": "🌫️"
        }

        weather_type = data["weather"][0]["main"].lower()
        icon = weather_icons.get(weather_type, "🌤️")

        temp = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]
        description = data["weather"][0]["description"].capitalize()
        humidity = data["main"]["humidity"]
        wind = data["wind"]["speed"]

        return (
            f"{icon} Погода в {data['name']}:\n"
            f"• Температура: {temp}°C (ощущается как {feels_like}°C)\n"
            f"• Состояние: {description}\n"
            f"• Влажность: {humidity}%\n"
            f"• Ветер: {wind} м/с"
        )

    except requests.exceptions.Timeout:
        return "⌛ Превышено время ожидания ответа от сервера погоды"
    except Exception as e:
        logging.error(f"Weather API error: {str(e)}")
        return "⚠ Произошла ошибка при запросе погоды. Попробуйте позже."

def get_currency_rates() -> str:
    try:
        url = "https://www.cbr-xml-daily.ru/daily_json.js"
        response = requests.get(url, timeout=5)
        data = response.json()
        usd = data["Valute"]["USD"]["Value"]
        eur = data["Valute"]["EUR"]["Value"]
        return (
            "📊 Актуальные курсы ЦБ РФ:\n"
            f"• Доллар: {usd:.2f} руб\n"
            f"• Евро: {eur:.2f} руб"
        )
    except Exception as e:
        logging.error(f"Currency API error: {str(e)}")
        return "⚠ Не удалось получить курсы валют. Попробуйте позже."

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logging.info("Бот запущен и готов к работе!")
    app.run_polling()

if __name__ == "__main__":
    main()
