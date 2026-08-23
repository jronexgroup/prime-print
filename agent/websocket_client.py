import asyncio
import json
import logging

import websockets

logger = logging.getLogger("runova_agent")


class WebSocketClient:
    def __init__(self, server_url: str, device_id: str, on_message=None):
        self.server_url = server_url
        self.device_id = device_id
        self.on_message = on_message
        self._ws = None
        self._running = False
        self._reconnect_delay = 1

    async def connect(self):
        self._running = True
        while self._running:
            try:
                url = f"{self.server_url}/ws/agent/{self.device_id}"
                async with websockets.connect(url) as ws:
                    self._ws = ws
                    self._reconnect_delay = 1
                    logger.info("Connected to server")

                    await ws.send(json.dumps({"type": "agent_ready"}))

                    async for message in ws:
                        try:
                            data = json.loads(message)
                            if self.on_message:
                                self.on_message(data)
                        except json.JSONDecodeError:
                            logger.warning("Invalid JSON received")

            except websockets.ConnectionClosed:
                logger.warning("Connection closed, reconnecting...")
            except Exception as e:
                logger.error(f"Connection error: {e}")

            if self._running:
                logger.info(f"Reconnecting in {self._reconnect_delay}s...")
                await asyncio.sleep(self._reconnect_delay)
                self._reconnect_delay = min(self._reconnect_delay * 2, 30)

    async def send(self, message: dict):
        if self._ws:
            try:
                await self._ws.send(json.dumps(message))
            except Exception as e:
                logger.error(f"Send error: {e}")

    def disconnect(self):
        self._running = False
