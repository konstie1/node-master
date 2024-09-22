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

# States for XRP Withdrawal Process
class WithdrawXRPState(StatesGroup):
    waiting_for_sender_address = State()
    waiting_for_private_key = State()
    waiting_for_destination_address = State()
    waiting_for_amount = State()

# XRP Menu Handler
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

# Fetch XRP Node Information
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
            build_version = info.get("build_version", "Unknown")
            complete_ledgers = info.get("complete_ledgers", "Unknown")
            server_state = info.get("server_state", "Unknown")
            uptime = info.get("uptime", 0)
            ledger_seq = info.get("validated_ledger", {}).get("seq", "Unknown")

            formatted_info = (
                f"💻 <b>Ripple (XRP) Node Info:</b>\n\n"
                f"🌐 <b>Version:</b> {build_version}\n"
                f"📜 <b>Last Processed Ledgers:</b> {complete_ledgers}\n"
                f"⚙️ <b>Server State:</b> {server_state}\n"
                f"🕒 <b>Uptime (secs):</b> {uptime}\n"
                f"🔗 <b>Last Validated Ledger:</b> #{ledger_seq}\n"
            )
        else:
            formatted_info = "Error: Unable to fetch Ripple node information."
    except Exception as e:
        formatted_info = f"Error fetching node info: {html.escape(str(e))}"

    await callback_query.message.edit_text(formatted_info, reply_markup=back_to_xrp_menu(), parse_mode=ParseMode.HTML)
    await callback_query.answer()

# Generate a New XRP Address
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

        if 'result' in result and result['result']['status'] == 'success':
            wallet = result['result']
            address = wallet.get("account_id", "Unknown")
            public_key = wallet.get("public_key", "Unknown")
            master_key = wallet.get("master_key", "Unknown")
            master_seed = wallet.get("master_seed", "Unknown")

            formatted_address_info = (
                f"🆔 <b>Generated Address:</b>\n<code>{address}</code>\n\n"
                f"🔑 <b>Public Key:</b>\n<code>{public_key}</code>\n\n"
                f"🗝 <b>Master Key:</b>\n<code>{master_key}</code>\n\n"
                f"🌱 <b>Master Seed:</b>\n<code>{master_seed}</code>\n"
            )
        else:
            formatted_address_info = "Error: Failed to generate address. Server response: " + json.dumps(result)
    except Exception as e:
        formatted_address_info = f"Error generating address: {str(e)}"

    await callback_query.message.edit_text(formatted_address_info, reply_markup=back_to_xrp_menu(), parse_mode=ParseMode.HTML)
    await callback_query.answer()

# "Back" Button for XRP Menu
def back_to_xrp_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Back", callback_data="back_to_xrp_menu")]
    ])
    return keyboard

# Start the XRP Withdrawal Process
@xrp_router.callback_query(lambda call: call.data == "xrp_withdraw")
@is_admin
async def start_withdraw(callback_query: CallbackQuery, state: FSMContext, **kwargs):
    response_message = await callback_query.message.edit_text("Enter your XRP address:", reply_markup=cancel_check_menu())
    await state.update_data(address_message_id=response_message.message_id)
    await state.set_state(WithdrawXRPState.waiting_for_sender_address)

# Handle Sender Address Input
@xrp_router.message(WithdrawXRPState.waiting_for_sender_address)
async def handle_sender_address(message: types.Message, state: FSMContext, **kwargs):
    sender_address = message.text
    if not sender_address:
        await message.answer("Invalid address, please enter again:")
        return

    user_data = await state.get_data()
    if "address_message_id" in user_data:
        try:
            await message.bot.delete_message(message.chat.id, user_data['address_message_id'])
        except Exception as e:
            print(f"Error deleting address message: {e}")

    await message.delete()
    await state.update_data(sender_address=sender_address)

    response_message = await message.answer("Enter the private key for sending:", reply_markup=cancel_check_menu())
    await state.update_data(private_key_message_id=response_message.message_id)
    await state.set_state(WithdrawXRPState.waiting_for_private_key)

# Handle Private Key Input
@xrp_router.message(WithdrawXRPState.waiting_for_private_key)
async def handle_private_key(message: types.Message, state: FSMContext, **kwargs):
    private_key = message.text
    if not private_key:
        await message.answer("Invalid key, please enter again:")
        return

    user_data = await state.get_data()
    if "private_key_message_id" in user_data:
        try:
            await message.bot.delete_message(message.chat.id, user_data['private_key_message_id'])
        except Exception as e:
            print(f"Error deleting private key message: {e}")

    try:
        await message.delete()
    except Exception as e:
        print(f"Error deleting message: {e}")

    await state.update_data(private_key=private_key)

    response_message = await message.answer("Enter the recipient address:", reply_markup=cancel_check_menu())
    await state.update_data(destination_address_message_id=response_message.message_id)
    await state.set_state(WithdrawXRPState.waiting_for_destination_address)

