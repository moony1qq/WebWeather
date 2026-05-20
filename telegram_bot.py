import sys
import os
from dotenv import load_dotenv

load_dotenv()

# Allow importing WeatherService from the Django app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "weather_project.settings")

import django
django.setup()

import telebot
from telebot import types
from weather.services import WeatherService

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is not set in your .env file")

bot = telebot.TeleBot(BOT_TOKEN)
service = WeatherService()

# --- FAQ RESPONSES (quick replies to common messages) ---
FAQ_RESPONSES = {
    "hello": "Hey! Good to see you. Use the menu buttons below or just ask me about the weather! 👋",
    "hi": "Hi there! How can I help? ☀️",
    "hey": "Hey! Ready to check the weather for you. 🌤️",
    "how are you": "Running perfectly! My servers are working hard to get you accurate forecasts. How about you? 😊",
    "who made you": "I was built by a developer using Python and Django! 🐍",
    "what can you do": "I can show current weather and a 5-day forecast for any city in the world. Try `/weather London` or use the buttons below!",
    "thanks": "You're welcome! Come back anytime you need to know whether to grab an umbrella. ☂️",
    "thank you": "Anytime! Happy to help. 😊",
    "what's the weather": "To check the weather, use the 'Current Weather 🌍' button or type a command like: `/weather Almaty`",
    "forecast": "I can give you a 5-day forecast! Hit the '5-Day Forecast 📅' button or type `/forecast Astana`",
    "what to wear": "If it's cold — layer up, if it's warm — don't forget a hat! Better yet, check the exact temp with `/weather <city>` 🧥👕",
    "umbrella": "Good thinking! Check the weather description with `/weather <city>`. If it says 'rain' — definitely bring one! 🌧️",
    "bye": "See you later! Stay warm out there! ❄️",
    "goodbye": "Goodbye! Catch you next time! 🚀",
}


# --- KEYBOARD BUTTONS ---
def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_weather = types.KeyboardButton("Current Weather 🌍")
    btn_forecast = types.KeyboardButton("5-Day Forecast 📅")
    btn_help = types.KeyboardButton("Help ❓")
    btn_about = types.KeyboardButton("Who made you? 🤖")
    markup.add(btn_weather, btn_forecast, btn_help, btn_about)
    return markup


# --- FORMATTERS ---
def format_current(w) -> str:
    return (
        f"🌍 *{w.city}, {w.country}*\n\n"
        f"🌡 *{w.temperature:.1f}°C* (feels like {w.feels_like:.1f}°C)\n"
        f"☁️ {w.description}\n"
        f"💧 Humidity: {w.humidity}%\n"
        f"💨 Wind: {w.wind_speed} m/s"
    )


def format_forecast(f) -> str:
    lines = [f"📅 *5-Day Forecast — {f.city}, {f.country}*\n"]
    for day in f.days:
        lines.append(
            f"*{day.weekday}* ({day.date}): "
            f"{day.temp_max:.0f}° / {day.temp_min:.0f}° — {day.description}"
        )
    return "\n".join(lines)


# --- COMMAND HANDLERS ---

@bot.message_handler(commands=["start"])
def cmd_start(message):
    bot.send_message(
        message.chat.id,
        "👋 Welcome to *WeatherBot*!\n\n"
        "I can help you check the weather anywhere in the world. "
        "Use the menu buttons below or type commands directly.\n\n"
        "ℹ️ *Available commands:*\n"
        "`/weather <city>` — current weather\n"
        "`/forecast <city>` — 5-day forecast\n"
        "`/help` — show this help message",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )


@bot.message_handler(commands=["help"])
@bot.message_handler(func=lambda m: m.text == "Help ❓")
def cmd_help(message):
    bot.reply_to(
        message,
        "Here's what you can do:\n\n"
        "• Current weather: `/weather London`\n"
        "• 5-day forecast: `/forecast Tokyo`\n"
        "• Or use the buttons in the menu below!\n\n"
        "You can also just chat with me — I understand common phrases.",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )


@bot.message_handler(commands=["weather"])
def cmd_weather(message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(message, "Please specify a city. Example: `/weather London`", parse_mode="Markdown")
        return
    city = parts[1].strip()
    fetch_and_send_weather(message, city)


@bot.message_handler(commands=["forecast"])
def cmd_forecast(message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(message, "Please specify a city. Example: `/forecast Tokyo`", parse_mode="Markdown")
        return
    city = parts[1].strip()
    fetch_and_send_forecast(message, city)


# --- HELPERS ---

def fetch_and_send_weather(message, city):
    try:
        weather = service.get_current_weather(city)
        bot.reply_to(message, format_current(weather), parse_mode="Markdown")
    except ValueError as e:
        bot.reply_to(message, f"❌ Error: {e}")
    except ConnectionError:
        bot.reply_to(message, "❌ Network error. Please try again later.")


def fetch_and_send_forecast(message, city):
    try:
        forecast = service.get_forecast(city)
        bot.reply_to(message, format_forecast(forecast), parse_mode="Markdown")
    except ValueError as e:
        bot.reply_to(message, f"❌ Error: {e}")
    except ConnectionError:
        bot.reply_to(message, "❌ Network error. Please try again later.")


# --- TEXT & DIALOGUE HANDLER (smart fallback) ---

MENU_BUTTONS = ["Current Weather 🌍", "5-Day Forecast 📅", "Help ❓", "Who made you? 🤖"]

@bot.message_handler(func=lambda m: True)
def handle_text_and_dialogue(message):
    text_lower = message.text.lower().strip()

    # 1. Handle menu button presses
    if message.text == "Current Weather 🌍":
        msg = bot.reply_to(message, "Enter the city name you want weather for (e.g. London):")
        bot.register_next_step_handler(msg, process_weather_step)
        return

    elif message.text == "5-Day Forecast 📅":
        msg = bot.reply_to(message, "Enter the city name for the 5-day forecast:")
        bot.register_next_step_handler(msg, process_forecast_step)
        return

    elif message.text == "Who made you? 🤖":
        bot.reply_to(message, FAQ_RESPONSES["who made you"])
        return

    # 2. Check FAQ dictionary
    for key, response in FAQ_RESPONSES.items():
        if key in text_lower:
            bot.reply_to(message, response)
            return

    # 3. Unknown input fallback
    bot.reply_to(
        message,
        "🤔 I didn't quite understand that.\n\n"
        "Try using the menu buttons or type a command:\n"
        "`/weather <city>` — current weather\n"
        "`/forecast <city>` — 5-day forecast",
        parse_mode="Markdown"
    )


# --- NEXT STEP HANDLERS ---

def process_weather_step(message):
    city = message.text.strip()
    if city.startswith('/') or city in MENU_BUTTONS:
        bot.reply_to(message, "Request cancelled. Returning to main menu.", reply_markup=get_main_keyboard())
        return
    fetch_and_send_weather(message, city)


def process_forecast_step(message):
    city = message.text.strip()
    if city.startswith('/') or city in MENU_BUTTONS:
        bot.reply_to(message, "Request cancelled. Returning to main menu.", reply_markup=get_main_keyboard())
        return
    fetch_and_send_forecast(message, city)


if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()
