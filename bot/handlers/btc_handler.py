import requests
import json
import html
from aiogram import Router, types
from aiogram.types import CallbackQuery
from aiogram.enums import ParseMode
from bot.menus.btc_menu import btc_menu, wallet_menu, cancel_check_menu, confirm_cancel_menu  # Используем меню кошельков
from bot.menus.main_menu import main_menu
from bot.filters.admin_filter import is_admin
from config.config import BITCOIN_IP, BITCOIN_PORT, BITCOIN_LOGIN, BITCOIN_PASSWORD
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

btc_router = Router()

# Состояния для вывода биткоина
class WithdrawBTCState(StatesGroup):
    waiting_for_address = State()
    waiting_for_amount = State()

#  class DataState(StatesGroup):
#     data = State()

# Обработчик нажатия кнопки "Вывести BTC"
@btc_router.callback_query(lambda call: call.data == "btc_withdraw")
@is_admin
async def start_withdraw(callback_query: CallbackQuery, state: FSMContext, **kwargs):
    # Отправляем запрос на ввод адреса
    response_message = await callback_query.message.edit_text("Введите адрес для вывода BTC:", reply_markup=cancel_check_menu())
    await state.update_data(address_message_id=response_message.message_id)  # Сохраняем ID сообщения бота
    await state.set_state(WithdrawBTCState.waiting_for_address)

# Обработчик для получения адреса
@btc_router.message(WithdrawBTCState.waiting_for_address)
async def handle_withdraw_address(message: types.Message, state: FSMContext, **kwargs):
    address = message.text
    if not address:
        await message.answer("Некорректный адрес, пожалуйста введите снова:")
        return

    user_data = await state.get_data()

    # Удаляем сообщение с запросом адреса (бота)
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

    await state.update_data(address=address)  # Сохраняем адрес

    # Отправляем запрос на ввод суммы
    response_message = await message.answer("Теперь введите сумму для вывода:", reply_markup=cancel_check_menu())
    await state.update_data(amount_message_id=response_message.message_id)  # Сохраняем ID сообщения бота
    await state.set_state(WithdrawBTCState.waiting_for_amount)

# Обработчик для получения суммы
@btc_router.message(WithdrawBTCState.waiting_for_amount)
async def handle_withdraw_amount(message: types.Message, state: FSMContext):
    if message.text.startswith("/"):
        await message.answer("Пожалуйста, введите сумму, а не команду.")
        return
    
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

    await state.update_data(amount=amount)  # Сохраняем сумму
    
    # Подтверждение транзакции
    confirmation_message = await message.answer(
        f"Вы собираетесь отправить {amount} BTC на адрес {user_data['address']}.\n"
        f"Подтвердите отправку или отмените транзакцию.",
        reply_markup=confirm_cancel_menu(user_data['address'], amount)
    )
    await state.update_data(confirmation_message_id=confirmation_message.message_id)




def list_wallets():
    url = f"http://{BITCOIN_IP}:{BITCOIN_PORT}/"
    headers = {'content-type': 'text/plain;'}
    data = {
        "jsonrpc": "1.0",
        "id": "python_request",
        "method": "listwallets",
        "params": []
    }

    try:
        response = requests.post(url, auth=(BITCOIN_LOGIN, BITCOIN_PASSWORD), data=json.dumps(data), headers=headers)
        result = response.json()
        return result.get('result', [])
    except Exception as e:
        return f"Ошибка при запросе списка кошельков: {html.escape(str(e))}"
    

