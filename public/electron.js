/**
 * JungleGap.ai - Electron Main Process
 * Transparent, click-through overlay with Python backend auto-launch.
 */

const { app, BrowserWindow, screen } = require("electron")
const path = require("path")
const { spawn } = require("child_process")

let mainWindow = null
let pythonProcess = null

/**
 * Spawn the Python backend executable.
 */
function startPythonBackend() {
  const isDev = !app.isPackaged

  let pythonPath
  if (isDev) {
    // Development: run Python script directly
    pythonPath = "python"
    const scriptPath = path.join(__dirname, "..", "backend", "engine.py")
    console.log("[Backend] Starting Python script:", scriptPath)
    pythonProcess = spawn(pythonPath, [scriptPath], {
      stdio: ["ignore", "pipe", "pipe"],
    })
  } else {
    // Production: run compiled .exe from extraResources
    pythonPath = path.join(process.resourcesPath, "backend", "engine.exe")
    console.log("[Backend] Starting compiled backend:", pythonPath)
    pythonProcess = spawn(pythonPath, [], {
      stdio: ["ignore", "pipe", "pipe"],
    })
  }

  pythonProcess.stdout.on("data", (data) => {
    console.log(`[Python] ${data.toString().trim()}`)
  })

  pythonProcess.stderr.on("data", (data) => {
    console.error(`[Python ERROR] ${data.toString().trim()}`)
  })

  pythonProcess.on("close", (code) => {
    console.log(`[Python] Process exited with code ${code}`)
  })

  pythonProcess.on("error", (err) => {
    console.error("[Python] Failed to start:", err.message)
  })
}

/**
 * Create the transparent overlay window.
 */
function createOverlayWindow() {
  const { width, height } = screen.getPrimaryDisplay().workAreaSize

  mainWindow = new BrowserWindow({
    width: width,
    height: height,
    x: 0,
    y: 0,
    transparent: true,
    frame: false,
    alwaysOnTop: true,
    skipTaskbar: true,
    resizable: false,
    movable: false,
    focusable: false,
    hasShadow: false,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
    },
  })

  // Click-through: mouse events pass through to game
  mainWindow.setIgnoreMouseEvents(true, { forward: true })

  // Stay on top of fullscreen games
  mainWindow.setAlwaysOnTop(true, "screen-saver")
  mainWindow.setVisibleOnAllWorkspaces(true)

  // Load React app
  const isDev = !app.isPackaged
  if (isDev) {
    mainWindow.loadURL("http://localhost:3000")
    // Uncomment to debug: mainWindow.webContents.openDevTools({ mode: 'detach' });
  } else {
    mainWindow.loadFile(path.join(__dirname, "..", "build", "index.html"))
  }

  mainWindow.on("closed", () => {
    mainWindow = null
  })

  console.log("[Electron] Overlay window created")
}

// App lifecycle
app.whenReady().then(() => {
  startPythonBackend()

  // Give backend time to start before creating window
  setTimeout(createOverlayWindow, 1500)
})

app.on("window-all-closed", () => {
  if (pythonProcess) {
    pythonProcess.kill()
  }
  if (process.platform !== "darwin") {
    app.quit()
  }
})

app.on("before-quit", () => {
  if (pythonProcess) {
    pythonProcess.kill()
  }
})

app.on("activate", () => {
  if (mainWindow === null) {
    createOverlayWindow()
  }
})

// Single instance lock
const gotTheLock = app.requestSingleInstanceLock()
if (!gotTheLock) {
  app.quit()
}
