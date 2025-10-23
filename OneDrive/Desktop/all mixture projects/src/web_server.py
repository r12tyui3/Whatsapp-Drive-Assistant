#!/usr/bin/env python3
"""
FastAPI Web Server for Binance Futures Order Bot
Provides REST API endpoints and web interface for trading operations
"""

import os
import logging
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# Import existing bot modules
from config import BinanceConfig
from validators import OrderValidator
from market_orders import MarketOrderHandler
from limit_orders import LimitOrderHandler
from advanced.stop_limit import StopLimitOrderHandler
from advanced.oco import OCOOrderHandler
from advanced.twap import TWAPStrategy
from advanced.grid import GridStrategy

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Binance Futures Order Bot API",
    description="REST API for executing automated trading strategies on Binance Futures",
    version="1.0.0"
)

# Mount static files directory if it exists
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Request models
class MarketOrderRequest(BaseModel):
    symbol: str
    side: str  # BUY or SELL
    quantity: float

class LimitOrderRequest(BaseModel):
    symbol: str
    side: str
    quantity: float
    price: float
    time_in_force: Optional[str] = "GTC"

class StopLimitOrderRequest(BaseModel):
    symbol: str
    side: str
    quantity: float
    stop_price: float
    limit_price: float

class OCOOrderRequest(BaseModel):
    symbol: str
    side: str
    quantity: float
    price: float  # Take profit price
    stop_price: float
    stop_limit_price: float

class TWAPOrderRequest(BaseModel):
    symbol: str
    side: str
    total_quantity: float
    duration_minutes: int
    num_slices: int

class GridOrderRequest(BaseModel):
    symbol: str
    lower_price: float
    upper_price: float
    num_grids: int
    quantity_per_grid: float

# Initialize handlers
config = BinanceConfig()
validator = OrderValidator()
market_handler = MarketOrderHandler()
limit_handler = LimitOrderHandler()
stop_limit_handler = StopLimitOrderHandler()
oco_handler = OCOOrderHandler()
twap_strategy = TWAPStrategy()
grid_strategy = GridStrategy()

