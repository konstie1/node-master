from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def btc_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Тест Биткоин", callback_data="btc_test")],
        [InlineKeyboardButton(text="Назад", callback_data="back_to_main")]
    ])
