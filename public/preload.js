/**
 * JungleGap.ai - Preload Script
 * Secure bridge between Electron main process and React renderer.
 * Exposes safe APIs to the renderer process via contextBridge.
 */

const { contextBridge, ipcRenderer } = require("electron")

// Expose safe APIs to the renderer
contextBridge.exposeInMainWorld("electronAPI", {
  // Platform info
  platform: process.platform,

  // IPC communication (for future features)
  send: (channel, data) => {
    const validChannels = ["toggle-clickthrough", "minimize", "close"]
    if (validChannels.includes(channel)) {
      ipcRenderer.send(channel, data)
    }
  },

  receive: (channel, callback) => {
    const validChannels = ["backend-status", "detection-alert"]
    if (validChannels.includes(channel)) {
      ipcRenderer.on(channel, (event, ...args) => callback(...args))
    }
  },
})

console.log("[Preload] Electron APIs exposed to renderer")
