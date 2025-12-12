"""
JungleGap.ai - Vision Engine
Screen capture and YOLOv8-based minimap analysis with dynamic resolution support.
"""

import time
from dataclasses import dataclass
from typing import Optional, Tuple
import ctypes

import numpy as np
import mss

# Optional: YOLO import (comment out if not using real detection)
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("[Vision] Warning: ultralytics not installed. Using mock detection.")


def get_screen_resolution() -> Tuple[int, int]:
    """
    Get the primary monitor resolution using Windows API.
    Falls back to 1920x1080 if detection fails.
    """
    try:
        user32 = ctypes.windll.user32
        user32.SetProcessDPIAware()
        width = user32.GetSystemMetrics(0)
        height = user32.GetSystemMetrics(1)
        return width, height
    except Exception:
        return 1920, 1080


@dataclass
class MinimapRegion:
    """
    Screen coordinates for the minimap.
    Automatically calculated based on screen resolution.
    
    League minimap is always in the bottom-right corner:
    - Starts at ~85% of screen width
    - Starts at ~73% of screen height
    - Size is ~14.5% of screen width (square)
    """
    left: int
    top: int
    width: int
    height: int
    
    @classmethod
    def auto_detect(cls) -> "MinimapRegion":
        """Create MinimapRegion with auto-detected resolution."""
        screen_width, screen_height = get_screen_resolution()
        
        # Minimap position ratios (consistent across resolutions)
        minimap_size = int(screen_width * 0.145)  # ~14.5% of width
        left = int(screen_width * 0.85)
        top = int(screen_height * 0.73)
        
        print(f"[Vision] Screen: {screen_width}x{screen_height}")
        print(f"[Vision] Minimap region: ({left}, {top}) - {minimap_size}x{minimap_size}")
        
        return cls(
            left=left,
            top=top,
            width=minimap_size,
            height=minimap_size
        )


@dataclass
class Detection:
    """Represents a detected enemy jungler."""
    champion: str
    confidence: float
    location: str
    bbox: Tuple[int, int, int, int]


