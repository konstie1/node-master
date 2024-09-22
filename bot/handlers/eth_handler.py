from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from eth_account import Account
from web3 import Web3
import requests
from bot.filters.admin_filter import is_admin
from config.config import ETHEREUM_IP, ETHEREUM_PORT, ETHEREUM_LOGIN, ETHEREUM_PASSWORD
from bot.menus.eth_menu import eth_menu, eth_info_menu, eth_generate_menu, eth_back_to_eth_menu, eth_confirm_cancel_menu, eth_cancel_check_menu, eth_back_to_eth_menu
from bot.menus.main_menu import main_menu
import html

eth_router = Router()

# States for ETH Withdrawal Process
class eth_WithdrawETHState(StatesGroup):
    eth_waiting_for_sender_address = State()
    eth_waiting_for_private_key = State()
    eth_waiting_for_destination_address = State()
    eth_waiting_for_amount = State()

# States for Ethereum Address Generation
class eth_GenerateAddressState(StatesGroup):
    eth_waiting_for_password = State()

# Ethereum Menu Handler
@eth_router.callback_query(lambda call: call.data in ["eth_menu", "eth_info", "eth_generate", "eth_back_to_eth_menu", "eth_back_to_main", "eth_withdraw", "eth_back_to_eth_menu"])
@is_admin
async def eth_menu_handler(callback_query: CallbackQuery, state: FSMContext, **kwargs):
    if callback_query.data == "eth_menu":
        await callback_query.message.edit_text("ETH Menu:", reply_markup=eth_menu())
    elif callback_query.data == "eth_withdraw":
        await eth_start_withdraw(callback_query, state)
    if callback_query.data == "eth_menu":
        await callback_query.message.edit_text("Ethereum Menu:", reply_markup=eth_menu())
    elif callback_query.data == "eth_info":
        await eth_get_eth_info(callback_query)
    elif callback_query.data == "eth_generate":
        await eth_prompt_for_password(callback_query, state)
    elif callback_query.data == "eth_back_to_eth_menu":
        await callback_query.message.edit_text("Ethereum Menu:", reply_markup=eth_menu())

    elif callback_query.data == "eth_back_to_main":
        # Handler for going back to the main menu (assuming it is implemented elsewhere)
        await callback_query.message.edit_text("Main Menu:", reply_markup=main_menu())  # Replace with actual main menu function
    else:
        await callback_query.answer("Unknown command")

# Prompt for Password to Generate New Address
async def eth_prompt_for_password(callback_query: CallbackQuery, state: FSMContext, **kwargs):
    response_message = await callback_query.message.edit_text(
        "Please enter a password to generate a new Ethereum address:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Cancel", callback_data="eth_cancel_generate")]
        ])
    )
    await state.set_state(eth_GenerateAddressState.eth_waiting_for_password)
    await state.update_data(message_id=response_message.message_id)

# Generate a New Ethereum Address
@eth_router.message(eth_GenerateAddressState.eth_waiting_for_password)
async def eth_generate_eth_address(message: types.Message, state: FSMContext, **kwargs):
    password = message.text

    # Generate new Ethereum address using web3.py
    new_account = Account.create()
    address = new_account.address
    private_key = new_account.key.hex()  # Use the correct attribute

    formatted_address_info = (
        f"🆔 <b>Generated Address:</b>\n<code>{address}</code>\n\n"
        f"🔑 <b>Private Key:</b>\n<code>{private_key}</code>\n\n"
        f"🔐 <b>Note:</b> Ensure you keep the private key safe as it is required to manage this account."
    )

    # Delete the prompt message and user message, then send the address info
    state_data = await state.get_data()
    prompt_message_id = state_data.get("message_id")
    if prompt_message_id:
        await message.bot.delete_message(chat_id=message.chat.id, message_id=prompt_message_id)

    # Delete the user's message with the password
    await message.delete()

    # Send the generated address info
    await message.answer(formatted_address_info, reply_markup=eth_back_to_eth_menu(), parse_mode=ParseMode.HTML)

    await state.clear()

