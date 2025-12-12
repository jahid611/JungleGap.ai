"use client"

/**
 * JungleGap.ai - React Overlay Component
 * Hextech-styled alert display with WebSocket connection.
 */

import { useState, useEffect, useCallback } from "react"
import "./App.css"

const WS_URL = "ws://localhost:8765"
const ALERT_DURATION = 4000

function App() {
  const [alert, setAlert] = useState(null)
  const [isConnected, setIsConnected] = useState(false)
  const [isFlashing, setIsFlashing] = useState(false)

  const connectWebSocket = useCallback(() => {
    console.log("[WS] Connecting...")
    const ws = new WebSocket(WS_URL)

    ws.onopen = () => {
      console.log("[WS] Connected")
      setIsConnected(true)
    }

    ws.onclose = () => {
      console.log("[WS] Disconnected")
      setIsConnected(false)
      setTimeout(connectWebSocket, 2000)
    }

    ws.onerror = (err) => {
      console.error("[WS] Error:", err)
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)

        if (data.type === "alert") {
          setAlert({
            champion: data.champion,
            location: data.location,
            confidence: data.confidence,
          })

          setIsFlashing(true)
          setTimeout(() => setIsFlashing(false), 600)
          setTimeout(() => setAlert(null), ALERT_DURATION)
        }
      } catch (e) {
        console.error("[WS] Parse error:", e)
      }
    }

    return ws
  }, [])

  useEffect(() => {
    const ws = connectWebSocket()
    return () => ws.close()
  }, [connectWebSocket])

  return (
    <div className={`overlay ${isFlashing ? "flashing" : ""}`}>
      {/* Screen border flash */}
      <div className="screen-border" />

      {/* Alert panel */}
      {alert && (
        <div className="alert-container">
          <div className="alert-panel">
            <div className="alert-glow" />
            <div className="alert-border" />

            <div className="alert-content">
              <div className="alert-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 9v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>

              <div className="alert-text">
                <div className="alert-title">ENEMY JUNGLER DETECTED</div>
                <div className="alert-champion">{alert.champion}</div>
                <div className="alert-location">{alert.location}</div>
                <div className="alert-confidence">{Math.round(alert.confidence * 100)}% confidence</div>
              </div>
            </div>

            {/* Hextech corner accents */}
            <div className="corner corner-tl" />
            <div className="corner corner-tr" />
            <div className="corner corner-bl" />
            <div className="corner corner-br" />
          </div>
        </div>
      )}

      {/* Connection indicator */}
      <div className={`connection-dot ${isConnected ? "connected" : ""}`} />
    </div>
  )
}

export default App
