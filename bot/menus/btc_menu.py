from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Меню для ноды биткоина

def btc_menu(show_back_button=False):
    buttons = [
        [InlineKeyboardButton(text="Инфо", callback_data="btc_info")],
        [InlineKeyboardButton(text="Новый адрес", callback_data="btc_new_address")],
        [InlineKeyboardButton(text="Вывести BTC", callback_data="btc_withdraw")],  # Добавлена кнопка "Вывести BTC"
    ]
    
    # Кнопка для возврата в главное меню
    buttons.append([InlineKeyboardButton(text="Назад", callback_data="back_to_main")])

    if show_back_button:
        buttons = [[InlineKeyboardButton(text="Назад", callback_data="btc_menu")]]  # Кнопка "Назад" для возврата в меню ноды

    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Меню для отмены проверки адреса
def cancel_check_menu():
    buttons = [
        [InlineKeyboardButton(text="Отмена", callback_data="cancel_check_address_btc")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Меню для отображения кошельков
def wallet_menu(wallets):
    buttons = [[InlineKeyboardButton(text=wallet, callback_data=f"wallet_create_address_{wallet}")] for wallet in wallets]
    buttons.append([InlineKeyboardButton(text="Назад", callback_data="btc_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def confirm_cancel_menu(adress, amount):
    buttons = [
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm_withdraw_btc")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_check_address_btc")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def back_to_btc_menu():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="btc_menu"))
    return keyboard