from rich.highlighter import Highlighter
from rich.logging import RichHandler
from rich.console import Console
from dotenv import load_dotenv
from rich.text import Text
from enum import Enum
import logging
import os

# ------------------------
# Constants / ENVVAR setup
# ------------------------
load_dotenv()
BLOCK_CONFIRMATIONS = os.getenv("BLOCK_CONFIRMATIONS", 10)
GAS_DEPLOYMENT_LIMIT = os.getenv("GAS_DEPLOYMENT_LIMIT", 21000)
GAS_DEPLOYMENT_PRICE = os.getenv("GAS_DEPLOYMENT_PRICE", 5000000000)
DEBUG = True if int(os.getenv("DEBUG", 0)) == 1 else False

# -------------
# Logging setup
# -------------
console = Console(color_system=None, stderr=None)
logging.basicConfig(
    format="%(funcName)-9s : %(message)s",
    level=logging.DEBUG if DEBUG else logging.INFO,
    handlers=[RichHandler(level=logging.DEBUG if DEBUG else logging.INFO)],
)
logger = logging.getLogger("rich")


class Banner(Highlighter):
    def highlight(self, text: Text):
        c1, c2, c3 = 'dark_green', 'bright_green', 'pale_green3'
        return [text.stylize(style, i, i + 1) for i, style in enumerate([c1 if ord(ch._text[0]) == 10244 else c3 if ord(ch._text[0]) in {9600, 8195, 9604, 9608, 10, 9617} else c2 for ch in text])]


# ---------------------
# Application banner :)
# ---------------------
def banner():
    BANNER = """
⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄
⠄⠄⠄⠄⠄⠄⣴⣶⣤⡤⠦⣤⣀⣤⠆⠄⠄⠄⠄⠄⣈⣭⣭⣿⣶⣿⣦⣼⣆⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄
⠄⠄⠄⠄⠄⠄⠄⠉⠻⢿⣿⠿⣿⣿⣶⣦⠤⠄⡠⢾⣿⣿⡿⠋⠉⠉⠻⣿⣿⡛⣦⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄
⠄⠄⠄⠄⠄⠄⠄⠄⠄⠈⠄⠄⠄⠈⢿⣿⣟⠦⠄⣾⣿⣿⣷⠄⠄⠄⠄⠻⠿⢿⣿⣧⣄⠄⠄⠄⠄⠄⠄⠄⠄⠄
⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⣸⣿⣿⢧⠄⢻⠻⣿⣿⣷⣄⣀⠄⠢⣀⡀⠈⠙⠿⠄⠄⠄⠄⠄⠄⠄⠄⠄
⠄⠄⠄⠄⠄⠄⢀⠄⠄⠄⠄⠄⠄⢠⣿⣿⣿⠈⠄⠄⠡⠌⣻⣿⣿⣿⣿⣿⣿⣿⣛⣳⣤⣀⣀⠄⠄⠄⠄⠄⠄⠄
⠄⠄⠄⠄⠄⠄⢠⣧⣶⣥⡤⢄⠄⣸⣿⣿⠘⠄⠄⢀⣴⣿⣿⡿⠛⣿⣿⣧⠈⢿⠿⠟⠛⠻⠿⠄⠄⠄⠄⠄⠄⠄
⠄⠄⠄⠄⠄⣰⣿⣿⠛⠻⣿⣿⡦⢹⣿⣷⠄⠄⠄⢊⣿⣿⡏⠄⠄⢸⣿⣿⡇⠄⢀⣠⣄⣾⠄⠄⠄⠄⠄⠄⠄⠄
⠄⠄⠄⠄⣠⣿⠿⠛⠄⢀⣿⣿⣷⠘⢿⣿⣦⡀⠄⢸⢿⣿⣿⣄⠄⣸⣿⣿⡇⣪⣿⡿⠿⣿⣷⡄⠄⠄⠄⠄⠄⠄
⠄⠄⠄⠄⠙⠃⠄⠄⠄⣼⣿⡟⠌⠄⠈⠻⣿⣿⣦⣌⡇⠻⣿⣿⣷⣿⣿⣿⠐⣿⣿⡇⠄⠛⠻⢷⣄⠄⠄⠄⠄⠄
⠄⠄⠄⠄⠄⠄⠄⠄⠄⢻⣿⣿⣄⠄⠄⠄⠈⠻⣿⣿⣿⣷⣿⣿⣿⣿⣿⡟⠄⠫⢿⣿⡆⠄⠄⠄⠁⠄⠄⠄⠄⠄
⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠻⣿⣿⣿⣿⣶⣶⣾⣿⣿⣿⣿⣿⣿⣿⣿⡟⢀⣀⣤⣾⡿⠃⠄⠄⠄⠄⠄⠄⠄⠄⠄
⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⢶⣆⢀⣶⠂⣶⡶⠶⣦⡄⢰⣶⠶⢶⣦⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄
------------------------------------------
█░█ █▄█ █▀▄ █▀█ ▄▀█ █░░ █ █▀ █▄▀ ░ █▀█ █▄█
█▀█ ░█░ █▄▀ █▀▄ █▀█ █▄▄ █ ▄█ █░█ ▄ █▀▀ ░█░
-------------------------------@paulpierre
    """
    console = Console()
    bh = Banner()
    console.print(bh(BANNER))


