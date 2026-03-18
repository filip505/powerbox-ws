import { useState, useEffect, useRef, useCallback } from 'react'
import './App.css'

const DEFAULT_WS_URL = 'ws://192.168.1.125:8765'

// Protocol from BLE log analysis (2026-03-18):
// A front = AB below neutral (0x48), A back = AB above neutral (0xc8)
// B front = AB barely below neutral (0xb6), B back = AB above neutral (0xbf)
// C front = CD above neutral (0xa1), C back = CD below neutral (0x21)
// D front = CD above neutral (0x5d), D back = CD above neutral (0x55)
const MOTORS = [
  { id: 'a', label: 'A', color: '#27ae60' },
  { id: 'b', label: 'B', color: '#e67e22' },
  { id: 'c', label: 'C', color: '#3498db' },
  { id: 'd', label: 'D', color: '#9b59b6' },
]

function App() {
  const [wsUrl, setWsUrl] = useState(DEFAULT_WS_URL)
  const [connected, setConnected] = useState(false)
  const [status, setStatus] = useState('Disconnected')
  // Track active motor and direction: null, 'a_front', 'a_back', 'b_front', 'b_back', etc.
  const [activeCommand, setActiveCommand] = useState(null)
  const [broadcasting, setBroadcasting] = useState(false)
  const wsRef = useRef(null)

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    setStatus('Connecting...')
    const ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      setConnected(true)
      setStatus('Connected')
    }

    ws.onclose = () => {
      setConnected(false)
      setStatus('Disconnected')
      setActiveCommand(null)
      setBroadcasting(false)
    }

    ws.onerror = () => setStatus('Connection error')

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.broadcasting !== undefined) {
          setBroadcasting(data.broadcasting)
        }
      } catch (e) {
        console.error('Parse error:', e)
      }
    }

    wsRef.current = ws
  }, [wsUrl])

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
  }, [])

  const sendWake = () => {
    if (wsRef.current?.readyState !== WebSocket.OPEN) return
    wsRef.current.send(JSON.stringify({ cmd: 'wake' }))
  }

  const sendStop = () => {
    if (wsRef.current?.readyState !== WebSocket.OPEN) return
    wsRef.current.send(JSON.stringify({ cmd: 'stop' }))
    setActiveCommand(null)
  }

  // 8 commands — 4 motors × 2 directions (front/back):
  // From fresh BLE log (2026-03-18 23:12) — user moved each motor in order:
  // A front, A back, B front, B back, C front, C back, D front, D back
  const sendMotorCommand = (motor, dir) => {
    if (wsRef.current?.readyState !== WebSocket.OPEN) return

    const cmdId = `${motor}_${dir}`
    setActiveCommand(cmdId)

    let ab = 0
    let cd = 0

    // Values from BLE log captures (exact Android app packets):
    // A front→AB=0x48(72),  A back→AB=0xc8(200)
    // B front→AB=0xb6(182), B back→AB=0xbf(191)
    // C front→CD=0xa1(161), C back→CD=0x21(33)
    // D front→CD=0x5d(93),  D back→CD=0x55(85)
    switch (cmdId) {
      case 'a_front': ab = -59; break // AB → 0x48 (72)
      case 'a_back':  ab =  18; break // AB → 0xc8 (200)
      case 'b_front': ab =  -1; break // AB → 0xb6 (182)
      case 'b_back':  ab =  11; break // AB → 0xbf (191)
      case 'c_front': cd =  46; break // CD → 0xa1 (161)
      case 'c_back':  cd = -49; break // CD → 0x21 (33)
      case 'd_front': cd =   8; break // CD → 0x5d (93)
      case 'd_back':  cd =   3; break // CD → 0x55 (85)
    }

    wsRef.current.send(JSON.stringify({ cmd: 'set', ab, cd }))
  }

  useEffect(() => {
    return () => disconnect()
  }, [disconnect])

  return (
    <div className="app">
      <h1>Power Box Control</h1>

      <div className="connection">
        <input
          type="text"
          value={wsUrl}
          onChange={(e) => setWsUrl(e.target.value)}
          placeholder="WebSocket URL"
          disabled={connected}
        />
        {connected ? (
          <button onClick={disconnect} className="disconnect">Disconnect</button>
        ) : (
          <button onClick={connect} className="connect">Connect</button>
        )}
        <span className={`status ${connected ? 'online' : 'offline'}`}>{status}</span>
      </div>

      {broadcasting && (
        <div className="broadcasting">Broadcasting to Power Box...</div>
      )}

      <div className="top-controls">
        <button
          className="cmd-btn wake-btn"
          style={{ '--btn-color': '#9b59b6' }}
          onClick={sendWake}
          disabled={!connected}
        >
          WAKE
        </button>

        <button
          className="cmd-btn stop-btn"
          style={{ '--btn-color': '#e74c3c' }}
          onClick={sendStop}
          disabled={!connected}
        >
          STOP ALL
        </button>
      </div>

      <div className="motor-grid">
        {MOTORS.map((motor) => (
          <div key={motor.id} className="motor-control">
            <div className="motor-name" style={{ color: motor.color }}>Motor {motor.label}</div>
            <div className="motor-buttons">
              <button
                className={`dir-btn ${activeCommand === `${motor.id}_front` ? 'active' : ''}`}
                style={{ '--btn-color': motor.color }}
                onClick={() => sendMotorCommand(motor.id, 'front')}
                disabled={!connected}
              >
                FRONT
              </button>
              <button
                className={`dir-btn ${activeCommand === `${motor.id}_back` ? 'active' : ''}`}
                style={{ '--btn-color': motor.color }}
                onClick={() => sendMotorCommand(motor.id, 'back')}
                disabled={!connected}
              >
                BACK
              </button>
            </div>
          </div>
        ))}
      </div>

      <div className="info">
        <p>4 motors × 2 directions (FRONT/BACK) = 8 commands + STOP</p>
      </div>
    </div>
  )
}

export default App
