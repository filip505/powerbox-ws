# Power Box TF01 Controller

Control Power Box TF01 "A Series" building block motor controller via Bluetooth from a Raspberry Pi.

## Overview

This project reverse-engineers the BLE protocol used by the Power Box TF01 Android app and provides a WebSocket server for remote motor control.

## Hardware

- **Power Box TF01 "A Series"** - Building block motor controller with 4 motors (2 channels)
- **Raspberry Pi** (with built-in Bluetooth) - Sends BLE advertising packets

## Protocol

The Power Box uses BLE advertising (not connections). The Pi broadcasts packets that the Power Box listens to.

### Packet Structure

```
Header (8 bytes)     Control (8 bytes)           Checksum (2 bytes)
6db643cf7e8f4711     a55d2f [AB] [CD] fa2a0b     xxxx
```

### Motor Control Bytes

| Byte | Neutral | Range         | Motors        |
|------|---------|---------------|---------------|
| AB   | 0xb8    | 0x08 → 0xf8  | Motors A & B  |
| CD   | 0x51    | 0x01 → 0xf1  | Motors C & D  |

- Speed is proportional to distance from neutral — larger deviation = faster
- Motors A and B share the AB byte; C and D share the CD byte

### Captured Motor Commands (from Android app BLE log, 2026-03-18)

| Motor | Direction | AB byte | CD byte |
|-------|-----------|---------|---------|
| A     | front     | 0x48    | 0x51    |
| A     | back      | 0xc8    | 0x51    |
| B     | front     | 0xb6    | 0x51    |
| B     | back      | 0xbf    | 0x51    |
| C     | front     | 0xb8    | 0xa1    |
| C     | back      | 0xb8    | 0x21    |
| D     | front     | 0xb8    | 0x5d    |
| D     | back      | 0xb8    | 0x55    |

### Wake-up Packet

Before sending motor commands, a special wake-up packet must be sent:
```
6db643cf7e8f4711 415d2f38d17a2aef 6bf6
```

### Continuous Broadcasting

The Power Box requires continuous packet broadcasting to keep motors running. The server loops the last command until STOP is received.

## Installation

### On Raspberry Pi

```bash
cd ~/powerbox-ws
python3 -m venv venv
source venv/bin/activate
pip install websockets
```

### Start Server

```bash
sudo ./venv/bin/python server.py --port 8765
```

## Web Interface

4 motor sliders (A, B, C, D), each from -100 to +100. Center = stopped. The value controls speed and direction — positive and negative correspond to opposite directions.

### Start Development Server

```bash
cd web
npm install
npm run dev
```

Open http://localhost:5173

## WebSocket API

Connect to `ws://<pi-ip>:8765`

### Commands

**Wake up Power Box:**
```json
{"cmd": "wake"}
```

**Set motors (starts continuous broadcasting):**
```json
{"cmd": "set", "ab": 75, "cd": -50}
```
- `ab`: AB channel (-100 to 100). Controls motors A & B. Higher absolute value = faster.
- `cd`: CD channel (-100 to 100). Controls motors C & D. Higher absolute value = faster.

**Stop all motors:**
```json
{"cmd": "stop"}
```

**Get current state:**
```json
{"cmd": "state"}
```

### Responses

```json
{"status": "ok", "ab": 75, "cd": -50, "broadcasting": true}
```

## Files

```
powerbox-ws/
├── powerbox.py      # BLE advertising and motor control
├── server.py        # WebSocket server with broadcast loop
├── web/             # React web interface
│   ├── src/
│   │   ├── App.jsx
│   │   └── App.css
│   └── package.json
└── README.md
```

## Notes

- The Power Box goes to sleep after inactivity — send WAKE before first command
- Checksum algorithm is unknown — using lookup table of captured valid packets
- Motors stop automatically if all WebSocket clients disconnect
