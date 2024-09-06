from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from bot.filters.admin_filter import is_admin

btc_router = Router()

@btc_router.message(Command(commands=["btc_menu"]))
@is_admin
async def btc_menu_handler(message: Message):
    # Создание инлайн-кнопок для меню BTC
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Тест", callback_data="btc_test")]
    ])
    await message.answer("BTC Menu:", reply_markup=keyboard)