# Handle Recipient Address Input
@xrp_router.message(WithdrawXRPState.waiting_for_destination_address)
async def handle_destination_address(message: types.Message, state: FSMContext, **kwargs):
    destination_address = message.text
    if not destination_address:
        await message.answer("Invalid address, please enter again:")
        return

    user_data = await state.get_data()
    if "destination_address_message_id" in user_data:
        try:
            await message.bot.delete_message(message.chat.id, user_data['destination_address_message_id'])
        except Exception as e:
            print(f"Error deleting destination address message: {e}")

    try:
        await message.delete()
    except Exception as e:
        print(f"Error deleting message: {e}")

    await state.update_data(destination_address=destination_address)

    response_message = await message.answer("Enter the amount to send:", reply_markup=cancel_check_menu())
    await state.update_data(amount_message_id=response_message.message_id)
    await state.set_state(WithdrawXRPState.waiting_for_amount)

# Handle Amount Input
@xrp_router.message(WithdrawXRPState.waiting_for_amount)
async def handle_amount(message: types.Message, state: FSMContext, **kwargs):
    try:
        amount = float(message.text.replace(",", "."))
        if amount <= 0:
            raise ValueError("The amount must be positive.")
    except ValueError as e:
        await message.answer(f"Error: {str(e)}")
        return

    user_data = await state.get_data()
    if "amount_message_id" in user_data:
        try:
            await message.bot.delete_message(message.chat.id, user_data['amount_message_id'])
        except Exception as e:
            print(f"Error deleting amount message: {e}")

    await message.delete()
    await state.update_data(amount=amount)

    confirmation_message = await message.answer(
        f"You are about to send {amount} XRP to {user_data['destination_address']}.\n"
        f"Please confirm or cancel the transaction.",
        reply_markup=confirm_cancel_menu(user_data['destination_address'], amount)
    )
    await state.update_data(confirmation_message_id=confirmation_message.message_id)

@xrp_router.callback_query(lambda call: call.data.startswith("confirm_withdraw_"))
async def confirm_withdraw(call: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()

    sender_address = user_data.get('sender_address')
    private_key = user_data.get('private_key')
    destination_address = user_data.get('destination_address')
    total_amount = user_data.get('amount')  # Сумма, которую отправитель указал

    if not sender_address or not private_key or not destination_address or not total_amount:
        await call.message.answer("Error: Missing transaction data.")
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
            fee_drops = int(fee_result['result']['drops']['open_ledger_fee'])  # Комиссия в дропах
        else:
            await call.message.answer(f"❌ Error fetching fee: {fee_result['result'].get('error_message', 'Unknown error')}", reply_markup=xrp_menu())
            return
    except Exception as e:
        await call.message.answer(f"❌ Error fetching fee: {html.escape(str(e))}", reply_markup=xrp_menu())
        return

    account_info_data = {
        "method": "account_info",
        "params": [{"account": sender_address}]
    }

    try:
        account_info_response = requests.post(url, data=json.dumps(account_info_data), headers=headers)
        account_info_result = account_info_response.json()

        if 'result' in account_info_result and 'account_data' in account_info_result['result']:
            balance_drops = int(account_info_result['result']['account_data']['Balance'])
            balance_xrp = balance_drops / 1_000_000  
            reserve_base_xrp = 10 
            available_balance_xrp = balance_xrp - reserve_base_xrp  

            total_needed_balance = total_amount + (fee_drops / 1_000_000)  
            if total_needed_balance > available_balance_xrp:
                total_amount = available_balance_xrp - (fee_drops / 1_000_000)

                if total_amount <= 0:
                    await call.message.answer(f"❌ Error: Not enough balance to cover the fee and reserve.", reply_markup=xrp_menu())
                    return

            amount_drops = int(total_amount * 1_000_000)

            transaction_data = {
                "method": "submit",
                "params": [{
                    "secret": private_key,
                    "tx_json": {
                        "TransactionType": "Payment",
                        "Account": sender_address,
                        "Amount": str(amount_drops),  
                        "Destination": destination_address,
                        "Fee": str(fee_drops)  
                    }
                }]
            }

            try:
                response = requests.post(url, data=json.dumps(transaction_data), headers=headers)
                result = response.json()

                if result.get('result', {}).get('status') == 'success':
                    tx_id = result['result'].get('tx_json', {}).get('hash', 'Failed to get TXID')
                    await call.message.answer(f"✅ XRP успешно отправлены! TXID: <code>{tx_id}</code>", reply_markup=back_to_xrp_menu(), parse_mode=ParseMode.HTML)
                else:
                    error_message = result['result'].get('error_message', 'Unknown error')
                    await call.message.answer(f"❌ Error sending XRP: {error_message}", reply_markup=back_to_xrp_menu())
            except Exception as e:
                await call.message.answer(f"❌ Error sending XRP: {html.escape(str(e))}", reply_markup=back_to_xrp_menu())
        else:
            await call.message.answer("❌ Error: Unable to fetch account balance.", reply_markup=back_to_xrp_menu())
            return
    except Exception as e:
        await call.message.answer(f"❌ Error fetching account info: {html.escape(str(e))}", reply_markup=back_to_xrp_menu())
        return

    user_data = await state.get_data()
    confirmation_message_id = user_data.get('confirmation_message_id')

    if confirmation_message_id:
        try:
            await call.bot.delete_message(call.message.chat.id, confirmation_message_id)
        except Exception as e:
            print(f"Error deleting confirmation message: {e}")

    await state.clear()

    try:
        await call.message.delete()
    except Exception as e:
        print(f"Error deleting confirmation message: {e}")


class WalletInfoState(StatesGroup):
    waiting_for_wallet_address = State()

@xrp_router.callback_query(lambda call: call.data == "xrp_wallet_info")
async def request_wallet_address(callback_query: CallbackQuery, state: FSMContext):

    cancel_menu = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_wallet_info_request")]
    ])
    
    response_message = await callback_query.message.edit_text(
        "Please enter the XRP wallet address:",
        reply_markup=cancel_menu
    )
    
    await state.update_data(response_message_id=response_message.message_id) 
    await state.set_state(WalletInfoState.waiting_for_wallet_address)

