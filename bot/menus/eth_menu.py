from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def eth_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Info", callback_data="eth_info")],
        [InlineKeyboardButton(text="🔄 Generate New Address", callback_data="eth_generate")],
        [InlineKeyboardButton(text="💸 Withdraw ETH", callback_data="eth_withdraw")],
        [InlineKeyboardButton(text="🔙 Back to Main", callback_data="eth_back_to_main")]
    ])

def eth_info_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Back", callback_data="eth_back_to_eth_menu")]
    ])

def eth_generate_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Back", callback_data="eth_back_to_eth_menu")]
    ])

def eth_withdraw_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Back", callback_data="eth_back_to_eth_menu")]
    ])

def eth_back_to_eth_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Back to Ethereum Menu", callback_data="eth_back_to_eth_menu")]
    ])

def eth_confirm_cancel_menu():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Confirm", callback_data="eth_confirm_withdraw_eth"),
                InlineKeyboardButton(text="❌ Cancel", callback_data="eth_cancel_withdraw_eth")
            ]
        ]
    )
    return keyboard

def eth_cancel_check_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Cancel", callback_data="eth_cancel_withdraw")]
    ])
    return keyboard
