# Music Converter Bot

Telegram бот для конвертации ссылок между музыкальными сервисами Spotify и Яндекс.Музыка.

## Функциональность

- Конвертация ссылок из Spotify в Яндекс.Музыку
- Конвертация ссылок из Яндекс.Музыки в Spotify
- Статистика использования для пользователей
- Админ-статистика для администраторов

## Установка

1. Клонируйте репозиторий:
```bash
git clone [repository-url]
cd music-converter-bot
```

2. Создайте виртуальное окружение и установите зависимости:
```bash
python -m venv venv
source venv/bin/activate  # для Linux/Mac
pip install -r requirements.txt
```

3. Создайте файл `.env` с необходимыми переменными окружения:
```
API_TOKEN=your_telegram_bot_token
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
YANDEX_TOKEN=your_yandex_music_token
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

## Запуск

```bash
python bot.py
```

## Деплой

Бот настроен на автоматический деплой через GitHub Actions при пуше в ветку `main`.

## Требования

- Python 3.10+
- Все необходимые зависимости указаны в `requirements.txt`

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