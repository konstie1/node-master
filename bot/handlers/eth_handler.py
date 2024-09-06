from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from bot.filters.admin_filter import is_admin

eth_router = Router()

@eth_router.message(Command(commands=["eth_menu"]))
@is_admin
async def eth_menu_handler(message: Message):
    # Создание инлайн-кнопок для меню ETH
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Тест", callback_data="eth_test")]
    ])
    await message.answer("ETH Menu:", reply_markup=keyboard)
