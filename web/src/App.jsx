import { useState, useEffect, useRef, useCallback } from 'react'
import './App.css'

const DEFAULT_WS_URL = 'ws://192.168.1.125:8765'

const COMMANDS = [
  { id: 'wake', label: 'WAKE', desc: 'Wake up Power Box', color: '#9b59b6' },
  { id: 'stop', label: 'STOP', desc: 'Stop all motors', color: '#e74c3c' },
  { id: 'a_fwd', label: 'A FWD', desc: 'AB=f8 (forward)', color: '#27ae60' },
  { id: 'a_rev', label: 'A REV', desc: 'AB=48 (reverse)', color: '#e67e22' },
  { id: 'c_fwd', label: 'C FWD', desc: 'CD=f1 (forward)', color: '#3498db' },
  { id: 'c_rev', label: 'C REV', desc: 'CD=11 (reverse)', color: '#1abc9c' },
]

function App() {
  const [wsUrl, setWsUrl] = useState(DEFAULT_WS_URL)
  const [connected, setConnected] = useState(false)
  const [status, setStatus] = useState('Disconnected')
  const [activeCmd, setActiveCmd] = useState(null)
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
      setActiveCmd(null)
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

  const sendCommand = (cmdId) => {
    if (wsRef.current?.readyState !== WebSocket.OPEN) return

    let cmd
    switch (cmdId) {
      case 'wake':
        cmd = { cmd: 'wake' }
        break
      case 'stop':
        cmd = { cmd: 'stop' }
        setActiveCmd(null)
        break
      case 'a_fwd':
        cmd = { cmd: 'set', ab: 100, cd: 0 }
        setActiveCmd(cmdId)
        break
      case 'a_rev':
        cmd = { cmd: 'set', ab: -100, cd: 0 }
        setActiveCmd(cmdId)
        break
      case 'c_fwd':
        cmd = { cmd: 'set', ab: 0, cd: 100 }
        setActiveCmd(cmdId)
        break
      case 'c_rev':
        cmd = { cmd: 'set', ab: 0, cd: -100 }
        setActiveCmd(cmdId)
        break
      default:
        return
    }

    wsRef.current.send(JSON.stringify(cmd))
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

      <div className="commands">
        {COMMANDS.map((cmd) => (
          <button
            key={cmd.id}
            className={`cmd-btn ${activeCmd === cmd.id ? 'active' : ''} ${cmd.id === 'stop' ? 'stop-btn' : ''}`}
            style={{ '--btn-color': cmd.color }}
            onClick={() => sendCommand(cmd.id)}
            disabled={!connected}
          >
            <span className="cmd-label">{cmd.label}</span>
            <span className="cmd-desc">{cmd.desc}</span>
          </button>
        ))}
      </div>

      <div className="info">
        <p>Click a motor button to start. Click STOP to stop.</p>
        <p>Server keeps broadcasting until STOP is pressed.</p>
      </div>
    </div>
  )
}

export default App
