from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def xrp_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Тест", callback_data="xrp_test")],
        [InlineKeyboardButton(text="Назад", callback_data="back_to_main")]
    ])
