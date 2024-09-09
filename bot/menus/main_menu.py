from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="BTC Menu", callback_data="btc_menu")],
        [InlineKeyboardButton(text="ETH Menu", callback_data="eth_menu")],
        [InlineKeyboardButton(text="LTC Menu", callback_data="ltc_menu")],
        [InlineKeyboardButton(text="XRP Menu", callback_data="xrp_menu")],
        [InlineKeyboardButton(text="TRX Menu", callback_data="trx_menu")]
    ])
