import requests
import json
import html
from aiogram import Router, types
from aiogram.types import CallbackQuery
from aiogram.enums import ParseMode
from bot.menus.btc_menu import btc_menu, wallet_menu, cancel_check_menu, confirm_cancel_menu
from bot.menus.main_menu import main_menu
from bot.filters.admin_filter import is_admin
from config.config import BITCOIN_IP, BITCOIN_PORT, BITCOIN_LOGIN, BITCOIN_PASSWORD
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

btc_router = Router()

# States for the BTC withdrawal process
class WithdrawBTCState(StatesGroup):
    waiting_for_address = State()
    waiting_for_amount = State()

# Handler for the "Withdraw BTC" button click
@btc_router.callback_query(lambda call: call.data == "btc_withdraw")
@is_admin
async def start_withdraw(callback_query: CallbackQuery, state: FSMContext, **kwargs):
    # Request BTC withdrawal address
    response_message = await callback_query.message.edit_text("Enter the BTC withdrawal address:", reply_markup=cancel_check_menu())
    await state.update_data(address_message_id=response_message.message_id)  # Save the bot message ID
    await state.set_state(WithdrawBTCState.waiting_for_address)

# Handler for receiving the BTC withdrawal address
@btc_router.message(WithdrawBTCState.waiting_for_address)
async def handle_withdraw_address(message: types.Message, state: FSMContext, **kwargs):
    address = message.text
    if not address:
        await message.answer("Invalid address, please enter again:")
        return

    user_data = await state.get_data()

    # Delete bot's previous message asking for the address
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

    await state.update_data(address=address)  # Save the address

    # Request the withdrawal amount
    response_message = await message.answer("Enter the withdrawal amount:", reply_markup=cancel_check_menu())
    await state.update_data(amount_message_id=response_message.message_id)  # Save the bot message ID
    await state.set_state(WithdrawBTCState.waiting_for_amount)

# Handler for receiving the BTC withdrawal amount
@btc_router.message(WithdrawBTCState.waiting_for_amount)
async def handle_withdraw_amount(message: types.Message, state: FSMContext):
    if message.text.startswith("/"):
        await message.answer("Please enter an amount, not a command.")
        return
    
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

    await state.update_data(amount=amount)  # Save the amount

    # Confirmation message before sending BTC
    confirmation_message = await message.answer(
        f"You are about to send {amount} BTC to the address {user_data['address']}.\n"
        f"Please confirm or cancel the transaction.",
        reply_markup=confirm_cancel_menu(user_data['address'], amount)
    )
    await state.update_data(confirmation_message_id=confirmation_message.message_id)

# Function to list Bitcoin wallets
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
        return f"Error fetching wallet list: {html.escape(str(e))}"

# Handler for transaction confirmation
@btc_router.callback_query(lambda call: call.data == 'confirm_withdraw_btc')
async def confirm_withdraw(callback_query: CallbackQuery, state: FSMContext, **kwargs):
    user_data = await state.get_data()

    address = user_data.get('address')
    amount = user_data.get('amount')

    if not address or not amount:
        await callback_query.message.answer("Error: Unable to retrieve transaction data.")
        return

    # Delete confirmation message (from bot)
    if "confirmation_message_id" in user_data:
        try:
            await callback_query.message.bot.delete_message(callback_query.message.chat.id, user_data['confirmation_message_id'])
        except Exception:
            pass

    # Check if the amount is a valid number
    try:
        amount = float(amount)
        if amount <= 0:
            await callback_query.message.answer("Error: The amount must be a positive number.")
            return
    except ValueError:
        await callback_query.message.answer("Error: Invalid amount format.")
        return

    wallets = list_wallets()
    if not wallets:
        await callback_query.message.answer("Error: No wallets loaded on the node.")
        return

    wallet_name = wallets[0]

    url = f"http://{BITCOIN_IP}:{BITCOIN_PORT}/wallet/{wallet_name}"
    headers = {'content-type': 'text/plain;'}
    
    # Step 1: Get recommended transaction fee
    fee_url = f"http://{BITCOIN_IP}:{BITCOIN_PORT}"
    fee_data = {
        "jsonrpc": "1.0",
        "id": "python_request",
        "method": "estimatesmartfee",
        "params": [6]  # Estimate fee for confirmation in 6 blocks
    }
    try:
        fee_response = requests.post(fee_url, auth=(BITCOIN_LOGIN, BITCOIN_PASSWORD), data=json.dumps(fee_data), headers=headers)
        fee_result = fee_response.json()
        fee_rate = fee_result['result']['feerate'] if fee_result['result'] else None

        if not fee_rate:
            await callback_query.message.answer("Error: Unable to get fee data.")
            return
        
        # Step 2: Calculate final amount including fee
        estimated_fee = fee_rate * 226 / 1000  # Estimated transaction size in bytes
        final_amount = round(amount - estimated_fee, 8)  # Round to 8 decimal places

        if final_amount <= 0:
            await callback_query.message.answer("Error: Amount too small to cover the fee.")
            return

        # Step 3: Send BTC with fee
        send_data = {
            "jsonrpc": "1.0",
            "id": "python_request",
            "method": "sendtoaddress",
            "params": [address, final_amount]
        }
        send_response = requests.post(url, auth=(BITCOIN_LOGIN, BITCOIN_PASSWORD), data=json.dumps(send_data), headers=headers)
        send_result = send_response.json()

        if 'error' in send_result and send_result['error']:
            error_msg = send_result['error'].get('message', 'Unknown error')
            await callback_query.message.answer(f"❌ Error sending BTC: {error_msg}", reply_markup=btc_menu())
        else:
            txid = send_result.get('result', 'Failed to retrieve TXID')
            await callback_query.message.answer(f"✅ BTC successfully sent! TXID: {txid}", reply_markup=btc_menu())
    except Exception as e:
        await callback_query.message.answer(f"❌ Error sending BTC: {html.escape(str(e))}", reply_markup=btc_menu())

    await state.clear()