# Обработчик для подтверждения транзакции
@btc_router.callback_query(lambda call: call.data == 'confirm_withdraw_btc')
async def confirm_withdraw(callback_query: CallbackQuery, state: FSMContext, **kwargs):
    user_data = await state.get_data()

    address = user_data.get('address')
    amount = user_data.get('amount')

    if not address or not amount:
        await callback_query.message.answer("Ошибка: не удалось получить данные для транзакции.")
        return

    # Удаляем сообщение с подтверждением (бота)
    if "confirmation_message_id" in user_data:
        try:
            await callback_query.message.bot.delete_message(callback_query.message.chat.id, user_data['confirmation_message_id'])
        except Exception:
            pass


    # Проверка, что amount является числом
    try:
        amount = float(amount)
        if amount <= 0:
            await callback_query.message.answer("Ошибка: сумма должна быть положительным числом.")
            return
    except ValueError:
        await callback_query.message.answer("Ошибка: сумма имеет неверный формат.")
        return

    wallets = list_wallets()
    if not wallets:
        await callback_query.message.answer("Ошибка: ни один кошелек не загружен на ноде.")
        return

    wallet_name = wallets[0]

    url = f"http://{BITCOIN_IP}:{BITCOIN_PORT}/wallet/{wallet_name}"
    headers = {'content-type': 'text/plain;'}
    
    # Шаг 1: Получение рекомендованной комиссии
    fee_url = f"http://{BITCOIN_IP}:{BITCOIN_PORT}"
    fee_data = {
        "jsonrpc": "1.0",
        "id": "python_request",
        "method": "estimatesmartfee",
        "params": [6]  # Оценка комиссии для подтверждения за 6 блоков
    }
    try:
        fee_response = requests.post(fee_url, auth=(BITCOIN_LOGIN, BITCOIN_PASSWORD), data=json.dumps(fee_data), headers=headers)
        fee_result = fee_response.json()
        fee_rate = fee_result['result']['feerate'] if fee_result['result'] else None

        if not fee_rate:
            await callback_query.message.answer("Ошибка: не удалось получить данные о комиссии.")
            return
        
        # Шаг 2: Рассчитать сумму с учётом комиссии
        estimated_fee = fee_rate * 226 / 1000  # Оценка размера транзакции в байтах
        final_amount = round(amount - estimated_fee, 8)  # Округление суммы до 8 знаков после запятой

        if final_amount <= 0:
            await callback_query.message.answer("Ошибка: сумма слишком мала для покрытия комиссии.")
            return

        # Шаг 3: Отправка BTC с учётом комиссии
        send_data = {
            "jsonrpc": "1.0",
            "id": "python_request",
            "method": "sendtoaddress",
            "params": [address, final_amount]
        }
        send_response = requests.post(url, auth=(BITCOIN_LOGIN, BITCOIN_PASSWORD), data=json.dumps(send_data), headers=headers)
        send_result = send_response.json()

        if 'error' in send_result and send_result['error']:
            error_msg = send_result['error'].get('message', 'Неизвестная ошибка')
            await callback_query.message.answer(f"❌ Ошибка при отправке BTC: {error_msg}", reply_markup=btc_menu())
        else:
            txid = send_result.get('result', 'Не удалось получить TXID')
            await callback_query.message.answer(f"✅ BTC успешно отправлены! TXID: {txid}", reply_markup=btc_menu())
    except Exception as e:
        await callback_query.message.answer(f"❌ Ошибка при отправке BTC: {html.escape(str(e))}", reply_markup=btc_menu())

    await state.clear()




# Обработчик для команды /cancel и кнопки "Отмена"
@btc_router.message(Command("cancel"))
@btc_router.callback_query(lambda call: call.data == "cancel_check_address_btc")
async def cancel_withdraw(event: types.Message | CallbackQuery, state: FSMContext, **kwargs):
    await state.clear()
    if isinstance(event, CallbackQuery):
        await event.message.edit_text("Операция отменена.", reply_markup=main_menu())
    else:
        await event.answer("Операция отменена.", reply_markup=main_menu())


# Обработка callback query для биткоина и кнопок "Назад"
@btc_router.callback_query(lambda call: call.data in ["btc_menu", "btc_info", "btc_new_address", "back_to_main"])
@is_admin
async def btc_menu_handler(callback_query: CallbackQuery, **kwargs):
    if callback_query.data == "btc_menu":
        await callback_query.message.edit_text("BTC Menu:", reply_markup=btc_menu())
    elif callback_query.data == "btc_info":
        await get_btc_info(callback_query)
    elif callback_query.data == "btc_new_address":
        await show_wallets(callback_query)
    elif callback_query.data == "back_to_main":
        await callback_query.message.edit_text("Главное меню:", reply_markup=main_menu())

