import requests
import json
import html
from aiogram import Router, types
from aiogram.types import CallbackQuery, Message
from aiogram.enums import ParseMode
from bot.menus.ltc_menu import ltc_menu, confirm_cancel_menu, cancel_check_menu
from bot.menus.main_menu import main_menu
from bot.filters.admin_filter import is_admin
from config.config import LITECOIN_IP, LITECOIN_PORT, LITECOIN_LOGIN, LITECOIN_PASSWORD
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
import aiohttp
import json

ltc_router = Router()

# Состояния для вывода LTC
class WithdrawLTCState(StatesGroup):
    waiting_for_address = State()
    waiting_for_amount = State()

# Обработка callback query для Litecoin и кнопок "Назад"
@ltc_router.callback_query(lambda call: call.data in ["ltc_menu", "ltc_info", "ltc_new_address", "ltc_withdraw", "back_to_main"])
@is_admin
async def ltc_menu_handler(callback_query: CallbackQuery, state: FSMContext, **kwargs):
    if callback_query.data == "ltc_menu":
        await callback_query.message.edit_text("LTC Menu:", reply_markup=ltc_menu())
    elif callback_query.data == "ltc_info":
        await get_ltc_info(callback_query)
    elif callback_query.data == "ltc_new_address":
        await create_ltc_address(callback_query)
    elif callback_query.data == "ltc_withdraw":
        response_message = await callback_query.message.edit_text("Введите адрес для вывода LTC:", reply_markup=cancel_check_menu())
        await state.update_data(address_message_id=response_message.message_id)
        await state.set_state(WithdrawLTCState.waiting_for_address)
    elif callback_query.data == "back_to_main":
        await callback_query.message.edit_text("Главное меню:", reply_markup=main_menu())

# Получение информации о ноде Litecoin
async def get_ltc_info(callback_query: CallbackQuery, **kwargs):
    url = f"http://{LITECOIN_IP}:{LITECOIN_PORT}/"
    headers = {'content-type': 'text/plain;'}
    
    blockchain_info_data = {
        "jsonrpc": "1.0",
        "id": "python_request",
        "method": "getblockchaininfo",
        "params": []
    }

    balance_data = {
        "jsonrpc": "1.0",
        "id": "python_request",
        "method": "getbalance",
        "params": []
    }

    try:
        blockchain_response = requests.post(url, auth=(LITECOIN_LOGIN, LITECOIN_PASSWORD), data=json.dumps(blockchain_info_data), headers=headers)
        blockchain_result = blockchain_response.json()

        balance_response = requests.post(url, auth=(LITECOIN_LOGIN, LITECOIN_PASSWORD), data=json.dumps(balance_data), headers=headers)
        balance_result = balance_response.json()

        balance_ltc = balance_result.get('result', 0)
        ltc_to_usd = await get_ltc_to_usd_rate()

        balance_usd = balance_ltc * ltc_to_usd

        verification_progress = blockchain_result['result'].get('verificationprogress', 0) * 100
        size_on_disk_gb = blockchain_result['result'].get('size_on_disk', 0) / (1024 ** 3)
        datadir = blockchain_result['result'].get('datadir', 'Неизвестно')

        formatted_info = (
            f"💻 <b>Информация о ноде Litecoin:</b>\n\n"
            f"📊 <b>Верификация:</b> {verification_progress:.2f}%\n"
            f"💾 <b>Вес на диске:</b> {size_on_disk_gb:.2f} GB\n"
            f"📂 <b>Путь к данным:</b> {html.escape(datadir)}\n"
            f"💰 <b>Баланс:</b> {balance_ltc:.8f} LTC (~${balance_usd:,.2f})\n"
        )
    except Exception as e:
        formatted_info = f"Ошибка при запросе информации о ноде: {html.escape(str(e))}"

    await callback_query.message.edit_text(formatted_info, reply_markup=ltc_menu(show_back_button=True), parse_mode=ParseMode.HTML)
    await callback_query.answer()

# Создание нового Litecoin-адреса
async def create_ltc_address(callback_query: CallbackQuery, **kwargs):
    url = f"http://{LITECOIN_IP}:{LITECOIN_PORT}/"
    headers = {'content-type': 'text/plain;'}
    
    new_address_data = {
        "jsonrpc": "1.0",
        "id": "python_request",
        "method": "getnewaddress",
        "params": []
    }

    try:
        response = requests.post(url, auth=(LITECOIN_LOGIN, LITECOIN_PASSWORD), data=json.dumps(new_address_data), headers=headers)
        result = response.json()
        
        new_address = result.get('result', 'Не удалось создать новый адрес')
        formatted_info = f"🏦 <b>Новый Litecoin-адрес:</b>\n\n🔑 <code>{new_address}</code>"
    except Exception as e:
        formatted_info = f"Ошибка при создании нового адреса: {html.escape(str(e))}"

    await callback_query.message.edit_text(formatted_info, reply_markup=ltc_menu(show_back_button=True), parse_mode=ParseMode.HTML)
    await callback_query.answer()

