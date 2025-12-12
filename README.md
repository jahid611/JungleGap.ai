# JungleGap.ai

Real-time League of Legends jungle tracking overlay with Hextech-styled UI.

## Prerequisites

- Node.js 18+
- Python 3.10+
- Windows 10/11

## Quick Start

### 1. Install Dependencies

\`\`\`bash
# Frontend dependencies
npm install

# Backend dependencies
cd backend
pip install -r requirements.txt
cd ..
\`\`\`

### 2. Run in Development Mode

Open two terminals:

**Terminal 1 - Python Backend:**
\`\`\`bash
cd backend
python engine.py
\`\`\`

**Terminal 2 - Electron + React:**
\`\`\`bash
npm run electron-dev
\`\`\`

The overlay will appear with mock alerts every ~10 seconds.

## Build for Production

### Step 1: Compile Python to .exe

\`\`\`bash
cd backend
pyinstaller --onefile --noconsole engine.py
\`\`\`

This creates `backend/dist/engine.exe`

### Step 2: Build Electron Installer

\`\`\`bash
npm run dist
\`\`\`

This creates `dist/JungleGap.ai Setup.exe`

## Architecture

\`\`\`
JungleGap.ai/
├── backend/
│   ├── engine.py          # Python WebSocket server
│   └── requirements.txt   # Python dependencies
├── public/
│   ├── electron.js        # Electron main process
│   └── index.html         # HTML template
├── src/
│   ├── App.js             # React overlay component
│   ├── App.css            # Hextech styling
│   ├── index.js           # React entry point
│   └── index.css          # Global styles
├── package.json           # Node dependencies & scripts
└── README.md
\`\`\`

## How It Works

1. **Python Backend** runs a WebSocket server on `ws://localhost:8765`
2. **Mock Vision Engine** simulates enemy jungler detections every 10 seconds
3. **Riot LCU Client** connects to League's Live Client API for game state
4. **Electron Overlay** creates a transparent, click-through window
5. **React App** displays Hextech-styled alerts when detections arrive

## Customization

### Change Alert Frequency

In `backend/engine.py`, modify the interval:

\`\`\`python
self.vision_engine = MockVisionEngine(interval=10.0)  # seconds
\`\`\`

### Add Real Vision Detection

Replace `MockVisionEngine` with your trained YOLO model:

\`\`\`python
from ultralytics import YOLO

class RealVisionEngine:
    def __init__(self, model_path="models/jungler_detector.pt"):
        self.model = YOLO(model_path)
        # ... implement screen capture and inference
\`\`\`

## Troubleshooting

**Overlay not appearing?**
- Ensure Python backend is running first
- Check if port 8765 is available

**Connection dot is red?**
- Backend server might have crashed
- Check Python terminal for errors

**Not detecting League game?**
- League must be running in a match
- Riot's Live Client API only works in-game
