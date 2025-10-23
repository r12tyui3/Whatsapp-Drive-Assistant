import click
import logging
from decimal import Decimal
from config import BinanceConfig
from validators import OrderValidator
from limit_orders import LimitOrderHandler
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class GridStrategy:
    """Grid trading strategy for automated buy-low/sell-high within a price range"""

    def __init__(self):
        self.config = BinanceConfig()
        self.client = self.config.client
        self.validator = OrderValidator()
        self.limit_handler = LimitOrderHandler()

    def calculate_grid_levels(self, lower_price, upper_price, num_grids):
        """Calculate price levels for grid orders"""
        lower = Decimal(str(lower_price))
        upper = Decimal(str(upper_price))

        price_range = upper - lower
        grid_spacing = price_range / (num_grids - 1)

        levels = []
        for i in range(num_grids):
            level = lower + (grid_spacing * i)
            levels.append(float(level))

        return levels

    def setup_grid(self, symbol, lower_price, upper_price, num_grids, quantity_per_grid):
        """
        Set up a grid trading strategy

        Args:
            symbol: Trading pair
            lower_price: Lower bound of price range
            upper_price: Upper bound of price range
            num_grids: Number of grid levels
            quantity_per_grid: Quantity for each grid order
        """
        try:
            # Validate inputs
            self.validator.validate_symbol(symbol)
            self.validator.validate_price(lower_price)
            self.validator.validate_price(upper_price)
            self.validator.validate_quantity(quantity_per_grid)

            if upper_price <= lower_price:
                raise ValueError("Upper price must be greater than lower price")

            if num_grids < 2:
                raise ValueError("Number of grids must be at least 2")

            # Get current market price
            ticker = self.client.futures_symbol_ticker(symbol=symbol)
            current_price = float(ticker['price'])

            logger.info(f"Setting up grid strategy for {symbol}")
            logger.info(f"Range: {lower_price} - {upper_price}, Grids: {num_grids}")
            logger.info(f"Current price: {current_price}")

            # Calculate grid levels
            grid_levels = self.calculate_grid_levels(lower_price, upper_price, num_grids)

            buy_orders = []
            sell_orders = []

            for level in grid_levels:
                if level < current_price:
                    # Place buy order below current price
                    logger.info(f"Placing buy order at {level}")
                    order = self.limit_handler.place_limit_order(
                        symbol, 'BUY', quantity_per_grid, level
                    )
                    buy_orders.append({
                        'price': level,
                        'result': order
                    })
                elif level > current_price:
                    # Place sell order above current price
                    logger.info(f"Placing sell order at {level}")
                    order = self.limit_handler.place_limit_order(
                        symbol, 'SELL', quantity_per_grid, level
                    )
                    sell_orders.append({
                        'price': level,
                        'result': order
                    })

            logger.info(f"Grid setup complete: {len(buy_orders)} buy, {len(sell_orders)} sell orders")

            return {
                'status': 'success',
                'strategy': 'GRID',
                'symbol': symbol,
                'current_price': current_price,
                'grid_levels': grid_levels,
                'buy_orders': buy_orders,
                'sell_orders': sell_orders,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Grid strategy error: {e}")
            return {'status': 'error', 'message': str(e)}

@click.command()
@click.argument('symbol')
@click.argument('lower_price', type=float)
@click.argument('upper_price', type=float)
@click.argument('num_grids', type=int)
@click.argument('quantity_per_grid', type=float)
def grid_cli(symbol, lower_price, upper_price, num_grids, quantity_per_grid):
    """Execute grid trading strategy via CLI"""
    strategy = GridStrategy()
    result = strategy.setup_grid(symbol, lower_price, upper_price, num_grids, quantity_per_grid)
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    grid_cli()
