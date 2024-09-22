import json
import html
from aiogram import Router, types
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
from config.config import TRON_IP, TRON_PORT
from bot.menus.trx_menu import trx_menu, back_to_trx_menu
from bot.menus.main_menu import main_menu
from tronpy import Tron, keys
import requests

trx_router = Router()

# Инициализация клиента Tron
tron = Tron(network=f"http://{TRON_IP}:{TRON_PORT}")

# Обработка callback query для TRX
@trx_router.callback_query(lambda call: call.data in ["back_to_main", "trx_menu", "trx_info", "trx_generate_address", "back_to_trx_menu"])
async def trx_menu_handler(callback_query: CallbackQuery, **kwargs):
    if callback_query.data == "trx_menu":
        await update_message(callback_query.message, "TRX Menu:", trx_menu())
    elif callback_query.data == "trx_info":
        await get_trx_info(callback_query)
    elif callback_query.data == "trx_generate_address":
        await generate_trx_address(callback_query)
    elif callback_query.data == "back_to_trx_menu":
        await update_message(callback_query.message, "TRX Menu:", trx_menu())
    elif callback_query.data == "back_to_main":
        await update_message(callback_query.message, "Main Menu:", main_menu())

async def update_message(message: types.Message, new_text: str, new_markup: InlineKeyboardMarkup):
    if message.text != new_text or message.reply_markup != new_markup:
        await message.edit_text(new_text, reply_markup=new_markup, parse_mode=ParseMode.HTML)
    else:
        await message.answer("❓ Вы уже находитесь на этом экране.")

async def update_message(message: types.Message, new_text: str, new_markup: InlineKeyboardMarkup):
    current_text = message.text
    current_markup = message.reply_markup

    # Проверка различий
    if current_text == new_text and current_markup == new_markup:
        print("Новые данные совпадают с текущими.")
        return

    # Обновление сообщения
    await message.edit_text(new_text, reply_markup=new_markup, parse_mode=ParseMode.HTML)


# Функция для перехода в основное меню
async def back_to_main_menu(callback_query: CallbackQuery):
    try:
        # Обновляем сообщение пользователя основным меню
        await update_message(callback_query.message, "Main Menu:", main_menu())
        await callback_query.answer()
    except Exception as e:
        # Обработка ошибок
        await callback_query.message.answer(f"❌ Ошибка при возврате в основное меню: {str(e)}")

# Получение информации о ноде TRX
async def get_trx_info(callback_query: CallbackQuery, **kwargs):
    url = f"http://{TRON_IP}:{TRON_PORT}/wallet/getnodeinfo"
    
    try:
        response = requests.get(url)
        result = response.json()

        if 'activeConnectCount' in result:
            active_connections = result.get("activeConnectCount", "Неизвестно")
            version = result.get("configNodeInfo", {}).get("codeVersion", "Неизвестно")
            block_info = result.get("block", "Неизвестно")
            cpu_rate = result.get("machineInfo", {}).get("cpuRate", "Неизвестно")
            free_memory = result.get("machineInfo", {}).get("freeMemory", "Неизвестно")
            
            formatted_info = (
                f"💻 <b>Информация о ноде TRX:</b>\n\n"
                f"🌐 <b>Версия:</b> {version}\n"
                f"🔗 <b>Блок:</b> {block_info}\n"
                f"📶 <b>Активные подключения:</b> {active_connections}\n"
                f"🖥 <b>Загрузка CPU:</b> {cpu_rate}%\n"
                f"💾 <b>Свободная память:</b> {free_memory} байт\n"
            )
        else:
            formatted_info = "Ошибка: Не удалось получить информацию о ноде TRX."
    except Exception as e:
        formatted_info = f"Ошибка при запросе информации о ноде: {html.escape(str(e))}"

    await update_message(callback_query.message, formatted_info, back_to_trx_menu())
    await callback_query.answer()

# Обработчик генерации нового TRX-адреса
@trx_router.callback_query(lambda call: call.data == "trx_generate_address")
async def generate_trx_address(callback_query: CallbackQuery):
    try:
        # Генерация нового адреса и приватного ключа с помощью Tronpy
        private_key = keys.PrivateKey.random()
        address = private_key.public_key.to_base58check_address()
        
        formatted_info = (
            f"💳 <b>Новый TRX-адрес:</b> <code>{address}</code>\n"
            f"🔑 <b>Приватный ключ:</b> <code>{private_key.hex()}</code>"
        )
    except Exception as e:
        formatted_info = f"❌ Ошибка при генерации адреса: {str(e)}"

    # Отправляем сообщение пользователю
    await update_message(callback_query.message, formatted_info, back_to_trx_menu())
    await callback_query.answer()
