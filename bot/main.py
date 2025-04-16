import asyncio
from aiogram import Bot
from handlers import dp

# Укажи сюда свой токен
TOKEN = "YOUR_BOT_TOKEN"

bot = Bot(token=TOKEN)

async def main():
    await dp.start_polling(bot)
    
# Проверяем, является ли данный файл основным модулем
if __name__ == "__main__":
     # Запускаем основную асинхронную функцию
    asyncio.run(main())
except KeyboardInterrupt:
        # Обрабатываем прерывание программы (например, при нажатии Ctrl+C)
        print('Бот выключен')
