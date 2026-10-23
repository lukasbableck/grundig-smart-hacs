# Grundig Smart TV for Home Assistant

A custom Home Assistant integration for Grundig/Arçelik **SMART inter@ctive 3.0 / 4.0**
TVs. It talks to the TV's local, unauthenticated HTTP API on port **8085** — no
root, no cloud account, and no MQTT bridge required.

Tested on a **Grundig Ultralogic FHD** with firmware
`G7GRMR.-.-.-.-.V11.007.00` (`tvInfo.name = "Ultralogic FHD"`).

## Features

- `media_player` entity:
  - turn on/off
  - volume up/down and mute
  - channel up/down (shown as the previous/next track buttons, because Home
    Assistant has no separate channel feature flag)
  - switch to a channel by number or name via `media_player.play_media`
  - current channel name as the media title, plus channel number/type/source attributes
- `remote` entity with the full key set from the Grundig Smart Remote app,
  including navigation, menus, digits, colour keys, transport keys, Netflix,
  the smart portal, and raw `keyid:keysymbol` pairs
- UI config flow (IP + port, validated against `/gettvinfo`)
- Options flow for the poll interval (5–300 seconds)
- Diagnostics support

## Requirements

- A Grundig TV from the **SMART inter@ctive** generation (roughly 2013–2017,
  including the Ultralogic FHD series). This is **not** an Android TV or Google TV 
  integration.
- The TV and Home Assistant on the same network.
- Port `8085` reachable from Home Assistant. Verify with:

  ```bash
  curl "http://<TV_IP>:8085/gettvinfo"
  ```

  A supported TV returns a JSON object containing `"tvInfo"`.

## Installation

### HACS (recommended)

1. Open HACS → **Integrations** → menu → **Custom repositories**.
2. Add the repository URL (for example
   `https://github.com/lukasbableck/grundig-smart-hacs`) with category **Integration**.
3. Install **Grundig Smart TV**, then restart Home Assistant.
4. Go to **Settings → Devices & services → Add integration** and search for
   **Grundig Smart TV**.

### Manual

Copy `custom_components/grundig_smart` into your Home Assistant
`config/custom_components/` directory and restart Home Assistant.

## Configuration

Enter:

| Field | Default | Notes |
| --- | --- | --- |
| Host | — | IP address of the TV, e.g. `192.168.1.50` |
| Port | `8085` | Change only if you found a different port |
| Name | TV name | Optional friendly name |

The TV must be switched on during setup so the integration can read
`/gettvinfo`. The MAC address is used as the unique ID.

After setup you can change the poll interval under
**Settings → Devices & services → Grundig Smart TV → Configure**.

## Entities

Assuming the TV reports its name as `Ultralogic FHD`:

- `media_player.ultralogic_fhd`
- `remote.ultralogic_fhd_remote`

The exact entity IDs depend on your naming and existing entities.

## Sending remote keys

Use the standard `remote.send_command` action:

```yaml
action: remote.send_command
target:
  entity_id: remote.ultralogic_fhd_remote
data:
  command: OK
```

Send a sequence:

```yaml
action: remote.send_command
target:
  entity_id: remote.ultralogic_fhd_remote
data:
  command:
    - DOWN
    - DOWN
    - OK
```

Repeat a key and adjust the delay:

```yaml
action: remote.send_command
target:
  entity_id: remote.ultralogic_fhd_remote
data:
  command: VOLUME_UP
  num_repeats: 5
  delay_secs: 0.3
```

Raw key IDs also work if you discover additional keys:

```yaml
action: remote.send_command
target:
  entity_id: remote.ultralogic_fhd_remote
data:
  command: "-2475:-4020"
```

### Common key names

