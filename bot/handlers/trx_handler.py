from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from bot.filters.admin_filter import is_admin

trx_router = Router()

@trx_router.message(Command(commands=["trx_menu"]))
@is_admin
async def trx_menu_handler(message: Message):
    # Создание инлайн-кнопок для меню TRX
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Тест", callback_data="trx_test")]
    ])
    await message.answer("TRX Menu:", reply_markup=keyboard)
