import asyncio
from aiogram import Bot
from dotenv import load_dotenv
import os

async def main():
    # Загружаем токен из .env
    load_dotenv()
    token = os.getenv("API_TOKEN")
    print(f"Токен: {token}")
    
    # Создаем бота
    bot = Bot(token=token)
    
    try:
        # Пробуем получить информацию о боте
        me = await bot.get_me()
        print(f"✅ Подключение успешно! Информация о боте:")
        print(f"ID: {me.id}")
        print(f"Имя: {me.full_name}")
        print(f"Username: @{me.username}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main()) 