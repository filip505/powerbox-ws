"""
Power Box TF01 Motor Control Module

Controls 2 motor channels via BLE advertising:
- Channel AB: Controls Motor A/B pair
- Channel CD: Controls Motor C/D pair

Each channel uses a byte value where:
- AB: 0xb8 (184) = stop, lower = reverse, higher = forward
- CD: 0x51 (81) = stop, lower = reverse, higher = forward
"""

import subprocess
import time

HEADER = "6db643cf7e8f4711"

# Initialization packet - wakes up the Power Box to accept commands
INIT_PACKET = HEADER + "415d2f38d17a2aef" + "6bf6"

# Neutral values (motor stop)
AB_NEUTRAL = 0xb8  # 184
CD_NEUTRAL = 0x51  # 81

# Complete checksum lookup table from captured Android traffic
PACKETS = {
    "415d2f38d17a2aef": "6bf6",
    "a55d2f0851fa2a0b": "2fac",
    "a55d2f0d51fa2a0b": "7b8a",
    "a55d2f1551fa2a0b": "1b64",
    "a55d2f1851fa2a0b": "6f18",
    "a55d2f18f1fa2a0b": "52ba",
    "a55d2f1951fa2a0b": "2b13",
    "a55d2f1b51fa2a0b": "a305",
    "a55d2f1c51fa2a0b": "7f35",
    "a55d2f1d51fa2a0b": "3b3e",
    "a55d2f2151fa2a0b": "da9d",
    "a55d2f2351fa2a0b": "528b",
    "a55d2f2651fa2a0b": "06ad",
    "a55d2f2851fa2a0b": "becc",
    "a55d2f28c1fa2a0b": "7122",
    "a55d2f2b51fa2a0b": "72d1",
    "a55d2f2e51fa2a0b": "26f7",
    "a55d2f4751fa2a0b": "f107",
    "a55d2f4851fa2a0b": "0d6d",
    "a55d2f48a1fa2a0b": "261a",
    "a55d2f5851fa2a0b": "4dd9",
    "a55d2f6551fa2a0b": "e871",
    "a55d2f6851fa2a0b": "9c0d",
    "a55d2f6881fa2a0b": "e4f5",
    "a55d2f7851fa2a0b": "dcb9",
    "a55d2f7a51fa2a0b": "54af",
    "a55d2f7c51fa2a0b": "cc94",
    "a55d2f8551fa2a0b": "0e5a",
    "a55d2f8851fa2a0b": "7a26",
    "a55d2f9651fa2a0b": "82f3",
    "a55d2f9851fa2a0b": "3a92",
    "a55d2f9871fa2a0b": "691d",
    "a55d2f9a51fa2a0b": "b284",
    "a55d2fa651fa2a0b": "5327",
    "a55d2fa851fa2a0b": "eb46",
    "a55d2faf51fa2a0b": "3776",
    "a55d2fb151fa2a0b": "cfa3",
    "a55d2fb251fa2a0b": "03be",
    "a55d2fb351fa2a0b": "47b5",
    "a55d2fb451fa2a0b": "9b85",
    "a55d2fb551fa2a0b": "df8e",
    "a55d2fb651fa2a0b": "1393",
    "a55d2fb751fa2a0b": "5798",
    "a55d2fb801fa2a0b": "bd27",
    "a55d2fb811fa2a0b": "1ce4",
    "a55d2fb821fa2a0b": "eea8",
    "a55d2fb831fa2a0b": "4f6b",
    "a55d2fb841fa2a0b": "0a31",
    "a55d2fb850fa2a0b": "10ee",
    "a55d2fb851fa2a0b": "abf2",  # NEUTRAL - both motors stopped
    "a55d2fb852fa2a0b": "66d7",
    "a55d2fb853fa2a0b": "ddcb",
    "a55d2fb854fa2a0b": "fc9c",
    "a55d2fb855fa2a0b": "4780",
    "a55d2fb856fa2a0b": "8aa5",
    "a55d2fb857fa2a0b": "31b9",
    "a55d2fb858fa2a0b": "c80b",
    "a55d2fb85afa2a0b": "be32",
    "a55d2fb85bfa2a0b": "052e",
    "a55d2fb85cfa2a0b": "2479",
    "a55d2fb85dfa2a0b": "9f65",
    "a55d2fb85efa2a0b": "5240",
    "a55d2fb85ffa2a0b": "e95c",
    "a55d2fb861fa2a0b": "59be",
    "a55d2fb871fa2a0b": "f87d",
    "a55d2fb880fa2a0b": "6816",
    "a55d2fb881fa2a0b": "d30a",
    "a55d2fb890fa2a0b": "c9d5",
    "a55d2fb891fa2a0b": "72c9",
    "a55d2fb8a1fa2a0b": "8085",
    "a55d2fb8b0fa2a0b": "9a5a",
    "a55d2fb8b1fa2a0b": "2146",
    "a55d2fb8b3fa2a0b": "577f",
    "a55d2fb8c1fa2a0b": "641c",
    "a55d2fb8e1fa2a0b": "3793",
    "a55d2fb8e8fa2a0b": "546a",
    "a55d2fb8f0fa2a0b": "2d4c",
    "a55d2fb8f1fa2a0b": "9650",
    "a55d2fb951fa2a0b": "eff9",
    "a55d2fba51fa2a0b": "23e4",
    "a55d2fbb51fa2a0b": "67ef",
    "a55d2fbc51fa2a0b": "bbdf",
    "a55d2fbd51fa2a0b": "ffd4",
    "a55d2fbe51fa2a0b": "33c9",
    "a55d2fbf51fa2a0b": "77c2",
    "a55d2fc821fa2a0b": "1dbd",
    "a55d2fc851fa2a0b": "58e7",
    "a55d2fcf51fa2a0b": "84d7",
    "a55d2fd151fa2a0b": "7c02",
    "a55d2fd251fa2a0b": "b01f",
    "a55d2fd831fa2a0b": "fcca",
    "a55d2fd851fa2a0b": "1853",
    "a55d2fde51fa2a0b": "8068",
    "a55d2fe451fa2a0b": "f9f0",
    "a55d2fe851fa2a0b": "c987",
    "a55d2fed51fa2a0b": "9da1",
    "a55d2ff551fa2a0b": "fd4f",
    "a55d2ff811fa2a0b": "3e25",
    "a55d2ff851fa2a0b": "8933",
    "a55d2ffc51fa2a0b": "991e",
}

