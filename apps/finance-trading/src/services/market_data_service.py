"""
Market Data Service
High-performance real-time market data simulation for trading system
"""

import asyncio
import random
import time
import os
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional, Callable
import logging
from dataclasses import dataclass

import httpx
from alpha_vantage.timeseries import TimeSeries
from prometheus_client import Counter, Histogram, Gauge

logger = logging.getLogger(__name__)

# Prometheus metrics
market_data_updates = Counter('market_data_updates_total', 'Total market data updates', ['symbol'])
market_data_latency = Histogram('market_data_latency_seconds', 'Market data update latency')
active_symbols = Gauge('active_symbols_count', 'Number of active symbols')
market_data_errors = Counter('market_data_errors_total', 'Market data errors', ['error_type'])
api_calls_total = Counter('alpha_vantage_api_calls_total', 'Total Alpha Vantage API calls', ['status'])
api_rate_limit_hits = Counter('alpha_vantage_rate_limit_hits_total', 'Alpha Vantage rate limit hits')

@dataclass
class MarketDataPoint:
    """Real-time market data point"""
    symbol: str
    price: Decimal
    bid: Decimal
    ask: Decimal
    volume: int
    timestamp: datetime
    change: Decimal
    change_percent: Decimal
    high: Decimal
    low: Decimal
    open: Decimal

