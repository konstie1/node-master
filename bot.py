import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from bot.filters.admin_filter import AdminFilter, is_admin
from config.config import TOKEN
from bot.menus.btc_menu import btc_menu
from bot.menus.eth_menu import eth_menu
from bot.menus.ltc_menu import ltc_menu
from bot.menus.xrp_menu import xrp_menu
from bot.menus.trx_menu import trx_menu
from bot.menus.main_menu import main_menu

dp = Dispatcher()

# Главное меню
@dp.message(Command(commands=["start"]))
@is_admin
async def start_menu(message: Message, **kwargs):
    await message.answer("Choose a node menu:", reply_markup=main_menu())

# Обработка callback queries с фильтром для администраторов
@dp.callback_query(lambda call: call.data in ["btc_menu", "eth_menu", "ltc_menu", "xrp_menu", "trx_menu", "back_to_main"])
@is_admin
async def node_menu_handler(callback_query: CallbackQuery, **kwargs):
    # Если нажата кнопка "Назад", возвращаем в главное меню
    if callback_query.data == "back_to_main":
        await callback_query.message.edit_text("Choose a node menu:", reply_markup=main_menu())
    elif callback_query.data == "btc_menu":
        await callback_query.message.edit_text("BTC Menu:", reply_markup=btc_menu())
    elif callback_query.data == "eth_menu":
        await callback_query.message.edit_text("ETH Menu:", reply_markup=eth_menu())
    elif callback_query.data == "ltc_menu":
        await callback_query.message.edit_text("LTC Menu:", reply_markup=ltc_menu())
    elif callback_query.data == "xrp_menu":
        await callback_query.message.edit_text("XRP Menu:", reply_markup=xrp_menu())
    elif callback_query.data == "trx_menu":
        await callback_query.message.edit_text("TRX Menu:", reply_markup=trx_menu())

    # Подтверждение обработки callback
    await callback_query.answer()

# Обработка нажатия кнопки "Тест" для каждой ноды
@dp.callback_query(lambda call: call.data in ["btc_test", "eth_test", "ltc_test", "xrp_test", "trx_test"])
@is_admin
async def test_button_handler(callback_query: CallbackQuery, **kwargs):
    await callback_query.answer(f"Test button pressed in {callback_query.data.split('_')[0].upper()} menu!", show_alert=True)

# Инициализация
async def main():
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    # Применение фильтра администратора
    dp.update.middleware(AdminFilter())

    # Запуск поллинга
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
