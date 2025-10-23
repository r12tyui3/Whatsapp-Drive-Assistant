import click
import logging
from config import BinanceConfig
from validators import OrderValidator
from binance.exceptions import BinanceAPIException
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class OCOOrderHandler:
    """Handle OCO (One-Cancels-the-Other) orders for Binance Futures"""

    def __init__(self):
        self.config = BinanceConfig()
        self.client = self.config.client
        self.validator = OrderValidator()

    def place_oco_order(self, symbol, side, quantity, price, stop_price, stop_limit_price):
        """
        Place an OCO order (take-profit and stop-loss simultaneously)

        Args:
            symbol: Trading pair
            side: 'BUY' or 'SELL'
            quantity: Order quantity
            price: Take-profit price
            stop_price: Stop trigger price
            stop_limit_price: Stop-limit execution price
        """
        try:
            # Validate all inputs
            self.validator.validate_symbol(symbol)
            self.validator.validate_side(side)
            self.validator.validate_quantity(quantity)
            self.validator.validate_price(price)
            self.validator.validate_price(stop_price)
            self.validator.validate_price(stop_limit_price)

            logger.info(f"Attempting OCO order: {symbol} {side} {quantity}")
            logger.info(f"Take-profit: {price}, Stop: {stop_price}, Stop-limit: {stop_limit_price}")

            # For futures, we need to place two separate orders
            # First, place the limit order (take-profit)
            tp_order = self.client.futures_create_order(
                symbol=symbol,
                side=side.upper(),
                type='LIMIT',
                quantity=quantity,
                price=price,
                timeInForce='GTC',
                reduceOnly=True
            )

            # Then place the stop-limit order (stop-loss)
            sl_order = self.client.futures_create_order(
                symbol=symbol,
                side='SELL' if side.upper() == 'BUY' else 'BUY',
                type='STOP',
                quantity=quantity,
                stopPrice=stop_price,
                price=stop_limit_price,
                timeInForce='GTC',
                reduceOnly=True
            )

            logger.info(f"OCO orders placed successfully")

            return {
                'status': 'success',
                'take_profit_order': tp_order['orderId'],
                'stop_loss_order': sl_order['orderId'],
                'symbol': symbol,
                'timestamp': datetime.now().isoformat()
            }

        except BinanceAPIException as e:
            logger.error(f"Binance API error in OCO order: {e}")
            return {'status': 'error', 'message': str(e)}
        except Exception as e:
            logger.error(f"Unexpected error in OCO order: {e}")
            return {'status': 'error', 'message': str(e)}

@click.command()
@click.argument('symbol')
@click.argument('side')
@click.argument('quantity', type=float)
@click.argument('price', type=float)
@click.argument('stop_price', type=float)
@click.argument('stop_limit_price', type=float)
def oco_order_cli(symbol, side, quantity, price, stop_price, stop_limit_price):
    """Execute an OCO order via CLI"""
    handler = OCOOrderHandler()
    result = handler.place_oco_order(symbol, side, quantity, price, stop_price, stop_limit_price)
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    oco_order_cli()