banner()

# ------------------------------
# Enum constants for application
# ------------------------------

# For autmated gas price calculation
class GAS_SPEED(Enum):
    SLOW = 1
    STANDARD = 2
    FAST = 3


"""
---------------------
CHAIN enum properties
---------------------
- NAME: Display name of the chain
- SYMBOL: Symbol of the chain used for a variety of purposes
- SLUG: Slug is the internal reference
- CHAIN_ID: Chain ID is the canonical network ID
- RPC_URL: RPC url for a node provider by chain
- API_URL: Block explorer URL, primarily used for ABI fetching
"""


class CHAIN(Enum):
    ETHEREUM = {
        'id': 1,
        'symbol': 'ETH',
        'slug': 'ethereum',
        'name': 'Ethereum Mainnet',
        'api': f'https://api.etherscan.io/api?apikey={os.getenv("ETHERSCAN_API_KEY", None)}&',
        'rpc': os.getenv('ETHEREUM_RPC_URL', None),
    }
    POLYGON = {
        'id': 137,
        'slug': 'polygon',
        'name': 'Polygon Mainnet',
        'symbol': 'MATIC',
        'api': f'https://api.polygonscan.com/api?apikey={os.getenv("POLYGONSCAN_API_KEY", None)}&',
        'rpc': os.getenv('POLYGON_RPC_URL', None),
    }
    BSC = {
        'id': 56,
        'slug': 'bsc',
        'name': 'BSC Mainnet',
        'symbol': 'BSC',
        'api': f'https://api.bscscan.com/api?apikey={os.getenv("BSCSCAN_API_KEY", None)}&',
        'rpc': os.getenv('BSC_RPC_URL', None),
    }
    MUMBAI = {
        'id': 80001,
        'slug': 'mumbai',
        'name': 'Mumbai Polygon Testnet',
        'symbol': 'MATIC',
        'api': f'https://api-testnet.polygonscan.com/api?apikey={os.getenv("POLYGONSCAN_API_KEY", None)}&',
        'rpc': os.getenv('MUMBAI_RPC_URL', None),
    }
    GOERLI = {
        'id': 5,
        'slug': 'goerli',
        'name': 'Goerli Ethereum Testnet',
        'symbol': 'ETH',
        'api': f'https://api-goerli.etherscan.io?apikey={os.getenv("ETHERSCAN_API_KEY", None)}&',
        'rpc': os.getenv('GOERLI_RPC_URL', None),
    }
    BSC_TESTNET = {
        'id': 97,
        'slug': 'bsc-testnet',
        'name': 'BSC Testnet',
        'symbol': 'BSC',
        'api': f'https://api-testnet.bscscan.com?apikey={os.getenv("BSCSCAN_API_KEY", None)}&',
        'rpc': os.getenv('BSC_TESTNET_RPC_URL', None),
    }

    @property
    def CHAIN_ID(self):
        return self.value['id']

    @property
    def SLUG(self):
        return self.value['slug']

    @property
    def DECIMALS(self):
        return 18

    @property
    def NAME(self):
        return self.value['name']

    @property
    def SYMBOL(self):
        return self.value['symbol']

    @property
    def API_URL(self):
        return self.value['api']

    @property
    def RPC_URL(self):
        return self.value['rpc']