# Handler for /cancel command and "Cancel" button
@btc_router.message(Command("cancel"))
@btc_router.callback_query(lambda call: call.data == "cancel_check_address_btc")
async def cancel_withdraw(event: types.Message | CallbackQuery, state: FSMContext, **kwargs):
    await state.clear()
    if isinstance(event, CallbackQuery):
        await event.message.edit_text("Operation cancelled.", reply_markup=main_menu())
    else:
        await event.answer("Operation cancelled.", reply_markup=main_menu())

# Handler for BTC menu buttons
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
        await callback_query.message.edit_text("Main Menu:", reply_markup=main_menu())

# Function to fetch Bitcoin blockchain info and node balance
async def get_btc_info(callback_query: CallbackQuery, **kwargs):
    url = f"http://{BITCOIN_IP}:{BITCOIN_PORT}/"
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

    network_info_data = {
        "jsonrpc": "1.0",
        "id": "python_request",
        "method": "getnetworkinfo",
        "params": []
    }

    try:
        blockchain_info_response = requests.post(url, auth=(BITCOIN_LOGIN, BITCOIN_PASSWORD), data=json.dumps(blockchain_info_data), headers=headers)
        blockchain_info = blockchain_info_response.json()

        balance_response = requests.post(url, auth=(BITCOIN_LOGIN, BITCOIN_PASSWORD), data=json.dumps(balance_data), headers=headers)
        balance_info = balance_response.json()

        network_info_response = requests.post(url, auth=(BITCOIN_LOGIN, BITCOIN_PASSWORD), data=json.dumps(network_info_data), headers=headers)
        network_info = network_info_response.json()

        balance_btc = balance_info.get('result', 0.0) or 0.0

        btc_to_usd = await get_btc_to_usd_rate()
        btc_to_usd = btc_to_usd or 0.0

        balance_usd = balance_btc * btc_to_usd

        verification_progress = blockchain_info['result'].get('verificationprogress', 0) * 100  # Progress in %
        size_on_disk_gb = blockchain_info['result'].get('size_on_disk', 0) / (1024 ** 3)  # Size in GB
        error = blockchain_info.get('error', 'No errors')

        datadir = network_info['result'].get('datadir', 'Unable to retrieve data directory path')

        formatted_info = (
            f"💻 <b>Bitcoin Node Info:</b>\n\n"
            f"📊 <b>Verification:</b> {verification_progress:.2f}%\n"
            f"💾 <b>Disk Size:</b> {size_on_disk_gb:.2f} GB\n"
            f"💰 <b>Balance:</b> {balance_btc:.8f} BTC (~${balance_usd:,.2f})\n"
            f"📂 <b>Data Directory:</b> {html.escape(datadir)}\n"
            f"❌ <b>Error:</b> {html.escape(str(error))}\n"
        )
    except Exception as e:
        formatted_info = f"Error fetching node information: {html.escape(str(e))}"

    await callback_query.message.edit_text(formatted_info, reply_markup=btc_menu(show_back_button=True), parse_mode=ParseMode.HTML)
    await callback_query.answer()

# Function to get BTC to USD conversion rate
async def get_btc_to_usd_rate():
    try:
        response = requests.get("https://api.coindesk.com/v1/bpi/currentprice/BTC.json")
        result = response.json()
        btc_to_usd = result['bpi']['USD']['rate_float']
        return btc_to_usd
    except Exception as e:
        print(f"Error fetching BTC to USD rate: {e}")
        return 0  

# Function to show wallet list
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
            await callback_query.message.edit_text("Choose a wallet:", reply_markup=wallet_menu(wallets))
        else:
            await callback_query.message.edit_text("❌ <b>No wallets found!</b>\nLoad or create a new wallet.", reply_markup=btc_menu(show_back_button=True), parse_mode=ParseMode.HTML)
    except Exception as e:
        await callback_query.message.edit_text(f"Error fetching wallet list: {html.escape(str(e))}", reply_markup=btc_menu(show_back_button=True), parse_mode=ParseMode.HTML)

# Handler for creating a new address in the selected wallet
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
        new_address = result.get('result', 'Failed to create new address')

        formatted_info = (
            f"🏦 <b>New Bitcoin address in wallet {wallet_name}:</b>\n\n"
            f"🔑 <code>{new_address}</code>"
        )
    except Exception as e:
        formatted_info = f"Error creating new address in wallet {wallet_name}: {html.escape(str(e))}"

    await callback_query.message.edit_text(formatted_info, reply_markup=btc_menu(show_back_button=True), parse_mode=ParseMode.HTML)
    await callback_query.answer()
