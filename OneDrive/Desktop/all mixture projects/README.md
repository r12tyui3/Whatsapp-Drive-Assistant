# Binance Futures Order Bot

A comprehensive CLI-based trading bot for Binance USDT-M Futures with support for multiple order types, advanced strategies, and robust logging.

## Features

### Core Orders
- **Market Orders**: Instant execution at current market price
- **Limit Orders**: Execute at specified price or better

### Advanced Orders
- **Stop-Limit Orders**: Trigger limit orders when stop price is hit
- **OCO (One-Cancels-the-Other)**: Place take-profit and stop-loss simultaneously
- **TWAP (Time-Weighted Average Price)**: Split large orders over time
- **Grid Trading**: Automated buy-low/sell-high within price range

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/binance-bot.git
cd binance-bot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your Binance API credentials
```

## Configuration

Create a `.env` file with:
```
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here
USE_TESTNET=True  # Set to False for production
```

## Usage

### Basic Orders

#### Market Order
```bash
python src/market_orders.py BTCUSDT BUY 0.01
```

#### Limit Order
```bash
python src/limit_orders.py BTCUSDT BUY 0.01 45000
```

### Advanced Orders

#### Stop-Limit Order
```bash
python src/advanced/stop_limit.py BTCUSDT SELL 0.01 44000 43900
```

#### OCO Order
```bash
python src/advanced/oco.py BTCUSDT BUY 0.01 46000 44000 43900
```

#### TWAP Strategy
```bash
# Execute 0.1 BTC over 30 minutes in 10 slices
python src/advanced/twap.py BTCUSDT BUY 0.1 30 10
```

#### Grid Trading
```bash
# Set up grid between $44000-$46000 with 10 levels
python src/advanced/grid.py BTCUSDT 44000 46000 10 0.01
```

### Using Main CLI Interface
```bash
python src/main.py market BTCUSDT BUY 0.01
python src/main.py limit BTCUSDT BUY 0.01 45000
python src/main.py twap BTCUSDT BUY 0.1 30 10
```

## Logging

All operations are logged to `bot.log` with:
- Timestamps
- Order details
- API responses
- Error traces

## Testing

Use Binance Testnet by setting `USE_TESTNET=True` in `.env`.

Testnet API: https://testnet.binancefuture.com

## Project Structure

```
binance-bot/
├── src/
│   ├── config.py              # Configuration and client setup
│   ├── validators.py          # Input validation
│   ├── market_orders.py       # Market order implementation
│   ├── limit_orders.py        # Limit order implementation
│   ├── main.py               # Main CLI interface
│   └── advanced/
│       ├── stop_limit.py     # Stop-limit orders
│       ├── oco.py            # OCO orders
│       ├── twap.py           # TWAP strategy
│       └── grid.py           # Grid trading
├── bot.log                   # Structured logs
├── requirements.txt          # Dependencies
├── .env.example             # Environment template
└── README.md                # Documentation
```

## Safety Features

- Input validation for all parameters
- Comprehensive error handling
- Structured logging
- Testnet support for safe testing
- Order size limits

## Dependencies

- python-binance
- click
- python-dotenv
- asyncio

## Support

For API documentation: https://docs.anthropic.com
For Binance API: https://binance-docs.github.io/apidocs/futures/en/

## License

MIT
