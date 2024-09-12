import requests
import json
import html
from aiogram import Router, types
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
from bot.menus.xrp_menu import back_to_xrp_menu, xrp_menu, cancel_check_menu, confirm_cancel_menu
from bot.filters.admin_filter import is_admin
from config.config import RIPPLE_IP, RIPPLE_PORT, RIPPLE_LOGIN, RIPPLE_PASSWORD
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

xrp_router = Router()

# Обработка callback query для XRP и кнопки "Назад"
@xrp_router.callback_query(lambda call: call.data in ["xrp_menu", "xrp_info", "xrp_generate_address", "back_to_xrp_menu"])
@is_admin
async def xrp_menu_handler(callback_query: CallbackQuery, state: FSMContext, **kwargs):
    if callback_query.data == "xrp_menu":
        await callback_query.message.edit_text("XRP Menu:", reply_markup=xrp_menu())
    elif callback_query.data == "xrp_info":
        await get_xrp_info(callback_query)
    elif callback_query.data == "xrp_generate_address":
        await generate_xrp_address(callback_query)
    elif callback_query.data == "back_to_xrp_menu":
        await callback_query.message.edit_text("XRP Menu:", reply_markup=xrp_menu())

# Получение информации о ноде XRP
async def get_xrp_info(callback_query: CallbackQuery, **kwargs):
    url = f"http://{RIPPLE_IP}:{RIPPLE_PORT}/"
    headers = {'content-type': 'application/json'}
    
    data = {
        "method": "server_info",
        "params": [{}]
    }

    try:
        response = requests.post(url, auth=(RIPPLE_LOGIN, RIPPLE_PASSWORD), data=json.dumps(data), headers=headers)
        result = response.json()

        if 'result' in result and 'info' in result['result']:
            info = result['result']['info']
            build_version = info.get("build_version", "Неизвестно")
            complete_ledgers = info.get("complete_ledgers", "Неизвестно")
            server_state = info.get("server_state", "Неизвестно")
            uptime = info.get("uptime", 0)
            ledger_seq = info.get("validated_ledger", {}).get("seq", "Неизвестно")

            formatted_info = (
                f"💻 <b>Информация о ноде Ripple (XRP):</b>\n\n"
                f"🌐 <b>Версия:</b> {build_version}\n"
                f"📜 <b>Последние обработанные блоки:</b> {complete_ledgers}\n"
                f"⚙️ <b>Состояние сервера:</b> {server_state}\n"
                f"🕒 <b>Время работы (сек):</b> {uptime}\n"
                f"🔗 <b>Последний валидированный блок:</b> #{ledger_seq}\n"
            )
        else:
            formatted_info = "Ошибка: Не удалось получить информацию о ноде Ripple."
    except Exception as e:
        formatted_info = f"Ошибка при запросе информации о ноде: {html.escape(str(e))}"

    # Отображаем информацию и добавляем кнопку "Назад"
    await callback_query.message.edit_text(formatted_info, reply_markup=back_to_xrp_menu(), parse_mode=ParseMode.HTML)
    await callback_query.answer()

# Генерация нового адреса XRP
async def generate_xrp_address(callback_query: CallbackQuery, **kwargs):
    url = f"http://{RIPPLE_IP}:{RIPPLE_PORT}/"
    headers = {'content-type': 'application/json'}
    
    data = {
        "method": "wallet_propose",
        "params": [{}]
    }

    try:
        response = requests.post(url, auth=(RIPPLE_LOGIN, RIPPLE_PASSWORD), data=json.dumps(data), headers=headers)
        result = response.json()

        if 'result' in result and 'account_id' in result['result']:
            address = result['result']['account_id']
            formatted_info = f"🎉 Новый адрес: `{address}`"
        else:
            formatted_info = "❌ Не удалось сгенерировать новый адрес."
    except Exception as e:
        formatted_info = f"Ошибка при генерации нового адреса: {html.escape(str(e))}"

    # Отображаем информацию и добавляем кнопку "Назад"
    await callback_query.message.edit_text(formatted_info, reply_markup=xrp_menu(), parse_mode=ParseMode.HTML)
    await callback_query.answer()


