"""
JungleGap.ai - Backend Engine
WebSocket server with mock vision detection and Riot LCU API integration.
"""

import asyncio
import json
import random
import time
from datetime import datetime
from typing import Optional, Set

import requests
import urllib3
import websockets
from websockets.server import WebSocketServerProtocol

# Disable SSL warnings for Riot's self-signed certificate
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class RiotLCUClient:
    """Client for Riot's Live Client Data API (read-only)."""
    
    BASE_URL = "https://127.0.0.1:2999/liveclientdata"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.verify = False
    
    def get_game_time(self) -> Optional[float]:
        """Fetch current game time in seconds."""
        try:
            response = self.session.get(
                f"{self.BASE_URL}/gamestats",
                timeout=1.0
            )
            response.raise_for_status()
            data = response.json()
            return data.get("gameTime", 0.0)
        except requests.RequestException:
            return None
    
    def is_in_game(self) -> bool:
        """Check if player is currently in a game."""
        return self.get_game_time() is not None


class MockVisionEngine:
    """
    Simulates enemy jungler detection for testing.
    Sends a fake alert every ~10 seconds.
    """
    
    CHAMPIONS = ["Lee Sin", "Elise", "Graves", "Nidalee", "Viego", "Kha'Zix", "Rek'Sai", "Hecarim", "Jarvan IV", "Vi"]
    LOCATIONS = ["TOP RIVER", "BOT RIVER", "BLUE TOPSIDE", "BLUE BOTSIDE", "RED TOPSIDE", "RED BOTSIDE", "DRAGON PIT", "BARON PIT"]
    
    def __init__(self, interval: float = 10.0):
        self.interval = interval
        self._last_alert_time = 0
    
    def check_for_detection(self) -> Optional[dict]:
        """
        Simulate detection. Returns alert data ~every 10 seconds.
        """
        current_time = time.time()
        
        if current_time - self._last_alert_time >= self.interval:
            self._last_alert_time = current_time
            return {
                "champion": random.choice(self.CHAMPIONS),
                "location": random.choice(self.LOCATIONS),
                "confidence": round(random.uniform(0.75, 0.98), 2)
            }
        return None


class JungleGapServer:
    """Main WebSocket server orchestrating all components."""
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.connected_clients: Set[WebSocketServerProtocol] = set()
        
        self.lcu_client = RiotLCUClient()
        self.vision_engine = MockVisionEngine(interval=10.0)
        self._running = False

    async def register(self, websocket: WebSocketServerProtocol):
        self.connected_clients.add(websocket)
        print(f"[WS] Client connected. Total: {len(self.connected_clients)}")

    async def unregister(self, websocket: WebSocketServerProtocol):
        self.connected_clients.discard(websocket)
        print(f"[WS] Client disconnected. Total: {len(self.connected_clients)}")

    async def broadcast(self, message: dict):
        if not self.connected_clients:
            return
        payload = json.dumps(message)
        await asyncio.gather(
            *[client.send(payload) for client in self.connected_clients],
            return_exceptions=True
        )

    async def handler(self, websocket: WebSocketServerProtocol):
        await self.register(websocket)
        try:
            async for _ in websocket:
                pass  # Read-only server
        finally:
            await self.unregister(websocket)

    async def main_loop(self):
        """Main loop: check for detections and broadcast alerts."""
        while self._running:
            # Get game time from Riot API
            game_time = self.lcu_client.get_game_time()
            
            # Check for mock detection
            detection = self.vision_engine.check_for_detection()
            
            if detection:
                alert = {
                    "type": "alert",
                    "champion": detection["champion"],
                    "location": detection["location"],
                    "confidence": detection["confidence"],
                    "game_time": game_time,
                    "timestamp": datetime.now().isoformat()
                }
                print(f"[ALERT] {detection['champion']} spotted at {detection['location']}")
                await self.broadcast(alert)
            else:
                # Send heartbeat
                await self.broadcast({
                    "type": "heartbeat",
                    "game_time": game_time,
                    "in_game": game_time is not None
                })
            
            await asyncio.sleep(0.5)

    async def start(self):
        self._running = True
        print("=" * 50)
        print("  JungleGap.ai - Backend Engine")
        print("=" * 50)
        print(f"[WS] Server starting on ws://{self.host}:{self.port}")
        print("[MODE] Mock Vision Engine (alerts every ~10s)")
        print("[INFO] Press Ctrl+C to stop")
        print("=" * 50)
        
        async with websockets.serve(self.handler, self.host, self.port):
            await self.main_loop()

    def stop(self):
        self._running = False


def main():
    server = JungleGapServer()
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        server.stop()
        print("\n[Server] Shutdown complete.")


if __name__ == "__main__":
    main()
