import asyncio
from aiogram import Bot
from handlers import dp

# Укажи сюда свой токен
TOKEN = "YOUR_BOT_TOKEN"

bot = Bot(token=TOKEN)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