# Обработчик для получения адреса
@ltc_router.message(WithdrawLTCState.waiting_for_address)
async def handle_withdraw_address(message: types.Message, state: FSMContext, **kwargs):
    address = message.text
    if not address:
        await message.answer("Некорректный адрес, пожалуйста введите снова:")
        return

    user_data = await state.get_data()

    # Удаляем предыдущее сообщение бота
    if "address_message_id" in user_data:
        try:
            await message.bot.delete_message(message.chat.id, user_data['address_message_id'])
        except Exception:
            pass

    # Удаляем сообщение пользователя с адресом
    try:
        await message.delete()
    except Exception:
        pass

    await state.update_data(address=address)

    # Запрос на ввод суммы
    response_message = await message.answer("Теперь введите сумму для вывода:", reply_markup=cancel_check_menu())
    await state.update_data(amount_message_id=response_message.message_id)  # Сохраняем ID сообщения
    await state.set_state(WithdrawLTCState.waiting_for_amount)

# Обработчик для получения суммы
@ltc_router.message(WithdrawLTCState.waiting_for_amount)
async def handle_withdraw_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", "."))  
        if amount <= 0:
            raise ValueError("Сумма должна быть положительной.")
    except ValueError as e:
        await message.answer(f"Ошибка: {str(e)}")
        return

    user_data = await state.get_data()

    # Удаляем сообщение с запросом суммы (бота)
    if "amount_message_id" in user_data:
        try:
            await message.bot.delete_message(message.chat.id, user_data['amount_message_id'])
        except Exception:
            pass

    # Удаляем сообщение пользователя с суммой
    try:
        await message.delete()
    except Exception:
        pass

    # Сохраняем сумму и адрес в состоянии
    await state.update_data(amount=amount)

    # Подтверждение транзакции
    confirmation_message = await message.answer(
        f"Вы собираетесь отправить {amount} LTC на адрес {user_data['address']}.\n"
        f"Подтвердите отправку или отмените транзакцию.",
        reply_markup=confirm_cancel_menu()
    )
    await state.update_data(confirmation_message_id=confirmation_message.message_id)

# Обработчик подтверждения транзакции
@ltc_router.callback_query(lambda call: call.data == "confirm_withdraw_ltc")
async def confirm_withdraw_ltc(call: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()

    address = user_data.get('address')
    amount = user_data.get('amount')

    if not address or not amount:
        await call.message.answer("Ошибка: не удалось получить данные для транзакции.")
        return

    # Удаляем сообщение с подтверждением (бота)
    if "confirmation_message_id" in user_data:
        try:
            await call.message.bot.delete_message(call.message.chat.id, user_data['confirmation_message_id'])
        except Exception:
            pass

    url = f"http://{LITECOIN_IP}:{LITECOIN_PORT}/"
    headers = {'content-type': 'text/plain;'}
    data = {
        "jsonrpc": "1.0",
        "id": "python_request",
        "method": "sendtoaddress",
        "params": [address, amount, "", "", True]  # True добавлен для subtractfeefromamount
    }

    try:
        response = requests.post(url, auth=(LITECOIN_LOGIN, LITECOIN_PASSWORD), data=json.dumps(data), headers=headers)
        result = response.json()
        if 'error' in result and result['error']:
            error_msg = result['error'].get('message', 'Неизвестная ошибка')
            await call.message.answer(f"❌ Ошибка при отправке LTC: {error_msg}", reply_markup=ltc_menu())
        else:
            txid = result.get('result', 'Не удалось получить TXID')
            await call.message.answer(f"✅ LTC успешно отправлены! TXID: {txid}", reply_markup=ltc_menu())
    except Exception as e:
        await call.message.answer(f"❌ Ошибка при отправке LTC: {html.escape(str(e))}", reply_markup=ltc_menu())

    await state.clear()


# Обработчик отмены транзакции
@ltc_router.callback_query(lambda call: call.data == "cancel_check_address_ltc")
async def cancel_check_address_ltc(call: CallbackQuery, state: FSMContext, **kwargs):
    await state.clear()
    await call.message.edit_text("Операция отменена.", reply_markup=ltc_menu())

# Функция для получения курса LTC к доллару
async def get_ltc_to_usd_rate():
    url = "https://api.coingecko.com/api/v3/simple/price?ids=litecoin&vs_currencies=usd"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return data["litecoin"]["usd"]
            else:
                return None