# Known AB byte values (sorted)
KNOWN_AB = sorted(set(int(k[6:8], 16) for k in PACKETS.keys() if k.startswith("a55d")))
# Known CD byte values when AB=0xb8
KNOWN_CD = sorted(set(int(k[8:10], 16) for k in PACKETS.keys() if k.startswith("a55d2fb8")))


def run_cmd(cmd, silent=True):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
        return result.returncode == 0, result.stdout + result.stderr
    except Exception as e:
        return False, str(e)


def find_closest(value, known_list):
    """Find closest value in known list"""
    return min(known_list, key=lambda x: abs(x - value))


def percent_to_ab(percent):
    """Convert -100 to 100 percent to AB byte value"""
    # AB: 0x08 (8) = -100%, 0xb8 (184) = 0%, 0xfc (252) = +100%
    # Range below neutral: 184 - 8 = 176
    # Range above neutral: 252 - 184 = 68
    percent = max(-100, min(100, percent))

    if percent <= 0:
        # Map -100..0 to 8..184
        raw = int(AB_NEUTRAL + (percent * (AB_NEUTRAL - 0x08) / 100))
    else:
        # Map 0..100 to 184..252
        raw = int(AB_NEUTRAL + (percent * (0xfc - AB_NEUTRAL) / 100))

    return find_closest(raw, KNOWN_AB)


def percent_to_cd(percent):
    """Convert -100 to 100 percent to CD byte value"""
    # CD: 0x01 (1) = -100%, 0x51 (81) = 0%, 0xf1 (241) = +100%
    percent = max(-100, min(100, percent))

    if percent <= 0:
        # Map -100..0 to 1..81
        raw = int(CD_NEUTRAL + (percent * (CD_NEUTRAL - 0x01) / 100))
    else:
        # Map 0..100 to 81..241
        raw = int(CD_NEUTRAL + (percent * (0xf1 - CD_NEUTRAL) / 100))

    return find_closest(raw, KNOWN_CD)


