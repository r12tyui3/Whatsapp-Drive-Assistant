import re
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class OrderValidator:
    """Validate order parameters before submission"""

    @staticmethod
    def validate_symbol(symbol):
        """Validate trading pair symbol"""
        pattern = r'^[A-Z]{2,}USDT$'
        if not re.match(pattern, symbol):
            raise ValueError(f"Invalid symbol format: {symbol}")
        return True

    @staticmethod
    def validate_quantity(quantity, min_qty=0.001):
        """Validate order quantity"""
        try:
            qty = Decimal(str(quantity))
            if qty <= 0:
                raise ValueError("Quantity must be positive")
            if qty < min_qty:
                raise ValueError(f"Quantity below minimum: {min_qty}")
            return True
        except Exception as e:
            raise ValueError(f"Invalid quantity: {e}")

    @staticmethod
    def validate_price(price):
        """Validate order price"""
        try:
            price_decimal = Decimal(str(price))
            if price_decimal <= 0:
                raise ValueError("Price must be positive")
            return True
        except Exception as e:
            raise ValueError(f"Invalid price: {e}")

    @staticmethod
    def validate_side(side):
        """Validate order side (BUY/SELL)"""
        valid_sides = ['BUY', 'SELL']
        if side.upper() not in valid_sides:
            raise ValueError(f"Invalid side: {side}. Must be BUY or SELL")
        return True
