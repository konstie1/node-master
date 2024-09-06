import os
from dotenv import load_dotenv

load_dotenv()

# Bot and Admin
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS").split(',')))

# Litecoin node
LITECOIN_IP = os.getenv("LITECOIN_IP")
LITECOIN_LOGIN = os.getenv("LITECOIN_LOGIN")
LITECOIN_PASSWORD = os.getenv("LITECOIN_PASSWORD")

# Ethereum node
ETHEREUM_IP = os.getenv("ETHEREUM_IP")
ETHEREUM_LOGIN = os.getenv("ETHEREUM_LOGIN")
ETHEREUM_PASSWORD = os.getenv("ETHEREUM_PASSWORD")

# Tron node
TRON_IP = os.getenv("TRON_IP")
TRON_LOGIN = os.getenv("TRON_LOGIN")
TRON_PASSWORD = os.getenv("TRON_PASSWORD")

# Ripple node
RIPPLE_IP = os.getenv("RIPPLE_IP")
RIPPLE_LOGIN = os.getenv("RIPPLE_LOGIN")
RIPPLE_PASSWORD = os.getenv("RIPPLE_PASSWORD")
