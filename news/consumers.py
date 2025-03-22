import json
import asyncio
from datetime import datetime
from channels.generic.websocket import AsyncWebsocketConsumer
from vnstock import Vnstock




class CandlestickConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.stock_code = self.scope['url_route']['kwargs']['stock_code']  # Get stock_code from URL
        self.list_stock = Vnstock().stock(source='VCI').listing.all_symbols()['ticker'].values
        if self.stock_code not in self.list_stock:
            await self.close(code=4000, reason=f"Stock code {self.stock_code} is not valid")
            return

        await self.accept()  # Accept the WebSocket connection
        print(f"WebSocket connected for stock: {self.stock_code}")

        # Fetch historical data (example)
        await self.send_historical_data()

    async def receive(self, text_data):
        # Handle any messages from the client (if needed)
        pass

    async def send_historical_data(self):
        # Example: Fetch historical data using vnstock
        stock = Vnstock().stock(symbol=self.stock_code, source='VCI')
        today = datetime.now().strftime("%Y-%m-%d")
        historical_data = stock.quote.history(start='2000-01-01', end=today)

        # Convert historical data to the required format
        historical = [
            {
                'time': row['time'].isoformat(),
                'open': row['open'],
                'high': row['high'],
                'low': row['low'],
                'close': row['close']
            } for index, row in historical_data.iterrows()
        ]

        # Send historical data to the client
        await self.send(text_data=json.dumps({
            'historical': historical
        }))
        asyncio.create_task(self.send_realtime_data())
        
    async def send_realtime_data(self):
        pass