class VisionEngine:
    """
    Handles screen capture and YOLOv8-based enemy jungler detection.
    Supports dynamic resolution and production-ready paths.
    """
    
    # Class ID to champion name mapping (customize based on your trained model)
    CLASS_NAMES = {
        0: "Lee Sin",
        1: "Elise",
        2: "Graves",
        3: "Nidalee",
        4: "Viego",
        5: "Kha'Zix",
        6: "Rek'Sai",
        7: "Hecarim",
        8: "Jarvan IV",
        9: "Vi",
        # Add more champions as you train them
    }
    
    # Minimap zones for location detection (normalized 0-1 coordinates)
    LOCATION_ZONES = {
        "BARON PIT": (0.0, 0.0, 0.25, 0.25),
        "TOP RIVER": (0.15, 0.15, 0.45, 0.45),
        "BLUE TOPSIDE": (0.0, 0.25, 0.35, 0.55),
        "BLUE BOTSIDE": (0.0, 0.55, 0.35, 0.85),
        "RED TOPSIDE": (0.65, 0.15, 1.0, 0.45),
        "RED BOTSIDE": (0.65, 0.45, 1.0, 0.75),
        "BOT RIVER": (0.55, 0.55, 0.85, 0.85),
        "DRAGON PIT": (0.75, 0.75, 1.0, 1.0),
    }

    def __init__(
        self,
        model_path: Optional[str] = None,
        minimap_region: Optional[MinimapRegion] = None,
        confidence_threshold: float = 0.6,
        use_mock: bool = False
    ):
        """
        Initialize the Vision Engine.
        
        Args:
            model_path: Path to trained YOLOv8 model (.pt file).
            minimap_region: Custom minimap region, or auto-detect if None.
            confidence_threshold: Minimum confidence for detections.
            use_mock: Force mock detection mode for testing.
        """
        self.minimap_region = minimap_region or MinimapRegion.auto_detect()
        self.confidence_threshold = confidence_threshold
        self.screen_capture = mss.mss()
        self.use_mock = use_mock
        self.model = None
        
        # Load YOLO model if available and not in mock mode
        if not use_mock and YOLO_AVAILABLE and model_path:
            try:
                self.model = YOLO(model_path)
                print(f"[Vision] YOLO model loaded from {model_path}")
            except Exception as e:
                print(f"[Vision] Failed to load model: {e}")
                print("[Vision] Falling back to mock detection")
                self.use_mock = True
        elif not use_mock:
            print("[Vision] No model path provided, using mock detection")
            self.use_mock = True

    def capture_minimap(self) -> np.ndarray:
        """
        Capture the minimap region of the screen.
        
        Returns:
            BGR numpy array of the minimap.
        """
        monitor = {
            "left": self.minimap_region.left,
            "top": self.minimap_region.top,
            "width": self.minimap_region.width,
            "height": self.minimap_region.height,
        }
        
        screenshot = self.screen_capture.grab(monitor)
        frame = np.array(screenshot)[:, :, :3]  # BGRA -> BGR
        
        return frame

    def _get_location_from_bbox(self, bbox: Tuple[int, int, int, int], frame_shape: Tuple[int, ...]) -> str:
        """
        Determine map location based on detection bounding box center.
        
        Args:
            bbox: (x1, y1, x2, y2) pixel coordinates.
            frame_shape: (height, width, ...) of the frame.
            
        Returns:
            Human-readable location string.
        """
        height, width = frame_shape[:2]
        center_x = (bbox[0] + bbox[2]) / 2 / width
        center_y = (bbox[1] + bbox[3]) / 2 / height
        
        for zone_name, (x1, y1, x2, y2) in self.LOCATION_ZONES.items():
            if x1 <= center_x <= x2 and y1 <= center_y <= y2:
                return zone_name
        
        return "JUNGLE"

    def detect(self, frame: np.ndarray) -> Optional[Detection]:
        """
        Run detection on a minimap frame.
        
        Args:
            frame: BGR numpy array of the minimap.
            
        Returns:
            Detection object if enemy jungler found, None otherwise.
        """
        if self.use_mock:
            return self._mock_detect()
        
        # Run YOLO inference
        results = self.model(frame, verbose=False)[0]
        
        # Find highest confidence detection
        best_detection = None
        best_confidence = 0
        
        for box in results.boxes:
            confidence = float(box.conf[0])
            
            if confidence >= self.confidence_threshold and confidence > best_confidence:
                class_id = int(box.cls[0])
                bbox = tuple(map(int, box.xyxy[0].tolist()))
                champion = self.CLASS_NAMES.get(class_id, f"Unknown({class_id})")
                location = self._get_location_from_bbox(bbox, frame.shape)
                
                best_detection = Detection(
                    champion=champion,
                    confidence=confidence,
                    location=location,
                    bbox=bbox
                )
                best_confidence = confidence
        
        return best_detection

    def _mock_detect(self) -> Optional[Detection]:
        """
        Mock detection for testing (10% chance per call).
        """
        import random
        if random.random() < 0.02:  # 2% chance per frame = ~1 alert per 5 seconds at 10 FPS
            champion = random.choice(list(self.CLASS_NAMES.values()))
            location = random.choice(list(self.LOCATION_ZONES.keys()))
            return Detection(
                champion=champion,
                confidence=round(random.uniform(0.75, 0.98), 2),
                location=location,
                bbox=(100, 50, 130, 80)
            )
        return None

    def run_loop(self, fps: int = 10):
        """
        Generator that yields detections at the specified FPS.
        
        Args:
            fps: Target frames per second.
            
        Yields:
            Detection objects when enemy jungler is spotted.
        """
        frame_time = 1.0 / fps
        
        print(f"[Vision] Starting detection loop at {fps} FPS")
        print(f"[Vision] Mode: {'MOCK' if self.use_mock else 'YOLO'}")
        
        while True:
            start = time.perf_counter()
            
            frame = self.capture_minimap()
            detection = self.detect(frame)
            
            if detection:
                yield detection
            
            # Maintain target FPS
            elapsed = time.perf_counter() - start
            sleep_time = max(0, frame_time - elapsed)
            time.sleep(sleep_time)


# Test the vision engine
if __name__ == "__main__":
    print("=" * 50)
    print("  JungleGap.ai - Vision Engine Test")
    print("=" * 50)
    
    engine = VisionEngine(use_mock=True)
    
    print("\n[Test] Running detection loop (Ctrl+C to stop)...")
    
    try:
        for detection in engine.run_loop(fps=10):
            print(f"[DETECTED] {detection.champion} at {detection.location} ({detection.confidence:.0%})")
    except KeyboardInterrupt:
        print("\n[Test] Stopped.")