# Генерация нового адреса XRP
async def generate_xrp_address(callback_query: types.CallbackQuery, **kwargs):
    url = f"http://{RIPPLE_IP}:{RIPPLE_PORT}/"
    headers = {'content-type': 'application/json'}
    
    data = {
        "method": "wallet_propose",
        "params": [{}]
    }

    try:
        response = requests.post(url, auth=(RIPPLE_LOGIN, RIPPLE_PASSWORD), data=json.dumps(data), headers=headers)
        result = response.json()

        # Отладочные сообщения
        print("Response Status Code:", response.status_code)
        print("Response JSON:", result)

        if 'result' in result and result['result']['status'] == 'success':
            wallet = result['result']
            address = wallet.get("account_id", "Неизвестно")
            public_key = wallet.get("public_key", "Неизвестно")
            master_key = wallet.get("master_key", "Неизвестно")
            master_seed = wallet.get("master_seed", "Неизвестно")

            formatted_address_info = (
                f"🆔 <b>Сгенерированный адрес:</b> {address}\n"
                f"🔑 <b>Публичный ключ:</b> {public_key}\n"
                f"🗝 <b>Мастер-ключ:</b> {master_key}\n"
                f"🌱 <b>Мастер-Seed:</b> {master_seed}\n"
            )
        else:
            formatted_address_info = "Ошибка: Не удалось сгенерировать адрес. Ответ сервера: " + json.dumps(result)
    except Exception as e:
        formatted_address_info = f"Ошибка при запросе адреса: {str(e)}"

    # Отображаем информацию о адресе и добавляем кнопку "Назад"
    await callback_query.message.edit_text(formatted_address_info, reply_markup=xrp_menu(), parse_mode=ParseMode.HTML)
    await callback_query.answer()

# Генерация нового адреса XRP
async def generate_xrp_address(callback_query: types.CallbackQuery, **kwargs):
    url = f"http://{RIPPLE_IP}:{RIPPLE_PORT}/"
    headers = {'content-type': 'application/json'}
    
    data = {
        "method": "wallet_propose",
        "params": [{}]
    }

    try:
        response = requests.post(url, auth=(RIPPLE_LOGIN, RIPPLE_PASSWORD), data=json.dumps(data), headers=headers)
        result = response.json()

        if 'result' in result and result['result']['status'] == 'success':
            wallet = result['result']
            address = wallet.get("account_id", "Неизвестно")
            public_key = wallet.get("public_key", "Неизвестно")
            master_key = wallet.get("master_key", "Неизвестно")
            master_seed = wallet.get("master_seed", "Неизвестно")

            formatted_address_info = (
                f"🆔 <b>Сгенерированный адрес:</b>\n<code>{address}</code>\n\n"
                f"🔑 <b>Публичный ключ:</b>\n<code>{public_key}</code>\n\n"
                f"🗝 <b>Мастер-ключ:</b>\n<code>{master_key}</code>\n\n"
                f"🌱 <b>Мастер-Seed:</b>\n<code>{master_seed}</code>\n"
            )
        else:
            formatted_address_info = "Ошибка: Не удалось сгенерировать адрес. Ответ сервера: " + json.dumps(result)
    except Exception as e:
        formatted_address_info = f"Ошибка при запросе адреса: {str(e)}"

    # Отображаем информацию о адресе и добавляем кнопку "Назад"
    await callback_query.message.edit_text(formatted_address_info, reply_markup=back_to_xrp_menu(), parse_mode=ParseMode.HTML)
    await callback_query.answer()

# Кнопка "Назад" для возврата в меню XRP
def back_to_xrp_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_xrp_menu")]
    ])
    return keyboard



