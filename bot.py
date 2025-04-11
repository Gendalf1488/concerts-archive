from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
import json
from datetime import datetime, timedelta
from dateutil.parser import parse
import os

# Настройки
BOT_TOKEN = '7807114637:AAHMlbnGIz7CFEY1_zsQwr83GcwpyBSFVFY'  # Токен вашего бота
CHANNEL_ID = '2628454818'  # ID канала (начинается с "-100...")
DATA_FILE = 'concerts.json'  # Файл для хранения данных
HTML_FILE = 'index.html'  # HTML-файл для сайта

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Загрузка данных из JSON-файла
def load_concerts():
    try:
        with open(DATA_FILE, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return []

# Сохранение данных в JSON-файл
def save_concerts(concerts):
    with open(DATA_FILE, 'w') as file:
        json.dump(concerts, file, ensure_ascii=False, indent=4)

# Извлечение даты из текста
def extract_date(text):
    try:
        date = parse(text, fuzzy=True)
        return date.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return None

# Извлечение ссылки из текста
def extract_link(text):
    words = text.split()
    for word in words:
        if word.startswith('http'):
            return word
    return None

# Обновление статусов концертов
def update_concert_statuses():
    concerts = load_concerts()
    now = datetime.now()

    for concert in concerts:
        concert_date = datetime.strptime(concert['date'], "%Y-%m-%d %H:%M")
        if concert['status'] == "new" and (now - concert_date > timedelta(hours=24)):
            concert['status'] = "past"

    save_concerts(concerts)

# Генерация HTML-страницы
def generate_html():
    concerts = load_concerts()

    # Разделение на новые и прошедшие концерты
    new_concerts = [c for c in concerts if c['status'] == "new"]
    past_concerts = [c for c in concerts if c['status'] == "past"]

    # Сортировка по дате
    new_concerts.sort(key=lambda x: x['date'])
    past_concerts.sort(key=lambda x: x['date'], reverse=True)

    # Генерация HTML
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Concerts</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
            .concert { margin-bottom: 20px; }
            .concert img { max-width: 100%; height: auto; border-radius: 10px; }
            .concert p { font-size: 18px; margin-top: 10px; }
            .concert a { color: #007BFF; text-decoration: none; font-weight: bold; }
            .past { opacity: 0.7; }
        </style>
    </head>
    <body>
        <h1>Upcoming Concerts</h1>
    """

    for concert in new_concerts:
        html_content += f"""
        <div class="concert">
            <img src="{concert['image_url']}" alt="Image">
            <p>{concert['text']}</p>
            <a href="{concert['link']}" target="_blank">Read more</a>
        </div>
        """

    html_content += "<h1>Past Concerts</h1>"
    for concert in past_concerts:
        html_content += f"""
        <div class="concert past">
            <img src="{concert['image_url']}" alt="Image">
            <p>{concert['text']}</p>
            <a href="{concert['link']}" target="_blank">Read more</a>
        </div>
        """

    html_content += "</body></html>"

    # Сохранение HTML-файла
    with open(HTML_FILE, "w") as file:
        file.write(html_content)

# Загрузка изменений на GitHub Pages
def upload_to_github():
    os.system("git add .")
    os.system("git commit -m 'Update concerts'")
    os.system("git push origin main")

# Обработчик новых постов
@dp.channel_post_handler(content_types=['photo', 'text'])
async def handle_channel_post(message: types.Message):
    text = message.caption or message.text
    link = extract_link(text)
    date = extract_date(text)

    if not date:
        print("Date not found in the post.")
        return

    if message.photo:
        photo_id = message.photo[-1].file_id
        photo_url = await get_photo_url(photo_id)

        # Добавление нового концерта
        concerts = load_concerts()
        concerts.append({
            "image_url": photo_url,
            "text": text,
            "link": link,
            "date": date,
            "status": "new"
        })
        save_concerts(concerts)

        # Обновление статусов и генерация HTML
        update_concert_statuses()
        generate_html()
        upload_to_github()

# Получение URL картинки
async def get_photo_url(photo_id):
    file = await bot.get_file(photo_id)
    return f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file.file_path}"

# Запуск бота
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
