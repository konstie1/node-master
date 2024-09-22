from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Кнопка "Назад" для возврата в меню TRX
def back_to_trx_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_trx_menu")]
    ])
    return keyboard

# Основное меню для TRX
def trx_menu():
    buttons = [
        [InlineKeyboardButton(text="📈 Информация о ноде TRX", callback_data="trx_info")],
        [InlineKeyboardButton(text="💳 Генерация нового адреса", callback_data="trx_generate_address")],
        [InlineKeyboardButton(text="💸 Вывод средств", callback_data="trx_withdraw")],  # Кнопка для вывода средств
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]  
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Меню для отмены транзакции (TRX)
def cancel_check_menu_trx():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Cancel TRX", callback_data="cancel_trx")]
    ])
    return keyboard

# Меню для подтверждения или отмены транзакции (TRX)
def confirm_cancel_menu_trx(destination_address, amount):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Confirm TRX", callback_data=f"confirm_trx_withdraw_{destination_address}_{amount}")],
        [InlineKeyboardButton(text="❌ Cancel TRX", callback_data=f"cancel_trx_withdraw_{destination_address}_{amount}")]
    ])
    return keyboard
