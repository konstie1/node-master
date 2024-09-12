from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def ltc_menu(show_back_button=False):
    buttons = [
        [InlineKeyboardButton(text="📈 Info", callback_data="ltc_info")],
        [InlineKeyboardButton(text="💳 Generate Address", callback_data="ltc_new_address")],
        [InlineKeyboardButton(text="💸 Withdraw LTC", callback_data="ltc_withdraw")]
    ]
    
    buttons.append([InlineKeyboardButton(text="🔙 Back", callback_data="back_to_main")])

    if show_back_button:
        buttons = [[InlineKeyboardButton(text="🔙 Back", callback_data="ltc_menu")]]

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def cancel_check_menu():
    buttons = [
        [InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_check_address_ltc")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def wallet_menu(wallets):
    buttons = [[InlineKeyboardButton(text=wallet, callback_data=f"wallet_create_address_{wallet}")] for wallet in wallets]
    buttons.append([InlineKeyboardButton(text="🔙 Back", callback_data="ltc_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def confirm_cancel_menu():
    buttons = [
        [InlineKeyboardButton(text="✅ Confirm", callback_data="confirm_withdraw_ltc")],
        [InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_check_address_ltc")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def back_to_ltc_menu():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🔙 Back", callback_data="ltc_menu"))
    return keyboard
