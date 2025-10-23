import click
import logging
from config import BinanceConfig
from validators import OrderValidator
from binance.exceptions import BinanceAPIException
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class MarketOrderHandler:
    """Handle market order execution for Binance Futures"""

    def __init__(self):
        self.config = BinanceConfig()
        self.client = self.config.client
        self.validator = OrderValidator()

    def place_market_order(self, symbol, side, quantity):
        """
        Place a market order on Binance Futures

        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            side: 'BUY' or 'SELL'
            quantity: Order quantity
        """
        try:
            # Validate inputs
            self.validator.validate_symbol(symbol)
            self.validator.validate_side(side)
            self.validator.validate_quantity(quantity)

            # Log order attempt
            logger.info(f"Attempting market order: {side} {quantity} {symbol}")

            # Place the order
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side.upper(),
                type='MARKET',
                quantity=quantity
            )

            # Log successful order
            logger.info(f"Market order successful: {json.dumps(order, indent=2)}")

            return {
                'status': 'success',
                'order_id': order['orderId'],
                'symbol': order['symbol'],
                'side': order['side'],
                'quantity': order['origQty'],
                'timestamp': datetime.now().isoformat()
            }

        except BinanceAPIException as e:
            logger.error(f"Binance API error: {e}")
            return {'status': 'error', 'message': str(e)}
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {'status': 'error', 'message': str(e)}

@click.command()
@click.argument('symbol')
@click.argument('side')
@click.argument('quantity', type=float)
def market_order_cli(symbol, side, quantity):
    """Execute a market order via CLI"""
    handler = MarketOrderHandler()
    result = handler.place_market_order(symbol, side, quantity)
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    market_order_cli()