# Состояния для вывода XRP
class WithdrawXRPState(StatesGroup):
    waiting_for_sender_address = State()
    waiting_for_private_key = State()
    waiting_for_destination_address = State()
    waiting_for_amount = State()

# Начало процесса вывода XRP
@xrp_router.callback_query(lambda call: call.data == "xrp_withdraw")
@is_admin
async def start_withdraw(callback_query: CallbackQuery, state: FSMContext, **kwargs):
    response_message = await callback_query.message.edit_text("Введите ваш XRP адрес:", reply_markup=cancel_check_menu())
    await state.update_data(address_message_id=response_message.message_id)  # Сохраняем ID сообщения
    await state.set_state(WithdrawXRPState.waiting_for_sender_address)

# Ввод адреса отправителя
@xrp_router.message(WithdrawXRPState.waiting_for_sender_address)
async def handle_sender_address(message: types.Message, state: FSMContext, **kwargs):
    sender_address = message.text
    if not sender_address:
        await message.answer("Некорректный адрес, пожалуйста, введите снова:")
        return

    # Удаляем сообщения
    user_data = await state.get_data()
    if "address_message_id" in user_data:
        try:
            await message.bot.delete_message(message.chat.id, user_data['address_message_id'])
        except Exception:
            pass

    await message.delete()

    await state.update_data(sender_address=sender_address)

    # Запрос на ввод приватного ключа
    response_message = await message.answer("Теперь введите приватный ключ для отправки:", reply_markup=cancel_check_menu())
    await state.update_data(private_key_message_id=response_message.message_id)
    await state.set_state(WithdrawXRPState.waiting_for_private_key)

# Ввод суммы
@xrp_router.message(WithdrawXRPState.waiting_for_amount)
async def handle_amount(message: types.Message, state: FSMContext, **kwargs):
    try:
        amount = float(message.text.replace(",", "."))
        if amount <= 0:
            raise ValueError("Сумма должна быть положительной.")
    except ValueError as e:
        await message.answer(f"Ошибка: {str(e)}")
        return

    # Удаляем сообщение с запросом суммы
    user_data = await state.get_data()
    if "amount_message_id" in user_data:
        try:
            await message.bot.delete_message(message.chat.id, user_data['amount_message_id'])
        except Exception:
            pass

    await message.delete()

    await state.update_data(amount=amount)

    # Подтверждение транзакции
    confirmation_message = await message.answer(
        f"Вы собираетесь отправить {amount} XRP на адрес {user_data['destination_address']}.\n"
        f"Подтвердите отправку или отмените транзакцию.",
        reply_markup=confirm_cancel_menu(user_data['destination_address'], amount)
    )
    await state.update_data(confirmation_message_id=confirmation_message.message_id)

# Ввод приватного ключа
@xrp_router.message(WithdrawXRPState.waiting_for_private_key)
async def handle_private_key(message: types.Message, state: FSMContext, **kwargs):
    private_key = message.text
    if not private_key:
        await message.answer("Некорректный ключ, пожалуйста, введите снова:")
        return

    # Удаляем сообщение с запросом приватного ключа
    user_data = await state.get_data()
    if "private_key_message_id" in user_data:
        try:
            await message.bot.delete_message(message.chat.id, user_data['private_key_message_id'])
        except Exception:
            pass

    # Удаляем сообщение пользователя с ключом
    try:
        await message.delete()
    except Exception:
        pass

    await state.update_data(private_key=private_key)

    # Запрос на ввод адреса получателя
    response_message = await message.answer("Введите адрес получателя:", reply_markup=cancel_check_menu())
    await state.update_data(destination_address_message_id=response_message.message_id)
    await state.set_state(WithdrawXRPState.waiting_for_destination_address)

