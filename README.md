# Music Service Converter Bot

Telegram бот для конвертации ссылок между музыкальными сервисами (Spotify ↔️ Яндекс.Музыка)

## Возможности

- Конвертация ссылок из Spotify в Яндекс.Музыку
- Конвертация ссылок из Яндекс.Музыки в Spotify
- Отслеживание статистики использования
- Админ-панель со статистикой

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/YOUR_USERNAME/music-converter-bot.git
cd music-converter-bot
```

2. Создайте виртуальное окружение и установите зависимости:
```bash
python -m venv venv
source venv/bin/activate  # Для Linux/Mac
# или
venv\Scripts\activate  # Для Windows
pip install -r requirements.txt
```

3. Создайте файл `.env` и заполните необходимые переменные окружения:
```env
API_TOKEN=your_telegram_bot_token
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
YANDEX_TOKEN=your_yandex_music_token
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

4. Запустите бота:
```bash
python bot.py
```

## Развертывание

Бот готов к развертыванию на серверах с использованием GitHub Actions. Подробные инструкции в [DEPLOYMENT.md](DEPLOYMENT.md).

## Статистика

Бот использует Supabase для хранения статистики использования. Доступны следующие метрики:
- Общее количество запросов
- Количество успешных конвертаций
- Количество ошибок
- Количество уникальных пользователей

## Лицензия

MIT 