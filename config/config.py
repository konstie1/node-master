import os
from dotenv import load_dotenv

load_dotenv()

# Bot and Admin
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS").split(',')))

BITCOIN_IP = os.getenv("BITCOIN_IP")
BITCOIN_PORT = os.getenv("BITCOIN_PORT")
BITCOIN_LOGIN = os.getenv("BITCOIN_LOGIN")
BITCOIN_PASSWORD = os.getenv("BITCOIN_PASSWORD")

LITECOIN_IP = os.getenv("LITECOIN_IP")
LITECOIN_LOGIN = os.getenv("LITECOIN_LOGIN")
LITECOIN_PASSWORD = os.getenv("LITECOIN_PASSWORD")
LITECOIN_PORT = os.getenv('LITECOIN_PORT')

ETHEREUM_IP = os.getenv("ETHEREUM_IP")
ETHEREUM_LOGIN = os.getenv("ETHEREUM_LOGIN")
ETHEREUM_PASSWORD = os.getenv("ETHEREUM_PASSWORD")

TRON_IP = os.getenv("TRON_IP")
TRON_LOGIN = os.getenv("TRON_LOGIN")
TRON_PASSWORD = os.getenv("TRON_PASSWORD")

RIPPLE_IP = os.getenv("RIPPLE_IP")
RIPPLE_LOGIN = os.getenv("RIPPLE_LOGIN")
RIPPLE_PASSWORD = os.getenv("RIPPLE_PASSWORD")
RIPPLE_PORT = os.getenv("RIPPLE_PORT")
