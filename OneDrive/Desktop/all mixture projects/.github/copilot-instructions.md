# Copilot instructions — Binance Futures Order Bot

Purpose: give AI coding agents the minimum, concrete knowledge to be productive in this repo.

1) Big picture
- This is a small CLI-based Binance USDT-M Futures bot. Core responsibilities are implemented in `src/`:
  - `src/config.py` — central Binance client + logging setup. Use `BinanceConfig().client` for API calls.
  - `src/market_orders.py`, `src/limit_orders.py` — handler classes that wrap API calls and return a dict with a `status` key.
  - `src/validators.py` — single place for input validation (symbols, quantity, price, side). Always call these before submitting orders.
  - `src/advanced/*` — higher-level strategies (stop-limit, OCO, TWAP, grid) that compose the core handlers.

2) Why things are structured this way
- Separation of concerns: handlers encapsulate order logic and return structured dicts (success/error), `config` centralizes client + logging, `validators` keep pre-flight checks consistent across handlers.
- Advanced strategies reuse core handlers (e.g., `TWAPStrategy` uses `MarketOrderHandler`; `GridStrategy` uses `LimitOrderHandler`). Modifications to core handlers will affect strategies.

3) Important conventions and patterns to follow
- Handlers are classes with `place_*` or `setup_*` methods and return a dict: `{ 'status': 'success' | 'error', ... }`.
- CLI usage is implemented at the bottom of each module with `click` (e.g., `market_order_cli()` in `src/market_orders.py`). The canonical CLI aggregator is `src/main.py` which wires commands to handlers.
- Logging: `BinanceConfig.setup_logging()` configures logging to `bot.log` and stdout. Use `logger = logging.getLogger(__name__)` in modules.
- Error handling: API errors are caught as `BinanceAPIException` and mapped to `{'status':'error','message':...}`. Preserve this shape when changing behavior.
- Environment: credentials come from `.env` (`BINANCE_API_KEY`, `BINANCE_API_SECRET`, `USE_TESTNET`). Respect `USE_TESTNET` boolean to avoid live trades during development.

4) Key integration points and dependencies
- External libs: `python-binance`, `click`, `python-dotenv`, `asyncio`. See `requirements.txt`.
- Binance calls use `client.futures_create_order(...)` and `client.futures_symbol_ticker(symbol=...)`. When modifying order parameters, keep naming consistent with `python-binance` futures API.
- OCO behavior: there is no single futures OCO API here — the repo places two separate orders (take-profit LIMIT with `reduceOnly=True`, and a STOP reduce-only opposite-side order). Keep that pattern unless intentionally replacing it with a tracked pair of orders and cancellation logic.

5) Running, builds and quick checks (developer workflows)
- Install: `pip install -r requirements.txt`.
- Run a single command (testnet): set `USE_TESTNET=True` in `.env`, then:
  - Market order: `python src/market_orders.py BTCUSDT BUY 0.001`
  - Via aggregator CLI: `python src/main.py market BTCUSDT BUY 0.001`
- Strategy examples:
  - TWAP: `python src/advanced/twap.py BTCUSDT BUY 0.1 30 10`
  - Grid: `python src/advanced/grid.py BTCUSDT 44000 46000 10 0.01`

6) Safety and testing guidance (concrete)
- Default `.env.example` shows `USE_TESTNET=True`. AI changes that touch order placement should default to testnet mode and minimal quantities.
- Because handlers return structured dicts and log to `bot.log`, prefer adding structured fields to these dicts (don't break `status` semantics).

7) Small pitfalls and gotchas discovered in code
- Validators expect uppercase `BUY`/`SELL`; modules call `.upper()` in a few places but not all — prefer validating and then using `side.upper()` when calling the client.
- `TWAPStrategy.execute_twap` uses `asyncio.sleep` and `asyncio.run` in `run_twap()`; keep async boundaries intact when refactoring.
- `GridStrategy.calculate_grid_levels` uses Decimal math and returns floats; preserve numeric handling to avoid precision regressions.

8) Examples for code edits
- Add a new order-type handler: copy pattern from `src/limit_orders.py`:
  - Use `BinanceConfig()` for client and logging.
  - Validate inputs with `OrderValidator`.
  - Catch `BinanceAPIException` and return `{'status':'error','message':...}`.
- To add a CLI subcommand, register it in `src/main.py` with the same `click` style used by other commands.

9) Files to inspect first when starting work
- `src/config.py`, `src/validators.py`, `src/market_orders.py`, `src/limit_orders.py`, `src/main.py`, and `src/advanced/*` (twap.py, grid.py, oco.py, stop_limit.py).

If anything above is unclear or you'd like more examples (unit tests, a dry-run mode, or a mock client for CI), tell me which area to expand and I will update this file.
