import asyncio
from aiogram import Bot

TOKEN = "7612164834:AAGlu9czEjxCYtAmEI6fLZndsA4GZI8vP1U"

async def main():
    print(f"Используем токен: {TOKEN}")
    
    # Создаем бота
    bot = Bot(token=TOKEN)
    
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