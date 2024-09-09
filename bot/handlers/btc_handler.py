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

# Обработчик нажатия кнопки "Вывести BTC"
@btc_router.callback_query(lambda call: call.data == "btc_withdraw")
@is_admin
async def start_withdraw(callback_query: CallbackQuery, state: FSMContext, **kwargs):
    await callback_query.message.edit_text("Введите адрес для вывода BTC:", reply_markup=cancel_check_menu())
    await state.set_state(WithdrawBTCState.waiting_for_address)

# Обработчик для получения адреса
@btc_router.message(WithdrawBTCState.waiting_for_address)
async def handle_withdraw_address(message: types.Message, state: FSMContext, **kwargs):
    address = message.text
    if not address:
        await message.answer("Некорректный адрес, пожалуйста введите снова:")
        return

    await state.update_data(address=address)  # Сохраняем адрес
    await message.answer("Теперь введите сумму для вывода:", reply_markup=cancel_check_menu())
    await state.set_state(WithdrawBTCState.waiting_for_amount)

# Обработчик для получения суммы
@btc_router.message(WithdrawBTCState.waiting_for_amount)
async def handle_withdraw_amount(message: types.Message, state: FSMContext):
    if message.text.startswith("/"):
        await message.answer("Пожалуйста, введите сумму, а не команду.")
        return
    
    try:
        # Принимаем как целые числа, так и числа с плавающей запятой
        amount = float(message.text.replace(",", "."))  # Заменяем запятые на точки для поддержки различных форматов
        if amount <= 0:
            raise ValueError("Сумма должна быть положительной.")  # Отклоняем суммы меньше или равные нулю
    except ValueError as e:
        # Отправляем сообщение с текстом ошибки
        await message.answer(f"Ошибка: {str(e)}")
        return

    await state.update_data(amount=amount)  # Сохраняем сумму
    user_data = await state.get_data()
    
    address = user_data.get('address')
    amount = user_data.get('amount')
    print(f"Адрес: {address}")
    print(f"Сумма: {amount}")

    # Подтверждение
    await message.answer(
        f"Вы собираетесь отправить {user_data['amount']} BTC на адрес {user_data['address']}.\n"
        f"Подтвердите отправку или отмените транзакцию.",
        reply_markup=confirm_cancel_menu()  # Используем меню с кнопкой подтверждения
    )

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


# Обработчик для подтверждения транзакции через кнопку
@btc_router.callback_query(lambda call: call.data == "confirm_withdraw")
async def confirm_withdraw(callback_query: CallbackQuery, state: FSMContext, **kwargs):
    user_data = await state.get_data()

    # Проверка наличия данных
    address = user_data.get('address')
    amount = user_data.get('amount')

    
    if not address or not amount:
        await callback_query.message.answer("Ошибка: не удалось получить данные для транзакции.")
        return

    # Проверим наличие загруженных кошельков
    wallets = list_wallets()
    if not wallets:
        await callback_query.message.answer("Ошибка: ни один кошелек не загружен на ноде.")
        return
    
    # Выбираем первый доступный кошелек
    wallet_name = wallets[0]  # Или укажите конкретный кошелек!!!!!!!!!!!!!!!!!!

    url = f"http://{BITCOIN_IP}:{BITCOIN_PORT}/wallet/{wallet_name}"
    headers = {'content-type': 'text/plain;'}
    data = {
        "jsonrpc": "1.0",
        "id": "python_request",
        "method": "sendtoaddress",
        "params": [address, amount]
    }
    try:
        response = requests.post(url, auth=(BITCOIN_LOGIN, BITCOIN_PASSWORD), data=json.dumps(data), headers=headers)
        result = response.json()
        
        if 'error' in result and result['error']:
            error_msg = result['error'].get('message', 'Неизвестная ошибка')
            await callback_query.message.answer(f"❌ Ошибка при отправке BTC: {error_msg}")
        else:
            txid = result.get('result', 'Не удалось получить TXID')
            await callback_query.message.answer(f"✅ BTC успешно отправлены! TXID: {txid}")
    except Exception as e:
        await callback_query.message.answer(f"❌ Ошибка при отправке BTC: {html.escape(str(e))}")
    
    await state.clear()  # Очищаем состояние после завершения транзакции



# Обработчик для команды /cancel и кнопки "Отмена"
@btc_router.message(Command("cancel"))
@btc_router.callback_query(lambda call: call.data == "cancel_check_address")
async def cancel_withdraw(event: types.Message | CallbackQuery, state: FSMContext, **kwargs):
    await state.clear()
    if isinstance(event, CallbackQuery):
        await event.message.edit_text("Операция отменена.", reply_markup=btc_menu())
    else:
        await event.answer("Операция отменена.", reply_markup=btc_menu())