async def get_btc_info(callback_query: CallbackQuery, **kwargs):
    url = f"http://{BITCOIN_IP}:{BITCOIN_PORT}/"
    headers = {'content-type': 'text/plain;'}
    
    # Запрос для получения информации о блокчейне
    blockchain_info_data = {
        "jsonrpc": "1.0",
        "id": "python_request",
        "method": "getblockchaininfo",
        "params": []
    }

    # Запрос для получения баланса ноды
    balance_data = {
        "jsonrpc": "1.0",
        "id": "python_request",
        "method": "getbalance",
        "params": []
    }

    # Запрос для получения информации о сети, включая datadir
    network_info_data = {
        "jsonrpc": "1.0",
        "id": "python_request",
        "method": "getnetworkinfo",
        "params": []
    }

    try:
        # Запрашиваем информацию о блокчейне
        blockchain_info_response = requests.post(url, auth=(BITCOIN_LOGIN, BITCOIN_PASSWORD), data=json.dumps(blockchain_info_data), headers=headers)
        blockchain_info = blockchain_info_response.json()

        # Запрашиваем баланс ноды
        balance_response = requests.post(url, auth=(BITCOIN_LOGIN, BITCOIN_PASSWORD), data=json.dumps(balance_data), headers=headers)
        balance_info = balance_response.json()

        # Запрашиваем информацию о сети для получения datadir
        network_info_response = requests.post(url, auth=(BITCOIN_LOGIN, BITCOIN_PASSWORD), data=json.dumps(network_info_data), headers=headers)
        network_info = network_info_response.json()

        # Получаем баланс в биткоинах
        balance_btc = balance_info.get('result', 0.0) or 0.0

        # Запрашиваем текущий курс биткоина к доллару
        btc_to_usd = await get_btc_to_usd_rate()

        # Если курс не был получен, задаем его как 0
        btc_to_usd = btc_to_usd or 0.0

        # Конвертируем баланс в доллары
        balance_usd = balance_btc * btc_to_usd

        # Прогресс верификации и размер на диске
        verification_progress = blockchain_info['result'].get('verificationprogress', 0) * 100  # Прогресс в процентах
        size_on_disk_gb = blockchain_info['result'].get('size_on_disk', 0) / (1024 ** 3)  # Размер в гигабайтах
        error = blockchain_info.get('error', 'Нет ошибок')

        # Получаем путь к директории данных
        datadir = network_info['result'].get('datadir', 'Не удалось получить путь к директории данных')

        # Форматированный вывод
        formatted_info = (
            f"💻 <b>Информация о ноде биткоина:</b>\n\n"
            f"📊 <b>Верификация:</b> {verification_progress:.2f}%\n"
            f"💾 <b>Вес:</b> {size_on_disk_gb:.2f} GB\n"
            f"💰 <b>Баланс:</b> {balance_btc:.8f} BTC (~${balance_usd:,.2f})\n"
            f"📂 <b>Data Directory:</b> {html.escape(datadir)}\n"
            f"❌ <b>Ошибка:</b> {html.escape(str(error))}\n"
        )
    except Exception as e:
        formatted_info = f"Ошибка при запросе информации о ноде: {html.escape(str(e))}"

    await callback_query.message.edit_text(formatted_info, reply_markup=btc_menu(show_back_button=True), parse_mode=ParseMode.HTML)
    await callback_query.answer()


async def get_btc_to_usd_rate():
    try:
        response = requests.get("https://api.coindesk.com/v1/bpi/currentprice/BTC.json")
        result = response.json()
        btc_to_usd = result['bpi']['USD']['rate_float']
        return btc_to_usd
    except Exception as e:
        print(f"Ошибка при запросе курса BTC к USD: {e}")
        return 0  
    
# Функция для показа списка кошельков
async def show_wallets(callback_query: CallbackQuery, **kwargs):
    url = f"http://{BITCOIN_IP}:{BITCOIN_PORT}/"
    headers = {'content-type': 'text/plain;'}
    data = {
        "jsonrpc": "1.0",
        "id": "python_request",
        "method": "listwallets",
        "params": []
    }

    try:
        response = requests.post(url, auth=(BITCOIN_LOGIN, BITCOIN_PASSWORD), data=json.dumps(data), headers=headers)
        result = response.json()
        wallets = result.get('result', [])

        if wallets:

            await callback_query.message.edit_text("Выберите кошелек:", reply_markup=wallet_menu(wallets))
        else:

            await callback_query.message.edit_text("❌ <b>Кошельки не найдены!</b>\nЗагрузите кошелек или создайте новый.", reply_markup=btc_menu(show_back_button=True), parse_mode=ParseMode.HTML)
    except Exception as e:
        await callback_query.message.edit_text(f"Ошибка при получении списка кошельков: {html.escape(str(e))}", reply_markup=btc_menu(show_back_button=True), parse_mode=ParseMode.HTML)

# Обработчик для создания нового адреса в выбранном кошельке
@btc_router.callback_query(lambda call: call.data.startswith("wallet_create_address_"))
@is_admin
async def create_address_in_wallet_handler(callback_query: CallbackQuery, **kwargs):
    wallet_name = callback_query.data.split("wallet_create_address_")[1]

    url = f"http://{BITCOIN_IP}:{BITCOIN_PORT}/wallet/{wallet_name}" 
    headers = {'content-type': 'text/plain;'}
    data = {
        "jsonrpc": "1.0",
        "id": "python_request",
        "method": "getnewaddress", 
        "params": []
    }

    try:
        response = requests.post(url, auth=(BITCOIN_LOGIN, BITCOIN_PASSWORD), data=json.dumps(data), headers=headers)
        result = response.json()
        new_address = result.get('result', 'Не удалось создать новый адрес')

        formatted_info = (
            f"🏦 <b>Новый биткоин-адрес в кошельке {wallet_name}:</b>\n\n"
            f"🔑 <code>{new_address}</code>"
        )
    except Exception as e:
        formatted_info = f"Ошибка при создании нового адреса в кошельке {wallet_name}: {html.escape(str(e))}"

    await callback_query.message.edit_text(formatted_info, reply_markup=btc_menu(show_back_button=True), parse_mode=ParseMode.HTML)
    await callback_query.answer()
