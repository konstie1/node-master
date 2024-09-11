from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Меню для ноды Litecoin
def ltc_menu(show_back_button=False):
    buttons = [
        [InlineKeyboardButton(text="Инфо", callback_data="ltc_info")],
        [InlineKeyboardButton(text="Новый адрес", callback_data="ltc_new_address")],
        [InlineKeyboardButton(text="Вывести LTC", callback_data="ltc_withdraw")]  # Добавлена кнопка "Вывести LTC"
    ]
    
    # Кнопка для возврата в главное меню
    buttons.append([InlineKeyboardButton(text="Назад", callback_data="back_to_main")])

    if show_back_button:
        buttons = [[InlineKeyboardButton(text="Назад", callback_data="ltc_menu")]]  # Кнопка "Назад" для возврата в меню ноды

    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Меню для отмены проверки адреса
def cancel_check_menu():
    buttons = [
        [InlineKeyboardButton(text="Отмена", callback_data="cancel_check_address_ltc")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Меню для отображения кошельков
def wallet_menu(wallets):
    buttons = [[InlineKeyboardButton(text=wallet, callback_data=f"wallet_create_address_{wallet}")] for wallet in wallets]
    buttons.append([InlineKeyboardButton(text="Назад", callback_data="ltc_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Меню для подтверждения или отмены транзакции
def confirm_cancel_menu():
    buttons = [
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_withdraw_ltc")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_check_address_ltc")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Кнопка "Назад" в меню Litecoin
def back_to_ltc_menu():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="ltc_menu"))
    return keyboard
