from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Кнопка "Назад" для возврата в меню XRP
def back_to_xrp_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_xrp_menu")]
    ])
    return keyboard

# Основное меню для XRP
def xrp_menu():
    buttons = [
        [InlineKeyboardButton(text="📈 Информация о ноде XRP", callback_data="xrp_info")],
        [InlineKeyboardButton(text="💳 Генерировать адрес", callback_data="xrp_generate_address")],
        [InlineKeyboardButton(text="💸 Вывести XRP", callback_data="xrp_withdraw")],  # Добавлена кнопка для вывода XRP
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Кнопка для отмены проверки
def cancel_check_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отмена", callback_data="cancel_check_address")]
    ])


# Меню для подтверждения или отмены транзакции
def confirm_cancel_menu(address, amount):
    buttons = [
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm_withdraw_{address}_{amount}")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_check_address")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)