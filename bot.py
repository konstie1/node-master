import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from config.config import TOKEN  # Убедитесь, что ваш токен бота хранится в файле config
from bot.handlers.btc_handler import btc_router  # Импортируем роутер для BTC
from bot.handlers.start_handler import router as start_router  # Импортируем роутер для команды /start

# Настройка логирования
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Подключаем маршрутизаторы
dp.include_router(btc_router)  # Подключаем BTC роутер
dp.include_router(start_router)  # Подключаем роутер для команды /start

# Функция для корректного завершения работы
async def shutdown(bot: Bot, dp: Dispatcher):
    logging.info("Завершение работы...")
    await dp.shutdown()  # Остановка диспетчера
    await bot.session.close()  # Закрытие сессии бота
    logging.info("Бот завершил работу")

# Основная функция для запуска бота
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

# Запуск бота
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот был остановлен вручную")
