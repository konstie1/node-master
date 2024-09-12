from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def btc_menu(show_back_button=False):
    buttons = [
        [InlineKeyboardButton(text="📈 Info", callback_data="btc_info")],
        [InlineKeyboardButton(text="💳 Generate Address", callback_data="btc_new_address")],
        [InlineKeyboardButton(text="💸 Withdraw BTC", callback_data="btc_withdraw")]
    ]
    
    buttons.append([InlineKeyboardButton(text="🔙 Back", callback_data="back_to_main")])

    if show_back_button:
        buttons = [[InlineKeyboardButton(text="🔙 Back", callback_data="btc_menu")]]

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def cancel_check_menu():
    buttons = [
        [InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_check_address_btc")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def wallet_menu(wallets):
    buttons = [[InlineKeyboardButton(text=wallet, callback_data=f"wallet_create_address_{wallet}")] for wallet in wallets]
    buttons.append([InlineKeyboardButton(text="🔙 Back", callback_data="btc_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def confirm_cancel_menu(address, amount):
    buttons = [
        [InlineKeyboardButton(text="✅ Confirm", callback_data="confirm_withdraw_btc")],
        [InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_check_address_btc")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def back_to_btc_menu():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🔙 Back", callback_data="btc_menu"))
    return keyboard