# Ввод адреса получателя
@xrp_router.message(WithdrawXRPState.waiting_for_destination_address)
async def handle_destination_address(message: types.Message, state: FSMContext, **kwargs):
    destination_address = message.text
    if not destination_address:
        await message.answer("Некорректный адрес, пожалуйста, введите снова:")
        return

    # Удаляем сообщение с запросом адреса получателя
    user_data = await state.get_data()
    if "destination_address_message_id" in user_data:
        try:
            await message.bot.delete_message(message.chat.id, user_data['destination_address_message_id'])
        except Exception:
            pass

    # Удаляем сообщение пользователя с введенным адресом
    try:
        await message.delete()
    except Exception:
        pass

    # Сохраняем адрес получателя
    await state.update_data(destination_address=destination_address)

    # Запрос на ввод суммы
    response_message = await message.answer("Введите сумму для отправки:", reply_markup=cancel_check_menu())
    await state.update_data(amount_message_id=response_message.message_id)
    await state.set_state(WithdrawXRPState.waiting_for_amount)


# Обработчик подтверждения транзакции
@xrp_router.callback_query(lambda call: call.data.startswith("confirm_withdraw_"))
async def confirm_withdraw(call: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()

    sender_address = user_data.get('sender_address')
    private_key = user_data.get('private_key')
    destination_address = user_data.get('destination_address')
    amount = user_data.get('amount')

    if not sender_address or not private_key or not destination_address or not amount:
        await call.message.answer("Ошибка: не удалось получить данные для транзакции.")
        return

    url = f"http://{RIPPLE_IP}:{RIPPLE_PORT}/"
    headers = {'content-type': 'application/json'}

    # Шаг 1: Получаем текущую минимальную комиссию (fee)
    fee_data = {
        "method": "fee",
        "params": [{}]
    }

    try:
        fee_response = requests.post(url, data=json.dumps(fee_data), headers=headers)
        fee_result = fee_response.json()

        if fee_result.get('result', {}).get('status') == 'success':
            fee = fee_result['result']['drops']['open_ledger_fee']
        else:
            await call.message.answer(f"❌ Ошибка при получении комиссии: {fee_result['result'].get('error_message', 'Неизвестная ошибка')}", reply_markup=xrp_menu())
            return

    except Exception as e:
        await call.message.answer(f"❌ Ошибка при получении комиссии: {html.escape(str(e))}", reply_markup=xrp_menu())
        return

    # Шаг 2: Формируем транзакцию для отправки XRP
    transaction_data = {
        "method": "submit",
        "params": [{
            "secret": private_key,
            "tx_json": {
                "TransactionType": "Payment",
                "Account": sender_address,
                "Amount": str(int(amount * 1_000_000)),  # Конвертируем сумму в дропы (1 XRP = 1,000,000 дропов)
                "Destination": destination_address,
                "Fee": fee  # Явно указываем комиссию
            }
        }]
    }

    try:
        response = requests.post(url, data=json.dumps(transaction_data), headers=headers)
        result = response.json()

        if result.get('result', {}).get('status') == 'success':
            tx_id = result['result'].get('tx_json', {}).get('hash', 'Не удалось получить TXID')
            await call.message.answer(f"✅ XRP успешно отправлены! TXID: <code>{tx_id}</code>", reply_markup=xrp_menu(), parse_mode=ParseMode.HTML)
        else:
            error_message = result['result'].get('error_message', 'Неизвестная ошибка')
            await call.message.answer(f"❌ Ошибка при отправке XRP: {error_message}", reply_markup=xrp_menu())
    except Exception as e:
        await call.message.answer(f"❌ Ошибка при отправке XRP: {html.escape(str(e))}", reply_markup=xrp_menu())

    await state.clear()

# Обработчик отмены транзакции
@xrp_router.callback_query(lambda call: call.data == "cancel_check_address")
async def cancel_withdraw(call: CallbackQuery, state: FSMContext, **kwargs):
    await state.clear()
    await call.message.edit_text("Операция отменена.", reply_markup=xrp_menu())