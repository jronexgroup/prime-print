from typing import Dict, Set

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self._connections: Dict[str, WebSocket] = {}

    async def connect(self, device_id: str, websocket: WebSocket):
        await websocket.accept()
        self._connections[device_id] = websocket

    def disconnect(self, device_id: str):
        self._connections.pop(device_id, None)

    async def send_to_device(self, device_id: str, message: dict):
        ws = self._connections.get(device_id)
        if ws:
            await ws.send_json(message)

    async def broadcast_to_shop(self, shop_id: str, message: dict, device_map: Dict[str, str]):
        for device_id, mapped_shop in device_map.items():
            if mapped_shop == shop_id:
                await self.send_to_device(device_id, message)

    def is_connected(self, device_id: str) -> bool:
        return device_id in self._connections

    @property
    def active_connections(self) -> int:
        return len(self._connections)


manager = ConnectionManager()
