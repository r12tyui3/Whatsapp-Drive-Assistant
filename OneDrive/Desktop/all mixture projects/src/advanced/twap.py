import click
import logging
import time
import asyncio
from config import BinanceConfig
from validators import OrderValidator
from market_orders import MarketOrderHandler
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class TWAPStrategy:
    """Time-Weighted Average Price strategy implementation"""

    def __init__(self):
        self.config = BinanceConfig()
        self.client = self.config.client
        self.validator = OrderValidator()
        self.market_handler = MarketOrderHandler()

    async def execute_twap(self, symbol, side, total_quantity, duration_minutes, num_slices):
        """
        Execute TWAP strategy by splitting orders over time

        Args:
            symbol: Trading pair
            side: 'BUY' or 'SELL'
            total_quantity: Total quantity to execute
            duration_minutes: Total duration for execution
            num_slices: Number of order slices
        """
        try:
            # Validate inputs
            self.validator.validate_symbol(symbol)
            self.validator.validate_side(side)
            self.validator.validate_quantity(total_quantity)

            if num_slices < 2:
                raise ValueError("Number of slices must be at least 2")

            slice_quantity = total_quantity / num_slices
            interval_seconds = (duration_minutes * 60) / num_slices

            logger.info(f"Starting TWAP execution: {symbol} {side} {total_quantity}")
            logger.info(f"Slices: {num_slices}, Interval: {interval_seconds}s")

            results = []
            start_time = datetime.now()

            for i in range(num_slices):
                # Execute slice
                logger.info(f"Executing slice {i+1}/{num_slices}")

                order_result = self.market_handler.place_market_order(
                    symbol, side, slice_quantity
                )

                results.append({
                    'slice': i + 1,
                    'quantity': slice_quantity,
                    'result': order_result,
                    'timestamp': datetime.now().isoformat()
                })

                # Wait for next slice (except for last one)
                if i < num_slices - 1:
                    await asyncio.sleep(interval_seconds)

            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            logger.info(f"TWAP execution completed in {execution_time} seconds")

            return {
                'status': 'success',
                'strategy': 'TWAP',
                'symbol': symbol,
                'side': side,
                'total_quantity': total_quantity,
                'num_slices': num_slices,
                'execution_time': execution_time,
                'slices': results,
                'timestamp': end_time.isoformat()
            }

        except Exception as e:
            logger.error(f"TWAP execution error: {e}")
            return {'status': 'error', 'message': str(e)}

    def run_twap(self, symbol, side, total_quantity, duration_minutes, num_slices):
        """Synchronous wrapper for TWAP execution"""
        return asyncio.run(self.execute_twap(
            symbol, side, total_quantity, duration_minutes, num_slices
        ))

@click.command()
@click.argument('symbol')
@click.argument('side')
@click.argument('total_quantity', type=float)
@click.argument('duration_minutes', type=int)
@click.argument('num_slices', type=int)
def twap_cli(symbol, side, total_quantity, duration_minutes, num_slices):
    """Execute TWAP strategy via CLI"""
    strategy = TWAPStrategy()
    result = strategy.run_twap(symbol, side, total_quantity, duration_minutes, num_slices)
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    twap_cli()
