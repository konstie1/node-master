from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from bot.filters.admin_filter import is_admin

ltc_router = Router()

@ltc_router.message(Command(commands=["ltc_menu"]))
@is_admin
async def ltc_menu_handler(message: Message):
    # Создание инлайн-кнопок для меню LTC
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Тест", callback_data="ltc_test")]
    ])
    await message.answer("LTC Menu:", reply_markup=keyboard)
