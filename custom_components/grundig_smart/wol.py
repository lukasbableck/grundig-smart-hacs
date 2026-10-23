"""Wake-on-LAN helper for the Grundig Smart TV integration."""

from __future__ import annotations

import socket

from homeassistant.core import HomeAssistant


def build_magic_packet(mac: str) -> bytes:
    """Build a Wake-on-LAN magic packet for a MAC address."""
    cleaned = mac.replace(":", "").replace("-", "").replace(".", "").strip()
    if len(cleaned) != 12:
        raise ValueError(f"Invalid MAC address: {mac!r}")
    return b"\xff" * 6 + bytes.fromhex(cleaned) * 16


def send_magic_packet(mac: str, broadcast_address: str, port: int) -> None:
    """Send a magic packet via UDP broadcast."""
    packet = build_magic_packet(mac)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(packet, (broadcast_address, port))


async def async_send_magic_packet(
    hass: HomeAssistant,
    mac: str,
    broadcast_address: str,
    port: int,
) -> None:
    """Send a magic packet without blocking the event loop."""
    await hass.async_add_executor_job(
        send_magic_packet,
        mac,
        broadcast_address,
        port,
    )