def build_packet(ab_byte, cd_byte):
    """Build a packet with known checksum, or closest match"""
    control = f"a55d2f{ab_byte:02x}{cd_byte:02x}fa2a0b"

    if control in PACKETS:
        checksum = PACKETS[control]
    else:
        # Try with neutral CD
        control_ab = f"a55d2f{ab_byte:02x}{CD_NEUTRAL:02x}fa2a0b"
        if control_ab in PACKETS:
            control = control_ab
            checksum = PACKETS[control]
        else:
            # Try with neutral AB
            control_cd = f"a55d2f{AB_NEUTRAL:02x}{cd_byte:02x}fa2a0b"
            if control_cd in PACKETS:
                control = control_cd
                checksum = PACKETS[control]
            else:
                # Fallback to full neutral
                control = f"a55d2f{AB_NEUTRAL:02x}{CD_NEUTRAL:02x}fa2a0b"
                checksum = PACKETS[control]

    return HEADER + control + checksum


def send_advertising(mfg_data, duration=0.03):
    """Send BLE advertising packet"""
    flags = "020102"
    mfg_len = len(mfg_data) // 2 + 2
    mfg_struct = f"{mfg_len:02x}ff00ff{mfg_data}"
    adv_data = flags + mfg_struct

    while len(adv_data) < 62:
        adv_data += "00"

    adv_len = min(31, len(adv_data) // 2)
    adv_bytes = " ".join([adv_data[i:i+2] for i in range(0, adv_len*2, 2)])

    run_cmd("sudo hciconfig hci0 noleadv")
    # Use 100ms advertising interval (A0 00 = 160 * 0.625ms) for BLE spec compliance
    run_cmd("sudo hcitool -i hci0 cmd 0x08 0x0006 A0 00 A0 00 03 00 00 00 00 00 00 00 00 07 00")
    run_cmd(f"sudo hcitool -i hci0 cmd 0x08 0x0008 {adv_len:02x} {adv_bytes}")
    run_cmd("sudo hciconfig hci0 leadv 3")
    time.sleep(duration)
    run_cmd("sudo hciconfig hci0 noleadv")


class PowerBoxController:
    def __init__(self):
        self.motor_ab = 0
        self.motor_cd = 0
        self._init_bluetooth()

    def _init_bluetooth(self):
        """Initialize Bluetooth"""
        run_cmd("sudo hciconfig hci0 up")

    def wake(self):
        """Send wake-up packet to Power Box"""
        for _ in range(5):
            send_advertising(INIT_PACKET, duration=0.5)

    def set_motors(self, motor_ab=None, motor_cd=None, repeat=10):
        """
        Set motor values (-100 to 100)

        motor_ab: Motor A/B channel (-100=full reverse, 0=stop, 100=full forward)
        motor_cd: Motor C/D channel (-100=full reverse, 0=stop, 100=full forward)
        """
        if motor_ab is not None:
            self.motor_ab = max(-100, min(100, motor_ab))
        if motor_cd is not None:
            self.motor_cd = max(-100, min(100, motor_cd))

        ab_byte = percent_to_ab(self.motor_ab)
        cd_byte = percent_to_cd(self.motor_cd)
        mfg_data = build_packet(ab_byte, cd_byte)

        for _ in range(repeat):
            send_advertising(mfg_data, duration=0.05)

    def stop(self):
        """Stop all motors"""
        self.motor_ab = 0
        self.motor_cd = 0
        mfg_data = HEADER + f"a55d2f{AB_NEUTRAL:02x}{CD_NEUTRAL:02x}fa2a0b" + "abf2"
        for _ in range(3):
            send_advertising(mfg_data, duration=0.05)

    def get_state(self):
        """Get current motor state"""
        return {"motor_ab": self.motor_ab, "motor_cd": self.motor_cd}
