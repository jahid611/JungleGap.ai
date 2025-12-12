"""
JungleGap.ai - Backend Engine
WebSocket server integrating VisionEngine and Riot LCU API.
"""

import asyncio
import json
import threading
from datetime import datetime
from typing import Optional, Set

import requests
import urllib3
import websockets
from websockets.server import WebSocketServerProtocol

from vision import VisionEngine, Detection

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


class JungleGapServer:
    """Main WebSocket server orchestrating Vision Engine and LCU API."""
    
    def __init__(
        self, 
        host: str = "localhost", 
        port: int = 8765,
        model_path: Optional[str] = None,
        use_mock: bool = True
    ):
        self.host = host
        self.port = port
        self.connected_clients: Set[WebSocketServerProtocol] = set()
        
        self.lcu_client = RiotLCUClient()
        self.vision_engine = VisionEngine(
            model_path=model_path,
            use_mock=use_mock
        )
        
        # Shared state between threads
        self._running = False
        self._latest_detection: Optional[Detection] = None
        self._detection_lock = threading.Lock()

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

    def _vision_thread(self):
        """
        Background thread running the Vision Engine.
        Updates _latest_detection when enemy jungler is spotted.
        """
        print("[Vision] Thread started")
        
        for detection in self.vision_engine.run_loop(fps=10):
            if not self._running:
                break
            
            with self._detection_lock:
                self._latest_detection = detection
        
        print("[Vision] Thread stopped")

    async def main_loop(self):
        """Main async loop: check for detections and broadcast alerts."""
        while self._running:
            # Get game time from Riot API
            game_time = self.lcu_client.get_game_time()
            
            # Check for new detection from vision thread
            detection = None
            with self._detection_lock:
                if self._latest_detection:
                    detection = self._latest_detection
                    self._latest_detection = None  # Consume detection
            
            if detection:
                alert = {
                    "type": "alert",
                    "champion": detection.champion,
                    "location": detection.location,
                    "confidence": detection.confidence,
                    "game_time": game_time,
                    "timestamp": datetime.now().isoformat()
                }
                print(f"[ALERT] {detection.champion} spotted at {detection.location} ({detection.confidence:.0%})")
                await self.broadcast(alert)
            else:
                # Send heartbeat
                await self.broadcast({
                    "type": "heartbeat",
                    "game_time": game_time,
                    "in_game": game_time is not None
                })
            
            await asyncio.sleep(0.1)  # 10 updates per second

    async def start(self):
        self._running = True
        
        # Start Vision Engine in background thread
        vision_thread = threading.Thread(target=self._vision_thread, daemon=True)
        vision_thread.start()
        
        print("=" * 50)
        print("  JungleGap.ai - Backend Engine")
        print("=" * 50)
        print(f"[WS] Server starting on ws://{self.host}:{self.port}")
        print(f"[MODE] {'Mock Detection' if self.vision_engine.use_mock else 'YOLO Detection'}")
        print("[INFO] Press Ctrl+C to stop")
        print("=" * 50)
        
        async with websockets.serve(self.handler, self.host, self.port):
            await self.main_loop()

    def stop(self):
        self._running = False


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="JungleGap.ai Backend")
    parser.add_argument("--model", type=str, default=None, help="Path to YOLO model (.pt)")
    parser.add_argument("--mock", action="store_true", help="Use mock detection for testing")
    parser.add_argument("--port", type=int, default=8765, help="WebSocket port")
    args = parser.parse_args()
    
    # Use mock if no model provided or --mock flag
    use_mock = args.mock or args.model is None
    
    server = JungleGapServer(
        port=args.port,
        model_path=args.model,
        use_mock=use_mock
    )
    
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        server.stop()
        print("\n[Server] Shutdown complete.")


if __name__ == "__main__":
    main()