# Обработка callback query для биткоина и кнопок "Назад"
@btc_router.callback_query(lambda call: call.data in ["btc_menu", "btc_info", "btc_new_address", "back_to_main"])
@is_admin
async def btc_menu_handler(callback_query: CallbackQuery, **kwargs):
    if callback_query.data == "btc_menu":
        # Показываем меню ноды биткоина
        await callback_query.message.edit_text("BTC Menu:", reply_markup=btc_menu())
    elif callback_query.data == "btc_info":
        # Показываем информацию о ноде биткоина
        await get_btc_info(callback_query)
    elif callback_query.data == "btc_new_address":
        # Показываем список кошельков для выбора
        await show_wallets(callback_query)
    elif callback_query.data == "back_to_main":
        # Возвращаем в главное меню
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

    try:
        # Запрашиваем информацию о блокчейне
        blockchain_info_response = requests.post(url, auth=(BITCOIN_LOGIN, BITCOIN_PASSWORD), data=json.dumps(blockchain_info_data), headers=headers)
        blockchain_info = blockchain_info_response.json()

        # Запрашиваем баланс ноды
        balance_response = requests.post(url, auth=(BITCOIN_LOGIN, BITCOIN_PASSWORD), data=json.dumps(balance_data), headers=headers)
        balance_info = balance_response.json()

        # Получаем баланс в биткоинах
        balance_btc = balance_info.get('result', 0)

        # Запрашиваем текущий курс биткоина к доллару
        btc_to_usd = await get_btc_to_usd_rate()

        # Конвертируем баланс в доллары
        balance_usd = balance_btc * btc_to_usd

        # Преобразование данных для красивого вывода
        verification_progress = blockchain_info['result'].get('verificationprogress', 0) * 100  # Прогресс в процентах
        size_on_disk_gb = blockchain_info['result'].get('size_on_disk', 0) / (1024 ** 3)  # Размер в гигабайтах
        error = blockchain_info.get('error', 'Нет ошибок')

        # Форматируем красивый вывод
        formatted_info = (
            f"💻 <b>Информация о ноде биткоина:</b>\n\n"
            f"📊 <b>Верификация:</b> {verification_progress:.2f}%\n"
            f"💾 <b>Вес:</b> {size_on_disk_gb:.2f} GB\n"
            f"💰 <b>Баланс:</b> {balance_btc:.8f} BTC (~${balance_usd:,.2f})\n"
            f"❌ <b>Ошибка:</b> {html.escape(str(error))}\n"
        )
    except Exception as e:
        formatted_info = f"Ошибка при запросе информации о ноде: {html.escape(str(e))}"

    # Редактируем сообщение с информацией и добавляем кнопку "Назад" в меню ноды
    await callback_query.message.edit_text(formatted_info, reply_markup=btc_menu(show_back_button=True), parse_mode=ParseMode.HTML)
    await callback_query.answer()

# Функция для запроса текущего курса биткоина к доллару
async def get_btc_to_usd_rate():
    try:
        response = requests.get("https://api.coindesk.com/v1/bpi/currentprice/BTC.json")
        result = response.json()
        btc_to_usd = result['bpi']['USD']['rate_float']
        return btc_to_usd
    except Exception as e:
        print(f"Ошибка при запросе курса BTC к USD: {e}")
        return 0  # Возвращаем 0, если не удалось получить курс

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
            # Если есть кошельки, выводим их как кнопки
            await callback_query.message.edit_text("Выберите кошелек:", reply_markup=wallet_menu(wallets))
        else:
            # Если нет кошельков, выводим сообщение и кнопку "Назад"
            await callback_query.message.edit_text("❌ <b>Кошельки не найдены!</b>\nЗагрузите кошелек или создайте новый.", reply_markup=btc_menu(show_back_button=True), parse_mode=ParseMode.HTML)
    except Exception as e:
        await callback_query.message.edit_text(f"Ошибка при получении списка кошельков: {html.escape(str(e))}", reply_markup=btc_menu(show_back_button=True), parse_mode=ParseMode.HTML)

# Обработчик для создания нового адреса в выбранном кошельке
@btc_router.callback_query(lambda call: call.data.startswith("wallet_create_address_"))
@is_admin
async def create_address_in_wallet_handler(callback_query: CallbackQuery, **kwargs):
    wallet_name = callback_query.data.split("wallet_create_address_")[1]

    url = f"http://{BITCOIN_IP}:{BITCOIN_PORT}/wallet/{wallet_name}"  # Используем кошелек
    headers = {'content-type': 'text/plain;'}
    data = {
        "jsonrpc": "1.0",
        "id": "python_request",
        "method": "getnewaddress",  # Генерация нового адреса
        "params": []
    }

    try:
        response = requests.post(url, auth=(BITCOIN_LOGIN, BITCOIN_PASSWORD), data=json.dumps(data), headers=headers)
        result = response.json()
        new_address = result.get('result', 'Не удалось создать новый адрес')

        # Отправляем пользователю новый адрес
        formatted_info = (
            f"🏦 <b>Новый биткоин-адрес в кошельке {wallet_name}:</b>\n\n"
            f"🔑 <code>{new_address}</code>"
        )
    except Exception as e:
        formatted_info = f"Ошибка при создании нового адреса в кошельке {wallet_name}: {html.escape(str(e))}"

    # Редактируем сообщение с новым адресом и добавляем кнопку "Назад" в меню ноды
    await callback_query.message.edit_text(formatted_info, reply_markup=btc_menu(show_back_button=True), parse_mode=ParseMode.HTML)
    await callback_query.answer()
