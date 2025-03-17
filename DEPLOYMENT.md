# Инструкция по развертыванию

## Подготовка к развертыванию

1. Создайте аккаунт на выбранном хостинге (например, DigitalOcean)
2. Создайте новый Ubuntu сервер (рекомендуется Ubuntu 22.04 LTS)
3. Настройте SSH доступ к серверу

## Настройка сервера

1. Обновите систему:
```bash
sudo apt update && sudo apt upgrade -y
```

2. Установите необходимые пакеты:
```bash
sudo apt install python3-pip python3-venv git -y
```

3. Создайте пользователя для бота:
```bash
sudo useradd -m -s /bin/bash botuser
sudo usermod -aG sudo botuser
```

## Настройка GitHub Actions

1. В репозитории GitHub перейдите в Settings -> Secrets and variables -> Actions
2. Добавьте следующие секреты:
   - `SSH_HOST` - IP адрес вашего сервера
   - `SSH_USERNAME` - имя пользователя (botuser)
   - `SSH_PRIVATE_KEY` - приватный SSH ключ
   - `API_TOKEN` - токен вашего Telegram бота
   - `SPOTIFY_CLIENT_ID` - ID клиента Spotify
   - `SPOTIFY_CLIENT_SECRET` - секрет клиента Spotify
   - `YANDEX_TOKEN` - токен Яндекс.Музыки
   - `SUPABASE_URL` - URL вашей базы Supabase
   - `SUPABASE_KEY` - ключ Supabase

## Настройка автоматического деплоя

1. Создайте файл `.github/workflows/deploy.yml` в вашем репозитории:
```yaml
name: Deploy Bot

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Deploy to Server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SSH_HOST }}
          username: ${{ secrets.SSH_USERNAME }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /home/botuser/music-converter-bot
            git pull
            source venv/bin/activate
            pip install -r requirements.txt
            sudo systemctl restart music-bot
```

## Настройка systemd сервиса

1. Создайте файл сервиса:
```bash
sudo nano /etc/systemd/system/music-bot.service
```

2. Добавьте следующее содержимое:
```ini
[Unit]
Description=Music Converter Telegram Bot
After=network.target

[Service]
Type=simple
User=botuser
WorkingDirectory=/home/botuser/music-converter-bot
Environment=PATH=/home/botuser/music-converter-bot/venv/bin
ExecStart=/home/botuser/music-converter-bot/venv/bin/python bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

3. Включите и запустите сервис:
```bash
sudo systemctl enable music-bot
sudo systemctl start music-bot
```

## Мониторинг

Для мониторинга логов используйте:
```bash
sudo journalctl -u music-bot -f
```

## Обновление

Бот будет автоматически обновляться при пуше в ветку main. Также можно обновить вручную:
```bash
cd /home/botuser/music-converter-bot
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart music-bot
``` 