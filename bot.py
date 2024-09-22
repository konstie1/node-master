import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from config.config import TOKEN  
from bot.handlers.btc_handler import btc_router 
from bot.handlers.start_handler import router as start_router  
from bot.handlers.ltc_handler import ltc_router
from bot.handlers.xrp_handler import xrp_router
from bot.handlers.trx_handler import trx_router
from bot.handlers.eth_handler import eth_router

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

bot = Bot(token=TOKEN)
dp = Dispatcher()


dp.include_router(btc_router)  
dp.include_router(start_router)  
dp.include_router(ltc_router) 
dp.include_router(xrp_router) 
dp.include_router(trx_router)
dp.include_router(eth_router)

async def shutdown(bot: Bot, dp: Dispatcher):
    logging.info("Завершение работы...")
    await dp.shutdown()  
    await bot.session.close() 
    logging.info("Бот завершил работу")

async def main():
    try:
        logging.info("Бот запущен")
        await dp.start_polling(bot)
    except (KeyboardInterrupt, SystemExit):
        logging.info("Прерывание, завершаем работу")
        await shutdown(bot, dp)
    except Exception as e:
        logging.error(f"Ошибка: {e}")
        await shutdown(bot, dp)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот был остановлен вручную")
