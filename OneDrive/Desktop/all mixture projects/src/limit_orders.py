import click
import logging
from config import BinanceConfig
from validators import OrderValidator
from binance.exceptions import BinanceAPIException
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class LimitOrderHandler:
    """Handle limit order execution for Binance Futures"""

    def __init__(self):
        self.config = BinanceConfig()
        self.client = self.config.client
        self.validator = OrderValidator()

    def place_limit_order(self, symbol, side, quantity, price, time_in_force='GTC'):
        """
        Place a limit order on Binance Futures

        Args:
            symbol: Trading pair
            side: 'BUY' or 'SELL'
            quantity: Order quantity
            price: Limit price
            time_in_force: Order time in force (GTC, IOC, FOK)
        """
        try:
            # Validate inputs
            self.validator.validate_symbol(symbol)
            self.validator.validate_side(side)
            self.validator.validate_quantity(quantity)
            self.validator.validate_price(price)

            logger.info(f"Attempting limit order: {side} {quantity} {symbol} @ {price}")

            order = self.client.futures_create_order(
                symbol=symbol,
                side=side.upper(),
                type='LIMIT',
                quantity=quantity,
                price=price,
                timeInForce=time_in_force
            )

            logger.info(f"Limit order successful: {json.dumps(order, indent=2)}")

            return {
                'status': 'success',
                'order_id': order['orderId'],
                'symbol': order['symbol'],
                'side': order['side'],
                'quantity': order['origQty'],
                'price': order['price'],
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
@click.argument('price', type=float)
@click.option('--time-in-force', default='GTC', help='Time in force (GTC, IOC, FOK)')
def limit_order_cli(symbol, side, quantity, price, time_in_force):
    """Execute a limit order via CLI"""
    handler = LimitOrderHandler()
    result = handler.place_limit_order(symbol, side, quantity, price, time_in_force)
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    limit_order_cli()
