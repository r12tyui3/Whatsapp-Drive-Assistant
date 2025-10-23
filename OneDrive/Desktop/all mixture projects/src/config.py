import os
from dotenv import load_dotenv
from binance.client import Client
from binance.exceptions import BinanceAPIException
import logging
from datetime import datetime

load_dotenv()

class BinanceConfig:
    """Configuration and client setup for Binance Futures"""

    def __init__(self):
        self.api_key = os.getenv('BINANCE_API_KEY')
        self.api_secret = os.getenv('BINANCE_API_SECRET')
        self.testnet = os.getenv('USE_TESTNET', 'True').lower() == 'true'

        if self.testnet:
            self.client = Client(self.api_key, self.api_secret, testnet=True)
        else:
            self.client = Client(self.api_key, self.api_secret)

        # Setup logging
        self.setup_logging()

    def setup_logging(self):
        """Configure structured logging"""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler('bot.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