@xrp_router.callback_query(lambda call: call.data == "cancel_wallet_info_request")
async def cancel_wallet_info_request(callback_query: CallbackQuery, state: FSMContext):
    await state.clear() 
    await callback_query.message.edit_text("The request has been canceled.", reply_markup=back_to_xrp_menu())

@xrp_router.message(WalletInfoState.waiting_for_wallet_address)
async def handle_wallet_address(message: types.Message, state: FSMContext):
    wallet_address = message.text

    user_data = await state.get_data()
    if "response_message_id" in user_data:
        try:
            await message.bot.delete_message(message.chat.id, user_data['response_message_id'])
        except Exception:
            pass

    try:
        await message.delete()
    except Exception as e:
        print(f"Error deleting message: {e}")

    await get_wallet_info(message, wallet_address)
    await state.clear()

async def get_wallet_info(message: types.Message, wallet_address: str):
    url = f"http://{RIPPLE_IP}:{RIPPLE_PORT}/"
    headers = {'content-type': 'application/json'}
    
    data = {
        "method": "account_info",
        "params": [{"account": wallet_address}]
    }

    try:
        response = requests.post(url, auth=(RIPPLE_LOGIN, RIPPLE_PASSWORD), data=json.dumps(data), headers=headers)
        result = response.json()

        if 'result' in result and 'account_data' in result['result']:
            account_data = result['result']['account_data']
            balance = int(account_data['Balance']) / 1_000_000  # Конвертация из дропов в XRP
            formatted_info = (
                f"💼 <b>Wallet Info:</b>\n\n"
                f"🔑 <b>Address:</b> {wallet_address}\n"
                f"💰 <b>Balance:</b> {balance:.6f} XRP\n"
            )
        else:
            formatted_info = "Error: Unable to fetch wallet information."
    except Exception as e:
        formatted_info = f"Error fetching wallet info: {html.escape(str(e))}"

    await message.edit_text(formatted_info, reply_markup=back_to_xrp_menu(), parse_mode=ParseMode.HTML)

@xrp_router.callback_query(lambda call: call.data == "cancel_check_address")
async def cancel_withdraw(call: CallbackQuery, state: FSMContext, **kwargs):
    await state.clear()  # Очищаем состояние FSM
    await call.message.edit_text("Transaction cancelled.", reply_markup=back_to_xrp_menu())  # Обновляем сообщение и возвращаем в меню
