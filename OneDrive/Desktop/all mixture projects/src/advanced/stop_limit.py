import click
import logging
from config import BinanceConfig
from validators import OrderValidator
from binance.exceptions import BinanceAPIException
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class StopLimitOrderHandler:
    """Handle stop-limit orders for Binance Futures"""

    def __init__(self):
        self.config = BinanceConfig()
        self.client = self.config.client
        self.validator = OrderValidator()

    def place_stop_limit_order(self, symbol, side, quantity, stop_price, limit_price):
        """
        Place a stop-limit order

        Args:
            symbol: Trading pair
            side: 'BUY' or 'SELL'
            quantity: Order quantity
            stop_price: Price to trigger the limit order
            limit_price: Limit price once triggered
        """
        try:
            # Validate inputs
            self.validator.validate_symbol(symbol)
            self.validator.validate_side(side)
            self.validator.validate_quantity(quantity)
            self.validator.validate_price(stop_price)
            self.validator.validate_price(limit_price)

            logger.info(f"Attempting stop-limit order: {side} {quantity} {symbol}")
            logger.info(f"Stop: {stop_price}, Limit: {limit_price}")

            order = self.client.futures_create_order(
                symbol=symbol,
                side=side.upper(),
                type='STOP',
                quantity=quantity,
                stopPrice=stop_price,
                price=limit_price,
                timeInForce='GTC'
            )

            logger.info(f"Stop-limit order successful: {json.dumps(order, indent=2)}")

            return {
                'status': 'success',
                'order_id': order['orderId'],
                'symbol': order['symbol'],
                'side': order['side'],
                'quantity': order['origQty'],
                'stop_price': stop_price,
                'limit_price': limit_price,
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
@click.argument('stop_price', type=float)
@click.argument('limit_price', type=float)
def stop_limit_cli(symbol, side, quantity, stop_price, limit_price):
    """Execute a stop-limit order via CLI"""
    handler = StopLimitOrderHandler()
    result = handler.place_stop_limit_order(symbol, side, quantity, stop_price, limit_price)
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    stop_limit_cli()
