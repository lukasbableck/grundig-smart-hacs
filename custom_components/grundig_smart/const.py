"""Constants and key map for the Grundig Smart TV integration."""

from __future__ import annotations

import re
from typing import Final

DOMAIN: Final = "grundig_smart"
MANUFACTURER: Final = "Grundig"

CONF_SCAN_INTERVAL: Final = "scan_interval"
CONF_TV_INFO: Final = "tv_info"
CONF_WOL_ENABLED: Final = "wol_enabled"
CONF_WOL_BROADCAST_ADDRESS: Final = "wol_broadcast_address"
CONF_WOL_BROADCAST_PORT: Final = "wol_broadcast_port"
CONF_WOL_TIMEOUT: Final = "wol_timeout"
CONF_WOL_SEND_POWER: Final = "wol_send_power"

DEFAULT_PORT: Final = 8085
DEFAULT_SCAN_INTERVAL: Final = 30
MIN_SCAN_INTERVAL: Final = 5
MAX_SCAN_INTERVAL: Final = 300
DEFAULT_NAME: Final = "Grundig TV"

DEFAULT_WOL_ENABLED: Final = True
DEFAULT_WOL_BROADCAST_ADDRESS: Final = "255.255.255.255"
DEFAULT_WOL_BROADCAST_PORT: Final = 9
DEFAULT_WOL_TIMEOUT: Final = 30
MIN_WOL_TIMEOUT: Final = 5
MAX_WOL_TIMEOUT: Final = 120
DEFAULT_WOL_SEND_POWER: Final = False

# HTTP endpoints exposed by the TV on port 8085.
PATH_TV_INFO: Final = "/gettvinfo"
PATH_CHANNEL: Final = "/getchannel"
PATH_CHANNEL_LIST: Final = "/list"
PATH_SET_CHANNEL: Final = "/setchannel"
PATH_SEND_KEY: Final = "/sendrcpackage"
PATH_WS: Final = "/foo"

# The TV's WebSocket API accepts the HDMI port as a decimal string.
HDMI_INPUTS: Final[dict[str, int]] = {
    "HDMI 1": 1,
    "HDMI 2": 2,
    "HDMI 3": 3,
    "HDMI 4": 4,
}

# Values are signed 16-bit integers as expected by /sendrcpackage.
KEY_MAP: Final[dict[str, tuple[int, int]]] = {
    "POWER": (-2544, -4081),
    "VOLUME_UP": (-2475, -4020),
    "VOLUME_DOWN": (-2476, -4019),
    "MUTE": (-2539, -4018),
    "CHPLUS": (-2464, -4026),
    "CHMINUS": (-2465, -4025),
    "SELECT": (-2490, 13),
    "BACK": (-2542, -3979),
    "EXIT": (-2534, -3998),
    "MENU": (-2547, -4078),
    "INFO": (-2551, -4076),
    "TOOLS": (-2506, -4079),
    "EPG": (-2536, -4069),
    "INPUTSOURCE": (-2541, -3992),
    "FAV": (-2518, -3976),
    "TEXT": (-2543, -3990),
    "SUBTITLE": (-2507, -4064),
    "AUDIO": (-2549, -3984),
    "RED": (-2523, -4030),
    "GREEN": (-2522, -4029),
    "YELLOW": (-2521, -4028),
    "BLUE": (-2520, -4027),
    "UP": (-2493, -4094),
    "DOWN": (-2492, -4093),
    "LEFT": (-2495, -4096),
    "RIGHT": (-2494, -4095),
    "0": (-2533, 48),
    "1": (-2532, 49),
    "2": (-2531, 50),
    "3": (-2530, 51),
    "4": (-2529, 52),
    "5": (-2528, 53),
    "6": (-2527, 54),
    "7": (-2526, 55),
    "8": (-2525, 56),
    "9": (-2524, 57),
    "PLAY": (-2548, -4015),
    "PAUSE": (-2480, -4086),
    "STOP": (-2533, -4014),
    "RECORD": (-2560, -4010),
    "FASTREWIND": (-2558, -3977),
    "FASTFORWARD": (-2555, -4023),
    "PREVIOUS": (-2538, -4005),
    "NEXT": (-2546, -4004),
    "RECORDLIST": (-2556, -3988),
    "NETFLIX": (-2534, -3991),
    "INTERNET": (-2534, -4039),
    "INTERNET_KY": (-2534, -3987),
    "3D": (-2534, -4038),
}

KEY_ALIASES: Final[dict[str, str]] = {
    "OK": "SELECT",
    "ENTER": "SELECT",
    "RETURN": "BACK",
    "CHANNEL_UP": "CHPLUS",
    "CHANNEL_DOWN": "CHMINUS",
    "CHANNEL+": "CHPLUS",
    "CHANNEL_": "CHMINUS",
    "CH_PLUS": "CHPLUS",
    "CH_MINUS": "CHMINUS",
    "CH+": "CHPLUS",
    "CH-": "CHMINUS",
    "CH_": "CHMINUS",
    "VOL_UP": "VOLUME_UP",
    "VOL_DOWN": "VOLUME_DOWN",
    "VOL+": "VOLUME_UP",
    "VOL-": "VOLUME_DOWN",
    "VOL_": "VOLUME_DOWN",
    "VOLUME+": "VOLUME_UP",
    "VOLUME-": "VOLUME_DOWN",
    "VOLUME_": "VOLUME_DOWN",
    "GUIDE": "EPG",
    "SOURCE": "INPUTSOURCE",
    "INPUT": "INPUTSOURCE",
    "INPUT_SOURCE": "INPUTSOURCE",
    "TTX": "TEXT",
    "TELETEXT": "TEXT",
    "REW": "FASTREWIND",
    "REWIND": "FASTREWIND",
    "FAST_REWIND": "FASTREWIND",
    "FF": "FASTFORWARD",
    "FAST_FORWARD": "FASTFORWARD",
    "RECORD_LIST": "RECORDLIST",
    "NUM_0": "0",
    "NUM_1": "1",
    "NUM_2": "2",
    "NUM_3": "3",
    "NUM_4": "4",
    "NUM_5": "5",
    "NUM_6": "6",
    "NUM_7": "7",
    "NUM_8": "8",
    "NUM_9": "9",
}

_RAW_KEY_RE = re.compile(r"^(-?\d+)[:,](-?\d+)$")


def resolve_key(command: str) -> tuple[int, int]:
    """Turn a key name or ``keyid:keysymbol`` pair into integers."""
    raw = command.strip()
    match = _RAW_KEY_RE.match(raw)
    if match:
        return int(match.group(1)), int(match.group(2))

    name = raw.upper().replace(" ", "_").replace("-", "_")
    name = KEY_ALIASES.get(name, name)
    if name not in KEY_MAP:
        known = ", ".join(sorted(KEY_MAP))
        raise ValueError(
            f"Unknown key {command!r}. Use one of: {known}, "
            "or a raw pair such as -2475:-4020."
        )
    return KEY_MAP[name]
