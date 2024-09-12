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

ltc_router = Router()

# States for the LTC withdrawal process
class WithdrawLTCState(StatesGroup):
    waiting_for_address = State()
    waiting_for_amount = State()

# Handler for the Litecoin menu and "Back" buttons
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
        response_message = await callback_query.message.edit_text("Enter the LTC withdrawal address:", reply_markup=cancel_check_menu())
        await state.update_data(address_message_id=response_message.message_id)
        await state.set_state(WithdrawLTCState.waiting_for_address)
    elif callback_query.data == "back_to_main":
        await callback_query.message.edit_text("Main Menu:", reply_markup=main_menu())

# Fetch Litecoin node information
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
        datadir = blockchain_result['result'].get('datadir', 'Unknown')

        formatted_info = (
            f"💻 <b>Litecoin Node Info:</b>\n\n"
            f"📊 <b>Verification:</b> {verification_progress:.2f}%\n"
            f"💾 <b>Disk Size:</b> {size_on_disk_gb:.2f} GB\n"
            f"📂 <b>Data Directory:</b> {html.escape(datadir)}\n"
            f"💰 <b>Balance:</b> {balance_ltc:.8f} LTC (~${balance_usd:,.2f})\n"
        )
    except Exception as e:
        formatted_info = f"Error fetching node info: {html.escape(str(e))}"

    await callback_query.message.edit_text(formatted_info, reply_markup=ltc_menu(show_back_button=True), parse_mode=ParseMode.HTML)
    await callback_query.answer()

# Create a new Litecoin address
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
        
        new_address = result.get('result', 'Failed to create a new address')
        formatted_info = f"🏦 <b>New Litecoin Address:</b>\n\n🔑 <code>{new_address}</code>"
    except Exception as e:
        formatted_info = f"Error creating new address: {html.escape(str(e))}"

    await callback_query.message.edit_text(formatted_info, reply_markup=ltc_menu(show_back_button=True), parse_mode=ParseMode.HTML)
    await callback_query.answer()

# Handle receiving LTC withdrawal address
@ltc_router.message(WithdrawLTCState.waiting_for_address)
async def handle_withdraw_address(message: types.Message, state: FSMContext, **kwargs):
    address = message.text
    if not address:
        await message.answer("Invalid address, please enter again:")
        return

    user_data = await state.get_data()

    # Delete bot's previous message
    if "address_message_id" in user_data:
        try:
            await message.bot.delete_message(message.chat.id, user_data['address_message_id'])
        except Exception:
            pass

    # Delete user's message with the address
    try:
        await message.delete()
    except Exception:
        pass

    await state.update_data(address=address)

    # Request withdrawal amount
    response_message = await message.answer("Enter the withdrawal amount:", reply_markup=cancel_check_menu())
    await state.update_data(amount_message_id=response_message.message_id)
    await state.set_state(WithdrawLTCState.waiting_for_amount)

# Handle receiving LTC withdrawal amount
@ltc_router.message(WithdrawLTCState.waiting_for_amount)
async def handle_withdraw_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", "."))  
        if amount <= 0:
            raise ValueError("The amount must be positive.")
    except ValueError as e:
        await message.answer(f"Error: {str(e)}")
        return

    user_data = await state.get_data()

    # Delete bot's previous message asking for the amount
    if "amount_message_id" in user_data:
        try:
            await message.bot.delete_message(message.chat.id, user_data['amount_message_id'])
        except Exception:
            pass

    # Delete user's message with the amount
    try:
        await message.delete()
    except Exception:
        pass

    await state.update_data(amount=amount)

    # Confirmation message before sending LTC
    confirmation_message = await message.answer(
        f"You are about to send {amount} LTC to {user_data['address']}.\n"
        f"Please confirm or cancel the transaction.",
        reply_markup=confirm_cancel_menu()
    )
    await state.update_data(confirmation_message_id=confirmation_message.message_id)

# Handle transaction confirmation
@ltc_router.callback_query(lambda call: call.data == "confirm_withdraw_ltc")
async def confirm_withdraw_ltc(call: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()

    address = user_data.get('address')
    amount = user_data.get('amount')

    if not address or not amount:
        await call.message.answer("Error: Unable to retrieve transaction data.")
        return

    # Delete bot's confirmation message
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
        "params": [address, amount, "", "", True]  # True enables subtractfeefromamount
    }

    try:
        response = requests.post(url, auth=(LITECOIN_LOGIN, LITECOIN_PASSWORD), data=json.dumps(data), headers=headers)
        result = response.json()
        if 'error' in result and result['error']:
            error_msg = result['error'].get('message', 'Unknown error')
            await call.message.answer(f"❌ Error sending LTC: {error_msg}", reply_markup=ltc_menu())
        else:
            txid = result.get('result', 'Failed to retrieve TXID')
            await call.message.answer(f"✅ LTC successfully sent! TXID: {txid}", reply_markup=ltc_menu())
    except Exception as e:
        await call.message.answer(f"❌ Error sending LTC: {html.escape(str(e))}", reply_markup=ltc_menu())

    await state.clear()

# Handler to cancel the transaction
@ltc_router.callback_query(lambda call: call.data == "cancel_check_address_ltc")
async def cancel_check_address_ltc(call: CallbackQuery, state: FSMContext, **kwargs):
    await state.clear()
    await call.message.edit_text("Transaction cancelled.", reply_markup=ltc_menu())

# Fetch Litecoin to USD conversion rate
async def get_ltc_to_usd_rate():
    url = "https://api.coingecko.com/api/v3/simple/price?ids=litecoin&vs_currencies=usd"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return data["litecoin"]["usd"]
            else:
                return None
