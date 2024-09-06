from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def ltc_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Тест", callback_data="ltc_test")],
        [InlineKeyboardButton(text="Назад", callback_data="back_to_main")]
    ])
