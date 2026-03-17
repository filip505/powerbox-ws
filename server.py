#!/usr/bin/env python3
"""
Power Box WebSocket Server

Server continuously broadcasts the last motor command until STOP is received.
"""

import asyncio
import json
import logging
from powerbox import PowerBoxController

try:
    import websockets
except ImportError:
    print("Error: websockets not installed. Run: pip install websockets")
    exit(1)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

controller = None
clients = set()

# Current motor values (continuously broadcast)
current_ab = 0
current_cd = 0
is_running = False
broadcast_task = None


async def broadcast_loop():
    """Continuously send current motor command to Power Box"""
    global is_running, current_ab, current_cd

    logger.info("Broadcast loop started")
    while is_running:
        if current_ab != 0 or current_cd != 0:
            controller.set_motors(motor_ab=current_ab, motor_cd=current_cd, repeat=1)
        await asyncio.sleep(0.15)  # Send every 150ms
    logger.info("Broadcast loop stopped")


def start_broadcast():
    """Start the broadcast loop"""
    global broadcast_task, is_running
    if broadcast_task is None or broadcast_task.done():
        is_running = True
        broadcast_task = asyncio.create_task(broadcast_loop())


def stop_broadcast():
    """Stop the broadcast loop"""
    global is_running
    is_running = False


async def handle_command(message):
    """Process a command and return response"""
    global current_ab, current_cd

    try:
        data = json.loads(message)
    except json.JSONDecodeError:
        return {"status": "error", "message": "Invalid JSON"}

    cmd = data.get("cmd", "").lower()

    if cmd == "set":
        ab = data.get("ab", 0)
        cd = data.get("cd", 0)

        current_ab = ab
        current_cd = cd

        # Start broadcasting if not already
        start_broadcast()

        logger.info(f"Motor command: AB={ab}, CD={cd} (broadcasting)")
        return {"status": "ok", "ab": ab, "cd": cd, "broadcasting": True}

    elif cmd == "stop":
        # Stop the broadcast loop
        stop_broadcast()
        current_ab = 0
        current_cd = 0

        # Send stop command once
        controller.stop()
        logger.info("STOP - broadcast stopped")
        return {"status": "ok", "ab": 0, "cd": 0, "broadcasting": False}

    elif cmd == "wake":
        controller.wake()
        logger.info("Wake-up signal sent")
        return {"status": "ok", "message": "Power Box woken up"}

    elif cmd == "state":
        return {"status": "ok", "ab": current_ab, "cd": current_cd, "broadcasting": is_running}

    else:
        return {"status": "error", "message": f"Unknown command: {cmd}"}


async def handler(websocket):
    """Handle WebSocket connection"""
    clients.add(websocket)
    remote = websocket.remote_address
    logger.info(f"Client connected: {remote}")

    # Wake up Power Box when client connects
    logger.info("Sending wake-up signal to Power Box...")
    controller.wake()
    logger.info("Power Box ready")

    try:
        async for message in websocket:
            response = await handle_command(message)
            await websocket.send(json.dumps(response))

    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client disconnected: {remote}")
    finally:
        clients.discard(websocket)
        # Stop motors if last client disconnects
        if len(clients) == 0:
            stop_broadcast()
            controller.stop()
            logger.info("Last client disconnected - motors stopped")


async def main(host="0.0.0.0", port=8765):
    global controller

    logger.info("Initializing Power Box controller...")
    controller = PowerBoxController()

    logger.info(f"Starting WebSocket server on ws://{host}:{port}")
    async with websockets.serve(handler, host, port):
        await asyncio.Future()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Power Box WebSocket Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8765, help="Port to listen on")
    args = parser.parse_args()

    try:
        asyncio.run(main(args.host, args.port))
    except KeyboardInterrupt:
        logger.info("Server stopped")
