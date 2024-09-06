from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from bot.filters.admin_filter import is_admin

xrp_router = Router()

@xrp_router.message(Command(commands=["xrp_menu"]))
@is_admin
async def xrp_menu_handler(message: Message):
    # Создание инлайн-кнопок для меню XRP
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Тест", callback_data="xrp_test")]
    ])
    await message.answer("XRP Menu:", reply_markup=keyboard)
