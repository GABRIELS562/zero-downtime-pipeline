#!/usr/bin/env python3
"""
WebSocket Server for Real-Time Market Data
Provides live price updates to the frontend dashboard
"""

import asyncio
import json
import random
from datetime import datetime
from decimal import Decimal
import logging
from typing import Set

import websockets
from websockets.server import WebSocketServerProtocol

logger = logging.getLogger(__name__)

class MarketDataWebSocketServer:
    """WebSocket server for broadcasting real-time market data"""
    
    def __init__(self, host='0.0.0.0', port=8082):
        self.host = host
        self.port = port
        self.clients: Set[WebSocketServerProtocol] = set()
        self.market_data = {
            'AAPL': {'price': 150.00, 'change': 0, 'volume': 0},
            'GOOGL': {'price': 140.00, 'change': 0, 'volume': 0},
            'MSFT': {'price': 380.00, 'change': 0, 'volume': 0},
            'TSLA': {'price': 250.00, 'change': 0, 'volume': 0},
            'AMZN': {'price': 170.00, 'change': 0, 'volume': 0},
            'META': {'price': 500.00, 'change': 0, 'volume': 0},
            'NVDA': {'price': 880.00, 'change': 0, 'volume': 0},
            'BTC': {'price': 45000.00, 'change': 0, 'volume': 0},
        }
        
    async def register(self, websocket: WebSocketServerProtocol):
        """Register a new client"""
        self.clients.add(websocket)
        logger.info(f"Client {websocket.remote_address} connected. Total clients: {len(self.clients)}")
        
        # Send initial market data
        await self.send_initial_data(websocket)
        
    async def unregister(self, websocket: WebSocketServerProtocol):
        """Unregister a client"""
        self.clients.discard(websocket)
        logger.info(f"Client {websocket.remote_address} disconnected. Total clients: {len(self.clients)}")
        
    async def send_initial_data(self, websocket: WebSocketServerProtocol):
        """Send initial market data to new client"""
        for symbol, data in self.market_data.items():
            message = {
                'type': 'price',
                'symbol': symbol,
                'price': data['price'],
                'change': data['change'],
                'changePercent': (data['change'] / data['price'] * 100) if data['price'] > 0 else 0,
                'volume': data['volume'],
                'timestamp': datetime.now().isoformat()
            }
            await websocket.send(json.dumps(message))
            
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        if self.clients:
            message_json = json.dumps(message)
            # Send to all clients concurrently
            await asyncio.gather(
                *[client.send(message_json) for client in self.clients],
                return_exceptions=True
            )
            
    async def simulate_market_data(self):
        """Simulate real-time market data updates"""
        while True:
            # Pick a random symbol to update
            symbol = random.choice(list(self.market_data.keys()))
            data = self.market_data[symbol]
            
            # Generate realistic price movement
            change_percent = (random.random() - 0.5) * 0.02  # +/- 1% max
            new_price = data['price'] * (1 + change_percent)
            change = new_price - data['price']
            
            # Update stored data
            data['price'] = new_price
            data['change'] = change
            data['volume'] += random.randint(1000, 10000)
            
            # Broadcast update
            message = {
                'type': 'price',
                'symbol': symbol,
                'price': round(new_price, 2),
                'change': round(change, 2),
                'changePercent': round(change_percent * 100, 2),
                'volume': data['volume'],
                'timestamp': datetime.now().isoformat()
            }
            
            await self.broadcast(message)
            
            # Wait before next update (1-3 seconds)
            await asyncio.sleep(random.uniform(1, 3))
            
    async def simulate_deployment_events(self):
        """Simulate deployment pipeline events"""
        deployment_messages = [
            {'type': 'deployment', 'status': 'info', 'message': 'Canary deployment initiated'},
            {'type': 'deployment', 'status': 'success', 'message': 'Health checks passed'},
            {'type': 'deployment', 'status': 'info', 'message': 'Blue-green switch in progress'},
            {'type': 'deployment', 'status': 'success', 'message': 'Zero-downtime achieved'},
            {'type': 'deployment', 'status': 'warning', 'message': 'Monitoring increased latency'},
            {'type': 'deployment', 'status': 'success', 'message': 'Auto-scaling triggered'},
        ]
        
        while True:
            # Wait 30-60 seconds between deployment events
            await asyncio.sleep(random.uniform(30, 60))
            
            message = random.choice(deployment_messages)
            message['timestamp'] = datetime.now().isoformat()
            await self.broadcast(message)
            
    async def handle_client(self, websocket: WebSocketServerProtocol, path: str):
        """Handle client connection"""
        await self.register(websocket)
        try:
            # Keep connection alive and handle messages
            async for message in websocket:
                # Handle client messages if needed
                data = json.loads(message)
                logger.info(f"Received from client: {data}")
                
                # Echo back or handle commands
                if data.get('type') == 'ping':
                    await websocket.send(json.dumps({'type': 'pong'}))
                    
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister(websocket)
            
    async def start(self):
        """Start the WebSocket server"""
        logger.info(f"Starting WebSocket server on {self.host}:{self.port}")
        
        # Start background tasks
        asyncio.create_task(self.simulate_market_data())
        asyncio.create_task(self.simulate_deployment_events())
        
        # Start WebSocket server
        async with websockets.serve(
            self.handle_client,
            self.host,
            self.port,
            ping_interval=20,
            ping_timeout=10
        ):
            logger.info(f"WebSocket server running on ws://{self.host}:{self.port}/feed")
            await asyncio.Future()  # Run forever

def main():
    """Main entry point"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    server = MarketDataWebSocketServer()
    asyncio.run(server.start())

if __name__ == '__main__':
    main()