# Cancel Address Generation Request
@eth_router.callback_query(lambda call: call.data == "eth_cancel_generate")
async def eth_cancel_generate(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("Address generation canceled.", reply_markup=eth_menu())

# Fetch Ethereum Node Information
@eth_router.callback_query(lambda call: call.data == "eth_info")
async def eth_get_eth_info(callback_query: CallbackQuery, **kwargs):
    url = f"http://{ETHEREUM_IP}:{ETHEREUM_PORT}"
    headers = {'Content-Type': 'application/json'}

    # Define JSON-RPC methods to fetch node information
    methods = {
        "web3_clientVersion": "Client Version",
        "eth_blockNumber": "Latest Block Number",
        "eth_chainId": "Chain ID",
        "net_version": "Network Version",
        "net_peerCount": "Peer Count"
    }

    results = {}
    for method, label in methods.items():
        data = {
            "jsonrpc": "2.0",
            "method": method,
            "params": [],
            "id": 1
        }

        try:
            response = requests.post(url, auth=(ETHEREUM_LOGIN, ETHEREUM_PASSWORD), json=data, headers=headers)
            result = response.json()
            if 'result' in result:
                # Convert hex numbers to decimal where applicable
                if result['result'].startswith('0x'):
                    results[label] = int(result['result'], 16)
                else:
                    results[label] = result['result']
            else:
                results[label] = "Error fetching data"
        except Exception as e:
            results[label] = f"Error: {str(e)}"

    # Web3 setup to check sync status
    w3 = Web3(Web3.HTTPProvider(url))

    # Fetch the synchronization status
    sync_status = w3.eth.syncing
    if sync_status:
        # Node is still syncing
        starting_block = sync_status['startingBlock']
        current_block = sync_status['currentBlock']
        highest_block = sync_status['highestBlock']

        # Convert blocks to decimal if they are in hex format
        starting_block = int(starting_block, 16) if isinstance(starting_block, str) and starting_block.startswith('0x') else starting_block
        current_block = int(current_block, 16) if isinstance(current_block, str) and current_block.startswith('0x') else current_block
        highest_block = int(highest_block, 16) if isinstance(highest_block, str) and highest_block.startswith('0x') else highest_block

        # Calculate sync progress
        if highest_block != 0 and highest_block != 2**64 - 1:
            sync_progress = 100 * current_block / highest_block
        else:
            sync_progress = 0.0

        sync_message = (f"🔄 <b>Node is syncing</b>:\n"
                        f"Starting block: {starting_block}\n"
                        f"Current block: {current_block}\n"
                        f"Highest block: {highest_block}\n"
                        f"Sync progress: {sync_progress:.2f}%")
    else:
        # Node is fully synced
        current_block = w3.eth.block_number
        sync_message = f"✅ <b>Node is fully synced</b>. Current block: {current_block}"

    # Format the node information along with the sync status
    formatted_info = (
        f"💻 <b>Ethereum Node Information:</b>\n\n"
        f"🌐 <b>Client Version:</b> {results['Client Version']}\n"
        f"🆙 <b>Latest Block Number:</b> {results['Latest Block Number']}\n"
        f"🔗 <b>Chain ID:</b> {results['Chain ID']}\n"
        f"🌍 <b>Network Version:</b> {results['Network Version']}\n"
        f"👥 <b>Peer Count:</b> {results['Peer Count']}\n\n"
        f"{sync_message}"
    )

    await callback_query.message.edit_text(formatted_info, reply_markup=eth_back_to_eth_menu(), parse_mode=ParseMode.HTML)
    await callback_query.answer()


# Start the ETH Withdrawal Process
async def eth_start_withdraw(callback_query: CallbackQuery, state: FSMContext, **kwargs):
    response_message = await callback_query.message.edit_text("Enter your ETH address:", reply_markup=eth_cancel_check_menu())
    await state.update_data(address_message_id=response_message.message_id)
    await state.set_state(eth_WithdrawETHState.eth_waiting_for_sender_address)

# Handle Sender Address Input
@eth_router.message(eth_WithdrawETHState.eth_waiting_for_sender_address)
async def eth_handle_sender_address(message: types.Message, state: FSMContext, **kwargs):
    sender_address = message.text
    if not Web3.is_address(sender_address):
        await message.answer("Invalid Ethereum address, please enter again:")
        return

    user_data = await state.get_data()
    if "address_message_id" in user_data:
        try:
            await message.bot.delete_message(message.chat.id, user_data['address_message_id'])
        except Exception as e:
            print(f"Error deleting address message: {e}")

    await message.delete()
    await state.update_data(sender_address=sender_address)

    response_message = await message.answer("Enter the private key for sending:", reply_markup=eth_cancel_check_menu())
    await state.update_data(private_key_message_id=response_message.message_id)
    await state.set_state(eth_WithdrawETHState.eth_waiting_for_private_key)

# Handle Private Key Input
@eth_router.message(eth_WithdrawETHState.eth_waiting_for_private_key)
async def eth_handle_private_key(message: types.Message, state: FSMContext, **kwargs):
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

    response_message = await message.answer("Enter the recipient address:", reply_markup=eth_cancel_check_menu())
    await state.update_data(destination_address_message_id=response_message.message_id)
    await state.set_state(eth_WithdrawETHState.eth_waiting_for_destination_address)

# Handle Recipient Address Input
@eth_router.message(eth_WithdrawETHState.eth_waiting_for_destination_address)
async def eth_handle_destination_address(message: types.Message, state: FSMContext, **kwargs):
    destination_address = message.text
    if not Web3.is_address(destination_address):
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

    response_message = await message.answer("Enter the amount to send:", reply_markup=eth_cancel_check_menu())
    await state.update_data(amount_message_id=response_message.message_id)
    await state.set_state(eth_WithdrawETHState.eth_waiting_for_amount)

# Handle Amount Input
@eth_router.message(eth_WithdrawETHState.eth_waiting_for_amount)
async def eth_handle_amount(message: types.Message, state: FSMContext, **kwargs):
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
        f"You are about to send {amount} ETH to {user_data['destination_address']}.\n"
        f"Please confirm or cancel the transaction.",
        reply_markup=eth_confirm_cancel_menu()
    )
    await state.update_data(confirmation_message_id=confirmation_message.message_id)


