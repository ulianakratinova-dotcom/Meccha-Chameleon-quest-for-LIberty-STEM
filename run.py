import asyncio

from aiogram import Bot, Dispatcher

from handlers import router
from info_table import async_main

bot = Bot(token='8873743308:AAGwxRPh-Z2rPhJVCfMK8vA7hm3AttZdo1A')
dp=Dispatcher()

async def main():
    await async_main()
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == '__main__':
        asyncio.run(main())