| Key | Aliases |
| --- | --- |
| `POWER` | |
| `VOLUME_UP` / `VOLUME_DOWN` | `VOL_UP`, `VOL_DOWN`, `VOL+`, `VOL-` |
| `MUTE` | |
| `CHPLUS` / `CHMINUS` | `CHANNEL_UP`, `CHANNEL_DOWN`, `CH+`, `CH-` |
| `SELECT` | `OK`, `ENTER` |
| `BACK` | `RETURN` |
| `EXIT`, `MENU`, `INFO`, `TOOLS` | |
| `EPG` | `GUIDE` |
| `INPUTSOURCE` | `SOURCE`, `INPUT` |
| `UP`, `DOWN`, `LEFT`, `RIGHT` | |
| `0` … `9` | `NUM_0` … `NUM_9` |
| `RED`, `GREEN`, `YELLOW`, `BLUE` | |
| `TEXT` | `TTX`, `TELETEXT` |
| `SUBTITLE`, `AUDIO`, `FAV` | |
| `PLAY`, `PAUSE`, `STOP`, `RECORD` | |
| `FASTREWIND` / `FASTFORWARD` | `REW`, `REWIND`, `FF` |
| `PREVIOUS`, `NEXT`, `RECORDLIST` | |
| `NETFLIX`, `INTERNET`, `INTERNET_KY`, `3D` | |

The complete table lives in
[`custom_components/grundig_smart/const.py`](custom_components/grundig_smart/const.py).

## Switching channels

```yaml
action: media_player.play_media
target:
  entity_id: media_player.ultralogic_fhd
data:
  media_content_type: channel
  media_content_id: "3"
```

`media_content_id` can also be an exact channel name from the TV's channel list:

```yaml
action: media_player.play_media
target:
  entity_id: media_player.ultralogic_fhd
data:
  media_content_type: channel
  media_content_id: "Das Erste HD"
```

## How it works

The integration uses these endpoints:

- `GET /gettvinfo` — name, firmware, MAC, API version
- `GET /getchannel` — current channel (empty on the smart portal)
- `GET /list` — channel list used by `play_media`
- `GET /setchannel?no=<number>&service=<DTV|ATV|Radio|Data>` — channel switch
- `GET /sendrcpackage?keyid=<id>&keysymbol=<symbol>` — remote key press

The key table was extracted from the React Native bundle of **Grundig Smart
Remote 3.28**, the last app version that still contained the legacy HTTP
protocol. The six keys documented by `pygrundig`/CVE-2018-13989 match the
extracted table exactly; the remaining keys were derived from the same
`DIKI_*`/`DIKS_*` constants used by the app.

The TV also exposes a WebSocket test page at `/` (`ws://<TV_IP>:8085/foo`) with
`power`, `mute`, `v+`, `v-`, `bl+`, `bl-`, `memc`, and `exit` events, but it has
no state feedback and no channel/navigation support, so the integration does
not use it.

## Limitations

- **Power-on from standby** only works if the TV keeps its HTTP service alive
  in standby. On many of these sets port 8085 disappears when the TV is off.
  If `media_player.turn_on` reports that the TV is unreachable, use Wake-on-LAN
  or an IR blaster for power-on. Power-off works while the TV is reachable.
- There is **no absolute volume, mute, or power feedback**. Volume is step-based,
  mute is optimistic, and power state is inferred from whether `/getchannel`
  responds (with a 20-second override after sending `POWER`). Because of that,
  `turn_on`/`turn_off` do nothing when the inferred state already matches. If
  the state is ever wrong, send the raw toggle with
  `remote.send_command` and `command: POWER`.
- `/getchannel` returns an empty channel object while the TV is in the smart
  portal, so the media title is blank there.
- Some keys are model-specific. `RECORD` in particular was reconstructed from
  an incomplete constant and may not work on every set.
- The API is **unauthenticated and unencrypted**. Anyone who can reach port
  8085 can control the TV. Do not expose it to the internet; keep the TV on a
  trusted VLAN or restrict access with firewall rules.

## Troubleshooting

1. Check that the TV is on and reachable:

   ```bash
   curl "http://<TV_IP>:8085/gettvinfo"
   ```

2. If the port is closed, scan for the actual port:

   ```bash
   nmap -sT <TV_IP>
   ```

3. Enable debug logging if needed:

   ```yaml
   logger:
     logs:
       custom_components.grundig_smart: debug
   ```

## License

MIT — see [LICENSE](LICENSE).