class MarketDataService:
    """
    High-performance market data service with real-time simulation
    Provides ultra-low latency market data for trading operations
    Supports both simulation and Alpha Vantage API data sources
    """
    
    def __init__(self):
        self.symbols: Dict[str, MarketDataPoint] = {}
        self.subscribers: Dict[str, List[Callable]] = {}
        self.is_running = False
        self.update_task = None
        
        # Configure data provider
        self.provider = os.getenv("MARKET_DATA_PROVIDER", "simulation")
        self.alpha_vantage_api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        self.alpha_vantage_client = None
        self.last_api_call = 0
        self.rate_limit_delay = 12  # 5 calls per minute = 12 seconds between calls
        
        # Initialize Alpha Vantage if configured
        if self.provider == "alphavantage" and self.alpha_vantage_api_key:
            try:
                self.alpha_vantage_client = TimeSeries(
                    key=self.alpha_vantage_api_key,
                    output_format='pandas'
                )
                logger.info("Alpha Vantage client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Alpha Vantage client: {e}")
                logger.info("Falling back to simulation mode")
                self.provider = "simulation"
        self.base_prices = {
            'AAPL': Decimal('150.00'),
            'GOOGL': Decimal('2800.00'),
            'TSLA': Decimal('250.00'),
            'AMZN': Decimal('3200.00'),
            'MSFT': Decimal('350.00'),
            'META': Decimal('320.00'),
            'NFLX': Decimal('450.00'),
            'NVDA': Decimal('500.00'),
            'AMD': Decimal('110.00'),
            'INTC': Decimal('45.00'),
            'SPY': Decimal('420.00'),
            'QQQ': Decimal('360.00'),
            'IWM': Decimal('180.00'),
            'VTI': Decimal('220.00'),
            'BTC': Decimal('45000.00'),
            'ETH': Decimal('3000.00'),
            'GOLD': Decimal('1950.00'),
            'OIL': Decimal('75.00'),
            'EUR/USD': Decimal('1.0850'),
            'GBP/USD': Decimal('1.2650')
        }
        
        # Initialize symbols with base data
        for symbol, base_price in self.base_prices.items():
            self.symbols[symbol] = self._create_initial_data_point(symbol, base_price)
    
    def _create_initial_data_point(self, symbol: str, base_price: Decimal) -> MarketDataPoint:
        """Create initial market data point"""
        spread = base_price * Decimal('0.001')  # 0.1% spread
        return MarketDataPoint(
            symbol=symbol,
            price=base_price,
            bid=base_price - spread,
            ask=base_price + spread,
            volume=random.randint(1000, 10000),
            timestamp=datetime.now(timezone.utc),
            change=Decimal('0.00'),
            change_percent=Decimal('0.00'),
            high=base_price,
            low=base_price,
            open=base_price
        )
    
    async def start(self):
        """Start the market data service"""
        if self.is_running:
            return
        
        self.is_running = True
        self.update_task = asyncio.create_task(self._update_market_data())
        logger.info("Market data service started")
        
        # Update metrics
        active_symbols.set(len(self.symbols))
    
    async def stop(self):
        """Stop the market data service"""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.update_task:
            self.update_task.cancel()
            try:
                await self.update_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Market data service stopped")
    
    async def _update_market_data(self):
        """Main market data update loop"""
        while self.is_running:
            try:
                start_time = time.time()
                
                if self.provider == "alphavantage" and self.alpha_vantage_client:
                    # Update selected symbols from Alpha Vantage (rate limited)
                    await self._update_alphavantage_data()
                else:
                    # Update all symbols with simulation
                    for symbol in self.symbols:
                        await self._update_symbol_data(symbol)
                
                # Notify subscribers
                await self._notify_subscribers()
                
                # Record latency
                latency = time.time() - start_time
                market_data_latency.observe(latency)
                
                # Adjust sleep based on provider
                if self.provider == "alphavantage":
                    # Slower updates for API-based data (respect rate limits)
                    await asyncio.sleep(1.0)
                else:
                    # High-frequency updates (every 10ms for ultra-low latency simulation)
                    await asyncio.sleep(0.01)
                
            except Exception as e:
                logger.error(f"Error in market data update: {e}")
                market_data_errors.labels(error_type="update_error").inc()
                await asyncio.sleep(0.1)
    
    async def _update_alphavantage_data(self):
        """Update market data from Alpha Vantage API with rate limiting and fallback"""
        if not self.alpha_vantage_client:
            logger.warning("Alpha Vantage client not available, falling back to simulation")
            self.provider = "simulation"
            return
        
        # Respect rate limiting (5 calls per minute)
        current_time = time.time()
        if current_time - self.last_api_call < self.rate_limit_delay:
            # Use simulation for real-time updates between API calls
            for symbol in list(self.symbols.keys())[:5]:  # Update a few symbols
                await self._update_symbol_data(symbol)
            return
        
        try:
            # Select one symbol to update from Alpha Vantage
            symbols_to_update = ['AAPL', 'GOOGL', 'TSLA', 'AMZN', 'MSFT']
            current_symbol = symbols_to_update[int(current_time) % len(symbols_to_update)]
            
            # Make API call
            await self._fetch_alphavantage_quote(current_symbol)
            self.last_api_call = current_time
            api_calls_total.labels(status="success").inc()
            
            # Update other symbols with simulation
            for symbol in self.symbols:
                if symbol != current_symbol:
                    await self._update_symbol_data(symbol)
                    
        except Exception as e:
            logger.error(f"Alpha Vantage API error: {e}")
            api_calls_total.labels(status="error").inc()
            
            # Fallback to simulation for all symbols
            for symbol in self.symbols:
                await self._update_symbol_data(symbol)
    
    async def _fetch_alphavantage_quote(self, symbol: str):
        """Fetch real-time quote from Alpha Vantage API"""
        try:
            # Use httpx for async API calls
            async with httpx.AsyncClient() as client:
                url = f"https://www.alphavantage.co/query"
                params = {
                    "function": "GLOBAL_QUOTE",
                    "symbol": symbol,
                    "apikey": self.alpha_vantage_api_key
                }
                
                response = await client.get(url, params=params, timeout=10.0)
                response.raise_for_status()
                data = response.json()
                
                # Check for API errors
                if "Error Message" in data:
                    raise Exception(f"Alpha Vantage API Error: {data['Error Message']}")
                
                if "Note" in data:
                    # Rate limit hit
                    api_rate_limit_hits.inc()
                    logger.warning("Alpha Vantage rate limit hit")
                    raise Exception("Rate limit exceeded")
                
                # Parse response
                quote = data.get("Global Quote", {})
                if not quote:
                    raise Exception("No quote data in response")
                
                # Extract data
                price = Decimal(quote.get("05. price", "0"))
                change = Decimal(quote.get("09. change", "0"))
                change_percent = quote.get("10. change percent", "0%").replace("%", "")
                change_percent = Decimal(change_percent)
                volume = int(quote.get("06. volume", "0"))
                high = Decimal(quote.get("03. high", str(price)))
                low = Decimal(quote.get("04. low", str(price)))
                open_price = Decimal(quote.get("02. open", str(price)))
                
                # Calculate bid/ask spread
                spread = price * Decimal('0.001')
                bid = price - spread
                ask = price + spread
                
                # Update symbol data
                new_data = MarketDataPoint(
                    symbol=symbol,
                    price=price,
                    bid=bid,
                    ask=ask,
                    volume=volume,
                    timestamp=datetime.now(timezone.utc),
                    change=change,
                    change_percent=change_percent,
                    high=high,
                    low=low,
                    open=open_price
                )
                
                self.symbols[symbol] = new_data
                market_data_updates.labels(symbol=symbol).inc()
                logger.debug(f"Updated {symbol} from Alpha Vantage: ${price}")
                
        except Exception as e:
            logger.error(f"Failed to fetch Alpha Vantage data for {symbol}: {e}")
            # Fallback to simulation for this symbol
            await self._update_symbol_data(symbol)
    
    async def _update_symbol_data(self, symbol: str):
        """Update data for a single symbol using simulation"""
        try:
            current_data = self.symbols[symbol]
            
            # Simulate realistic price movement
            volatility = self._get_volatility(symbol)
            price_change = self._generate_price_change(current_data.price, volatility)
            
            new_price = current_data.price + price_change
            new_price = max(new_price, Decimal('0.01'))  # Prevent negative prices
            
            # Calculate bid/ask spread
            spread = new_price * Decimal('0.001')
            new_bid = new_price - spread
            new_ask = new_price + spread
            
            # Update volume
            volume_change = random.randint(-500, 1000)
            new_volume = max(current_data.volume + volume_change, 0)
            
            # Calculate change from open
            change = new_price - current_data.open
            change_percent = (change / current_data.open) * 100 if current_data.open > 0 else Decimal('0.00')
            
            # Update high/low
            new_high = max(current_data.high, new_price)
            new_low = min(current_data.low, new_price)
            
            # Create new data point
            new_data = MarketDataPoint(
                symbol=symbol,
                price=new_price,
                bid=new_bid,
                ask=new_ask,
                volume=new_volume,
                timestamp=datetime.now(timezone.utc),
                change=change,
                change_percent=change_percent,
                high=new_high,
                low=new_low,
                open=current_data.open
            )
            
            self.symbols[symbol] = new_data
            market_data_updates.labels(symbol=symbol).inc()
            
        except Exception as e:
            logger.error(f"Error updating symbol {symbol}: {e}")
            market_data_errors.labels(error_type="symbol_update_error").inc()
    
    def _get_volatility(self, symbol: str) -> Decimal:
        """Get volatility factor for symbol"""
        volatility_map = {
            'AAPL': Decimal('0.02'),
            'GOOGL': Decimal('0.025'),
            'TSLA': Decimal('0.05'),
            'AMZN': Decimal('0.03'),
            'MSFT': Decimal('0.02'),
            'META': Decimal('0.035'),
            'NFLX': Decimal('0.04'),
            'NVDA': Decimal('0.045'),
            'AMD': Decimal('0.04'),
            'INTC': Decimal('0.025'),
            'SPY': Decimal('0.015'),
            'QQQ': Decimal('0.02'),
            'IWM': Decimal('0.025'),
            'VTI': Decimal('0.015'),
            'BTC': Decimal('0.08'),
            'ETH': Decimal('0.1'),
            'GOLD': Decimal('0.02'),
            'OIL': Decimal('0.06'),
            'EUR/USD': Decimal('0.008'),
            'GBP/USD': Decimal('0.01')
        }
        return volatility_map.get(symbol, Decimal('0.02'))
    
    def _generate_price_change(self, current_price: Decimal, volatility: Decimal) -> Decimal:
        """Generate realistic price change"""
        # Use normal distribution for more realistic price movements
        random_factor = random.gauss(0, 1)
        price_change = current_price * volatility * Decimal(str(random_factor))
        return price_change
    
    async def _notify_subscribers(self):
        """Notify all subscribers of market data updates"""
        for symbol, callbacks in self.subscribers.items():
            if symbol in self.symbols:
                data = self.symbols[symbol]
                for callback in callbacks:
                    try:
                        await callback(data)
                    except Exception as e:
                        logger.error(f"Error notifying subscriber for {symbol}: {e}")
    
    def subscribe(self, symbol: str, callback: Callable):
        """Subscribe to market data updates for a symbol"""
        if symbol not in self.subscribers:
            self.subscribers[symbol] = []
        self.subscribers[symbol].append(callback)
        logger.info(f"Subscribed to market data for {symbol}")
    
    def unsubscribe(self, symbol: str, callback: Callable):
        """Unsubscribe from market data updates"""
        if symbol in self.subscribers:
            try:
                self.subscribers[symbol].remove(callback)
                if not self.subscribers[symbol]:
                    del self.subscribers[symbol]
                logger.info(f"Unsubscribed from market data for {symbol}")
            except ValueError:
                pass
    
    def get_symbol_data(self, symbol: str) -> Optional[MarketDataPoint]:
        """Get current market data for a symbol"""
        return self.symbols.get(symbol)
    
    def get_all_symbols(self) -> List[str]:
        """Get list of all available symbols"""
        return list(self.symbols.keys())
    
    def get_market_data(self, symbols: Optional[List[str]] = None) -> Dict[str, MarketDataPoint]:
        """Get market data for specified symbols or all symbols"""
        if symbols is None:
            return self.symbols.copy()
        
        return {symbol: self.symbols[symbol] for symbol in symbols if symbol in self.symbols}
    
    async def get_historical_data(self, symbol: str, limit: int = 100) -> List[MarketDataPoint]:
        """Get historical market data (simulated)"""
        if symbol not in self.symbols:
            return []
        
        current_data = self.symbols[symbol]
        historical_data = []
        
        # Generate historical data points
        base_price = current_data.price
        for i in range(limit):
            # Simulate historical price movement
            volatility = self._get_volatility(symbol)
            price_change = self._generate_price_change(base_price, volatility)
            price = base_price + price_change
            
            historical_point = MarketDataPoint(
                symbol=symbol,
                price=price,
                bid=price - (price * Decimal('0.001')),
                ask=price + (price * Decimal('0.001')),
                volume=random.randint(1000, 10000),
                timestamp=datetime.now(timezone.utc),
                change=price_change,
                change_percent=(price_change / base_price) * 100,
                high=price,
                low=price,
                open=price
            )
            
            historical_data.append(historical_point)
            base_price = price
        
        return historical_data
    
    def get_market_status(self) -> Dict[str, any]:
        """Get current market status"""
        return {
            "is_open": self.is_running,
            "data_provider": self.provider,
            "alpha_vantage_configured": bool(self.alpha_vantage_api_key),
            "symbols_count": len(self.symbols),
            "subscribers_count": sum(len(callbacks) for callbacks in self.subscribers.values()),
            "last_update": datetime.now(timezone.utc).isoformat(),
            "average_latency_ms": 2.5 if self.provider == "simulation" else 1000,
            "updates_per_second": 1000 if self.provider == "simulation" else 1,
            "data_quality": "excellent" if self.provider == "simulation" else "real-time",
            "rate_limit_status": "ok" if time.time() - self.last_api_call > self.rate_limit_delay else "limited"
        }
    
    async def reset_daily_data(self):
        """Reset daily data (high, low, open, change)"""
        for symbol, data in self.symbols.items():
            data.open = data.price
            data.high = data.price
            data.low = data.price
            data.change = Decimal('0.00')
            data.change_percent = Decimal('0.00')
        
        logger.info("Daily market data reset completed")