@eth_router.callback_query(lambda call: call.data == "eth_confirm_withdraw_eth")
async def eth_confirm_withdraw(call: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()

    sender_address = user_data.get('sender_address')
    private_key = user_data.get('private_key')
    destination_address = user_data.get('destination_address')
    total_amount = user_data.get('amount')

    if not sender_address or not private_key or not destination_address or not total_amount:
        await call.message.answer("Error: Missing transaction data.")
        return

    # Web3 setup to send transaction
    w3 = Web3(Web3.HTTPProvider(f"http://{ETHEREUM_IP}:{ETHEREUM_PORT}"))

    try:
        # Get the chain ID for replay protection (EIP-155)
        chain_id = w3.eth.chain_id
        nonce = w3.eth.get_transaction_count(sender_address)
        
        # Get current gas price from the network
        gas_price = w3.eth.gas_price
        
        # Build the transaction object without specifying the gas limit
        transaction = {
            'to': destination_address,
            'value': w3.to_wei(total_amount, 'ether'),
            'gasPrice': gas_price,
            'nonce': nonce,
            'chainId': chain_id
        }

        # Estimate gas limit required for the transaction
        estimated_gas = w3.eth.estimate_gas(transaction)
        transaction['gas'] = estimated_gas  # Automatically calculate and set gas limit
        
        # Sign the transaction
        signed_txn = w3.eth.account.sign_transaction(transaction, private_key)

        # Send the signed transaction
        tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)

        # Calculate the total transaction fee (gas used * gas price)
        transaction_fee = estimated_gas * gas_price
        fee_in_eth = w3.from_wei(transaction_fee, 'ether')

        await call.message.answer(
            f"✅ ETH successfully sent!\n"
            f"TXID: <code>{w3.toHex(tx_hash)}</code>\n"
            f"Estimated Transaction Fee: {fee_in_eth} ETH",
            reply_markup=eth_back_to_eth_menu(),
            parse_mode=ParseMode.HTML
        )
    
    except Exception as e:
        # Fetch the available balance if there is an error (like insufficient funds)
        try:
            balance = w3.eth.get_balance(sender_address)
            balance_in_eth = w3.from_wei(balance, 'ether')
            error_message = f"❌ Error sending ETH: {html.escape(str(e))}\n" \
                            f"Available balance: {balance_in_eth} ETH"
        except Exception as balance_error:
            # In case of an error retrieving the balance
            error_message = f"❌ Error sending ETH: {html.escape(str(e))}\n" \
                            f"Failed to retrieve balance: {html.escape(str(balance_error))}"

        await call.message.answer(error_message, reply_markup=eth_back_to_eth_menu())

    await state.clear()

# Cancel Withdrawal Request
@eth_router.callback_query(lambda call: call.data == "eth_cancel_withdraw")
async def eth_cancel_withdraw(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("Transaction cancelled.", reply_markup=eth_back_to_eth_menu())