# API Routes
@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the web interface"""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Binance Futures Order Bot</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .header {
                text-align: center;
                color: #2c3e50;
                margin-bottom: 30px;
            }
            .order-section {
                background: white;
                padding: 20px;
                margin: 20px 0;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .form-group {
                margin: 10px 0;
            }
            label {
                display: block;
                margin-bottom: 5px;
                font-weight: bold;
            }
            input, select {
                width: 100%;
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                box-sizing: border-box;
            }
            button {
                background-color: #3498db;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                margin: 5px;
            }
            button:hover {
                background-color: #2980b9;
            }
            .response {
                margin-top: 20px;
                padding: 15px;
                border-radius: 4px;
                white-space: pre-wrap;
                font-family: monospace;
            }
            .success {
                background-color: #d4edda;
                border: 1px solid #c3e6cb;
                color: #155724;
            }
            .error {
                background-color: #f8d7da;
                border: 1px solid #f5c6cb;
                color: #721c24;
            }
            .grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🔥 Binance Futures Order Bot</h1>
            <p>Execute automated trading strategies via REST API</p>
        </div>

        <div class="grid">
            <!-- Market Order -->
            <div class="order-section">
                <h2>📈 Market Order</h2>
                <form id="marketForm">
                    <div class="form-group">
                        <label>Symbol (e.g., BTCUSDT):</label>
                        <input type="text" id="marketSymbol" value="BTCUSDT" required>
                    </div>
                    <div class="form-group">
                        <label>Side:</label>
                        <select id="marketSide" required>
                            <option value="BUY">BUY</option>
                            <option value="SELL">SELL</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Quantity:</label>
                        <input type="number" id="marketQuantity" step="0.000001" required>
                    </div>
                    <button type="submit">Execute Market Order</button>
                </form>
                <div id="marketResponse" class="response" style="display: none;"></div>
            </div>

            <!-- Limit Order -->
            <div class="order-section">
                <h2>🎯 Limit Order</h2>
                <form id="limitForm">
                    <div class="form-group">
                        <label>Symbol:</label>
                        <input type="text" id="limitSymbol" value="BTCUSDT" required>
                    </div>
                    <div class="form-group">
                        <label>Side:</label>
                        <select id="limitSide" required>
                            <option value="BUY">BUY</option>
                            <option value="SELL">SELL</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Quantity:</label>
                        <input type="number" id="limitQuantity" step="0.000001" required>
                    </div>
                    <div class="form-group">
                        <label>Price:</label>
                        <input type="number" id="limitPrice" step="0.01" required>
                    </div>
                    <button type="submit">Execute Limit Order</button>
                </form>
                <div id="limitResponse" class="response" style="display: none;"></div>
            </div>

            <!-- OCO Order -->
            <div class="order-section">
                <h2>⚡ OCO Order</h2>
                <form id="ocoForm">
                    <div class="form-group">
                        <label>Symbol:</label>
                        <input type="text" id="ocoSymbol" value="BTCUSDT" required>
                    </div>
                    <div class="form-group">
                        <label>Side:</label>
                        <select id="ocoSide" required>
                            <option value="BUY">BUY</option>
                            <option value="SELL">SELL</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Quantity:</label>
                        <input type="number" id="ocoQuantity" step="0.000001" required>
                    </div>
                    <div class="form-group">
                        <label>Take Profit Price:</label>
                        <input type="number" id="ocoPrice" step="0.01" required>
                    </div>
                    <div class="form-group">
                        <label>Stop Price:</label>
                        <input type="number" id="ocoStopPrice" step="0.01" required>
                    </div>
                    <div class="form-group">
                        <label>Stop Limit Price:</label>
                        <input type="number" id="ocoStopLimitPrice" step="0.01" required>
                    </div>
                    <button type="submit">Execute OCO Order</button>
                </form>
                <div id="ocoResponse" class="response" style="display: none;"></div>
            </div>

            <!-- TWAP Strategy -->
            <div class="order-section">
                <h2>⏰ TWAP Strategy</h2>
                <form id="twapForm">
                    <div class="form-group">
                        <label>Symbol:</label>
                        <input type="text" id="twapSymbol" value="BTCUSDT" required>
                    </div>
                    <div class="form-group">
                        <label>Side:</label>
                        <select id="twapSide" required>
                            <option value="BUY">BUY</option>
                            <option value="SELL">SELL</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Total Quantity:</label>
                        <input type="number" id="twapTotalQuantity" step="0.000001" required>
                    </div>
                    <div class="form-group">
                        <label>Duration (minutes):</label>
                        <input type="number" id="twapDuration" value="30" min="1" required>
                    </div>
                    <div class="form-group">
                        <label>Number of Slices:</label>
                        <input type="number" id="twapSlices" value="10" min="2" required>
                    </div>
                    <button type="submit">Execute TWAP Strategy</button>
                </form>
                <div id="twapResponse" class="response" style="display: none;"></div>
            </div>

            <!-- Grid Trading -->
            <div class="order-section">
                <h2>📊 Grid Trading</h2>
                <form id="gridForm">
                    <div class="form-group">
                        <label>Symbol:</label>
                        <input type="text" id="gridSymbol" value="BTCUSDT" required>
                    </div>
                    <div class="form-group">
                        <label>Lower Price:</label>
                        <input type="number" id="gridLowerPrice" step="0.01" required>
                    </div>
                    <div class="form-group">
                        <label>Upper Price:</label>
                        <input type="number" id="gridUpperPrice" step="0.01" required>
                    </div>
                    <div class="form-group">
                        <label>Number of Grids:</label>
                        <input type="number" id="gridNumGrids" value="5" min="2" required>
                    </div>
                    <div class="form-group">
                        <label>Quantity per Grid:</label>
                        <input type="number" id="gridQuantityPerGrid" step="0.000001" required>
                    </div>
                    <button type="submit">Execute Grid Strategy</button>
                </form>
                <div id="gridResponse" class="response" style="display: none;"></div>
            </div>

            <!-- Stop Limit -->
            <div class="order-section">
                <h2>🛑 Stop Limit Order</h2>
                <form id="stopLimitForm">
                    <div class="form-group">
                        <label>Symbol:</label>
                        <input type="text" id="stopLimitSymbol" value="BTCUSDT" required>
                    </div>
                    <div class="form-group">
                        <label>Side:</label>
                        <select id="stopLimitSide" required>
                            <option value="BUY">BUY</option>
                            <option value="SELL">SELL</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Quantity:</label>
                        <input type="number" id="stopLimitQuantity" step="0.000001" required>
                    </div>
                    <div class="form-group">
                        <label>Stop Price:</label>
                        <input type="number" id="stopLimitStopPrice" step="0.01" required>
                    </div>
                    <div class="form-group">
                        <label>Limit Price:</label>
                        <input type="number" id="stopLimitLimitPrice" step="0.01" required>
                    </div>
                    <button type="submit">Execute Stop Limit Order</button>
                </form>
                <div id="stopLimitResponse" class="response" style="display: none;"></div>
            </div>
        </div>

        <script>
            // Helper function to submit forms
            async function submitOrder(formId, url, responseId) {
                const form = document.getElementById(formId);
                const formData = new FormData(form);
                const data = Object.fromEntries(formData.entries());

                // Convert numeric fields
                const numericFields = ['quantity', 'price', 'total_quantity', 'duration_minutes',
                                     'num_slices', 'lower_price', 'upper_price', 'num_grids',
                                     'quantity_per_grid', 'stop_price', 'stop_limit_price', 'limit_price'];

                numericFields.forEach(field => {
                    if (data[field]) {
                        data[field] = parseFloat(data[field]);
                    }
                });

                try {
                    const response = await fetch(url, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(data)
                    });

                    const result = await response.json();
                    const responseDiv = document.getElementById(responseId);
                    responseDiv.style.display = 'block';
                    responseDiv.className = 'response ' + (result.status === 'success' ? 'success' : 'error');
                    responseDiv.textContent = JSON.stringify(result, null, 2);
                } catch (error) {
                    const responseDiv = document.getElementById(responseId);
                    responseDiv.style.display = 'block';
                    responseDiv.className = 'response error';
                    responseDiv.textContent = 'Error: ' + error.message;
                }
            }

            // Form event listeners
            document.getElementById('marketForm').addEventListener('submit', function(e) {
                e.preventDefault();
                submitOrder('marketForm', '/api/orders/market', 'marketResponse');
            });

            document.getElementById('limitForm').addEventListener('submit', function(e) {
                e.preventDefault();
                submitOrder('limitForm', '/api/orders/limit', 'limitResponse');
            });

            document.getElementById('ocoForm').addEventListener('submit', function(e) {
                e.preventDefault();
                submitOrder('ocoForm', '/api/orders/oco', 'ocoResponse');
            });

            document.getElementById('twapForm').addEventListener('submit', function(e) {
                e.preventDefault();
                submitOrder('twapForm', '/api/orders/twap', 'twapResponse');
            });

            document.getElementById('gridForm').addEventListener('submit', function(e) {
                e.preventDefault();
                submitOrder('gridForm', '/api/orders/grid', 'gridResponse');
            });

            document.getElementById('stopLimitForm').addEventListener('submit', function(e) {
                e.preventDefault();
                submitOrder('stopLimitForm', '/api/orders/stop-limit', 'stopLimitResponse');
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "testnet": config.testnet,
        "version": "1.0.0"
    }

@app.post("/api/orders/market")
async def place_market_order(request: MarketOrderRequest):
    """Execute a market order"""
    try:
        validator.validate_symbol(request.symbol)
        validator.validate_side(request.side)
        validator.validate_quantity(request.quantity)

        logger.info(f"API: Market order - {request.side} {request.quantity} {request.symbol}")
        result = market_handler.place_market_order(request.symbol, request.side, request.quantity)

        return result
    except Exception as e:
        logger.error(f"API Market order error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/orders/limit")
async def place_limit_order(request: LimitOrderRequest):
    """Execute a limit order"""
    try:
        validator.validate_symbol(request.symbol)
        validator.validate_side(request.side)
        validator.validate_quantity(request.quantity)
        validator.validate_price(request.price)

        logger.info(f"API: Limit order - {request.side} {request.quantity} {request.symbol} @ {request.price}")
        result = limit_handler.place_limit_order(
            request.symbol, request.side, request.quantity,
            request.price, request.time_in_force
        )

        return result
    except Exception as e:
        logger.error(f"API Limit order error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/orders/stop-limit")
async def place_stop_limit_order(request: StopLimitOrderRequest):
    """Execute a stop-limit order"""
    try:
        validator.validate_symbol(request.symbol)
        validator.validate_side(request.side)
        validator.validate_quantity(request.quantity)
        validator.validate_price(request.stop_price)
        validator.validate_price(request.limit_price)

        logger.info(f"API: Stop-limit order - {request.symbol} {request.side} {request.quantity}")
        result = stop_limit_handler.place_stop_limit_order(
            request.symbol, request.side, request.quantity,
            request.stop_price, request.limit_price
        )

        return result
    except Exception as e:
        logger.error(f"API Stop-limit order error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/orders/oco")
async def place_oco_order(request: OCOOrderRequest):
    """Execute an OCO order"""
    try:
        validator.validate_symbol(request.symbol)
        validator.validate_side(request.side)
        validator.validate_quantity(request.quantity)
        validator.validate_price(request.price)
        validator.validate_price(request.stop_price)
        validator.validate_price(request.stop_limit_price)

        logger.info(f"API: OCO order - {request.symbol} {request.side} {request.quantity}")
        result = oco_handler.place_oco_order(
            request.symbol, request.side, request.quantity,
            request.price, request.stop_price, request.stop_limit_price
        )

        return result
    except Exception as e:
        logger.error(f"API OCO order error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/orders/twap")
async def execute_twap_strategy(request: TWAPOrderRequest):
    """Execute TWAP strategy"""
    try:
        validator.validate_symbol(request.symbol)
        validator.validate_side(request.side)
        validator.validate_quantity(request.total_quantity)

        if request.num_slices < 2:
            raise ValueError("Number of slices must be at least 2")
        if request.duration_minutes < 1:
            raise ValueError("Duration must be at least 1 minute")

        logger.info(f"API: TWAP strategy - {request.symbol} {request.side} {request.total_quantity} over {request.duration_minutes}min in {request.num_slices} slices")

        # Run in background since TWAP takes time
        result = twap_strategy.run_twap(
            request.symbol, request.side, request.total_quantity,
            request.duration_minutes, request.num_slices
        )

        return result
    except Exception as e:
        logger.error(f"API TWAP error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/orders/grid")
async def execute_grid_strategy(request: GridOrderRequest):
    """Execute grid trading strategy"""
    try:
        validator.validate_symbol(request.symbol)
        validator.validate_price(request.lower_price)
        validator.validate_price(request.upper_price)
        validator.validate_quantity(request.quantity_per_grid)

        if request.upper_price <= request.lower_price:
            raise ValueError("Upper price must be greater than lower price")
        if request.num_grids < 2:
            raise ValueError("Number of grids must be at least 2")

        logger.info(f"API: Grid strategy - {request.symbol} range {request.lower_price}-{request.upper_price} with {request.num_grids} grids")

        result = grid_strategy.setup_grid(
            request.symbol, request.lower_price, request.upper_price,
            request.num_grids, request.quantity_per_grid
        )

        return result
    except Exception as e:
        logger.error(f"API Grid error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/orders")
async def get_order_status():
    """Get current orders status"""
    try:
        # This would require implementing order status retrieval
        # For now, return mock data
        return {
            "status": "info",
            "message": "Order status endpoint - implement order tracking",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Order status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Binance Futures Order Bot Web Server...")
    print("📱 Web Interface: http://localhost:8000")
    print("🔗 API Docs: http://localhost:8000/docs")
    print("💡 Testnet Mode:", config.testnet)
    uvicorn.run(app, host="0.0.0.0", port=8000)
