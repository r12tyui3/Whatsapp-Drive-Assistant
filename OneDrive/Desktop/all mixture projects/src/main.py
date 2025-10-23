import click
import logging
from market_orders import MarketOrderHandler
from limit_orders import LimitOrderHandler
from advanced.stop_limit import StopLimitOrderHandler
from advanced.oco import OCOOrderHandler
from advanced.twap import TWAPStrategy
from advanced.grid import GridStrategy

logger = logging.getLogger(__name__)

@click.group()
def cli():
    """Binance Futures Order Bot - CLI Interface"""
    pass

@cli.command()
@click.argument('symbol')
@click.argument('side')
@click.argument('quantity', type=float)
def market(symbol, side, quantity):
    """Place a market order"""
    handler = MarketOrderHandler()
    result = handler.place_market_order(symbol, side, quantity)
    print(result)

@cli.command()
@click.argument('symbol')
@click.argument('side')
@click.argument('quantity', type=float)
@click.argument('price', type=float)
def limit(symbol, side, quantity, price):
    """Place a limit order"""
    handler = LimitOrderHandler()
    result = handler.place_limit_order(symbol, side, quantity, price)
    print(result)

@cli.command()
@click.argument('symbol')
@click.argument('side')
@click.argument('quantity', type=float)
@click.argument('stop_price', type=float)
@click.argument('limit_price', type=float)
def stop_limit(symbol, side, quantity, stop_price, limit_price):
    """Place a stop-limit order"""
    handler = StopLimitOrderHandler()
    result = handler.place_stop_limit_order(symbol, side, quantity, stop_price, limit_price)
    print(result)

@cli.command()
@click.argument('symbol')
@click.argument('side')
@click.argument('quantity', type=float)
@click.argument('price', type=float)
@click.argument('stop_price', type=float)
@click.argument('stop_limit_price', type=float)
def oco(symbol, side, quantity, price, stop_price, stop_limit_price):
    """Place an OCO order"""
    handler = OCOOrderHandler()
    result = handler.place_oco_order(symbol, side, quantity, price, stop_price, stop_limit_price)
    print(result)

@cli.command()
@click.argument('symbol')
@click.argument('side')
@click.argument('total_quantity', type=float)
@click.argument('duration_minutes', type=int)
@click.argument('num_slices', type=int)
def twap(symbol, side, total_quantity, duration_minutes, num_slices):
    """Execute TWAP strategy"""
    strategy = TWAPStrategy()
    result = strategy.run_twap(symbol, side, total_quantity, duration_minutes, num_slices)
    print(result)

@cli.command()
@click.argument('symbol')
@click.argument('lower_price', type=float)
@click.argument('upper_price', type=float)
@click.argument('num_grids', type=int)
@click.argument('quantity_per_grid', type=float)
def grid(symbol, lower_price, upper_price, num_grids, quantity_per_grid):
    """Execute grid trading strategy"""
    strategy = GridStrategy()
    result = strategy.setup_grid(symbol, lower_price, upper_price, num_grids, quantity_per_grid)
    print(result)

if __name__ == '__main__':
    cli()
