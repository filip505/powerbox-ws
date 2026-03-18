# Power Box TF01 Controller

Control Power Box TF01 "A Series" building block motor controller via Bluetooth from a Raspberry Pi.

## Overview

This project reverse-engineers the BLE protocol used by the Power Box TF01 Android app and provides a WebSocket server for remote motor control.

## Hardware

- **Power Box TF01 "A Series"** - Building block motor controller with 2 motor channels
- **Raspberry Pi** (with built-in Bluetooth) - Sends BLE advertising packets
- **Motors**: 2 physical motors, each with 2 speeds (A/C and B/D) and forward/reverse control

## Protocol

The Power Box uses BLE advertising (not connections). The Pi broadcasts packets that the Power Box listens to.

### Packet Structure

```
Header (8 bytes)     Control (8 bytes)           Checksum (2 bytes)
6db643cf7e8f4711     a55d2f [AB] [CD] fa2a0b     xxxx
```

### Motor Control Bytes

| Byte | Neutral | Range | Effect |
|------|---------|-------|--------|
| AB   | 0xb8    | 0xb8 → 0xf8 | Motor 1 forward |
| AB   | 0xb8    | 0xb8 → 0x08 | Motor 1 reverse |
| CD   | 0x51    | 0x51 → 0xf1 | Motor 2 forward |
| CD   | 0x51    | 0x51 → 0x01 | Motor 2 reverse |

The Power Box has 2 physical motors, each with 2 speeds and 2 directions = 8 commands:
- **Motor 1 (AB byte)**: A = slow speed, C = fast speed
- **Motor 2 (CD byte)**: B = slow speed, D = fast speed

Speed is controlled by distance from neutral value.

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
{"cmd": "set", "ab": 100, "cd": 0}
```
- `ab`: Motor 1 speed/direction (-100 to 100). Positive=forward, negative=reverse. Higher abs value=faster.
- `cd`: Motor 2 speed/direction (-100 to 100). Positive=forward, negative=reverse. Higher abs value=faster.

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
{"status": "ok", "ab": 100, "cd": 0, "broadcasting": true}
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

- The Power Box goes to sleep after inactivity - wake-up packet is sent automatically when a client connects
- Checksum algorithm is unknown - using lookup table of captured valid packets
- Motors stop automatically if all WebSocket clients disconnect
