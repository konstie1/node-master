from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Основное меню XRP с опцией получения информации о кошельке
def xrp_menu():
    buttons = [
        [InlineKeyboardButton(text="📈 XRP Node Info", callback_data="xrp_info")],
        [InlineKeyboardButton(text="💳 Generate Address", callback_data="xrp_generate_address")],
        [InlineKeyboardButton(text="💸 Withdraw XRP", callback_data="xrp_withdraw")],
        [InlineKeyboardButton(text="🔍 Wallet Info", callback_data="xrp_wallet_info")],  # Кнопка для запроса информации о кошельке
        [InlineKeyboardButton(text="🔙 Back", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Кнопка "Назад" для возврата в меню XRP
def back_to_xrp_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Back", callback_data="back_to_xrp_menu")]
    ])

# Меню для отмены транзакции
def cancel_check_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_check_address")]
    ])

# Меню для подтверждения или отмены транзакции
def confirm_cancel_menu(address, amount):
    buttons = [
        [InlineKeyboardButton(text="✅ Confirm", callback_data=f"confirm_withdraw_{address}_{amount}")],
        [InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_check_address")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
