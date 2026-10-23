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
- `select` entity for the current channel, populated from the TV's full
  DTV/Radio channel list
- One `button` entity per remote key (49 buttons) for clickable dashboards
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
- `select.ultralogic_fhd_channel`
- 49 button entities such as `button.ultralogic_fhd_power`,
  `button.ultralogic_fhd_volume_up`, `button.ultralogic_fhd_ok`, and
  `button.ultralogic_fhd_netflix`

The exact entity IDs depend on your naming and existing entities. You can
disable buttons you do not need under **Settings → Devices & services →
Entities**.

## Remote buttons

Home Assistant's `remote` entity is service-style. It looks empty on the
device page because it has no activities to display; it is controlled with
`remote.send_command` instead. For clickable controls, the integration exposes
one `button` entity per key:

- `button.ultralogic_fhd_power`
- `button.ultralogic_fhd_volume_up` / `button.ultralogic_fhd_volume_down`
- `button.ultralogic_fhd_channel_up` / `button.ultralogic_fhd_channel_down`
- `button.ultralogic_fhd_up` / `down` / `left` / `right`
- `button.ultralogic_fhd_ok`, `back`, `menu`, `info`, `guide`, `source`
- `button.ultralogic_fhd_red`, `green`, `yellow`, `blue`
- `button.ultralogic_fhd_0` … `button.ultralogic_fhd_9`
- `button.ultralogic_fhd_play`, `pause`, `stop`, `record`, `rewind`,
  `fast_forward`, `previous`, `next`
- `button.ultralogic_fhd_netflix`, `internet`, `3d`

A simple dashboard grid:

```yaml
type: grid
columns: 4
square: true
cards:
  - type: button
    entity: button.ultralogic_fhd_power
  - type: button
    entity: button.ultralogic_fhd_up
  - type: button
    entity: button.ultralogic_fhd_ok
  - type: button
    entity: button.ultralogic_fhd_down
  - type: button
    entity: button.ultralogic_fhd_back
  - type: button
    entity: button.ultralogic_fhd_menu
  - type: button
    entity: button.ultralogic_fhd_volume_up
  - type: button
    entity: button.ultralogic_fhd_volume_down
```

The TV exposes two Internet key variants. Try `button.ultralogic_fhd_internet`
first, then `button.ultralogic_fhd_internet_alternate` if it does nothing.

The `remote` entity is still the better choice for sequences and raw key IDs.

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

The channel `select` entity uses labels in the form
`<number> · <name> (<service>)`, for example
`3 · RTL Television (DTV)`:

```yaml
action: select.select_option
target:
  entity_id: select.ultralogic_fhd_channel
data:
  option: "3 · RTL Television (DTV)"
```

The TV reports 662 channels (DTV and Radio), so the dropdown is long. The
`media_player.play_media` action is usually faster for automations.

## Input sources (HDMI)

The legacy HTTP API has **no input/source endpoint**. `/getsource`,
`/getinput`, `/getinputs`, `/getinputlist` and similar paths all return 404,
and `/setchannel` silently ignores unknown `service` values such as `HDMI1`.
The only source control the TV exposes is the `INPUTSOURCE` remote key, which
opens the TV's own source menu.

You can open that menu with the remote entity and navigate manually:

```yaml
action: remote.send_command
target:
  entity_id: remote.ultralogic_fhd_remote
data:
  command:
    - INPUTSOURCE
    - DOWN
    - OK
```

The menu order and the number of `DOWN` presses depend on your model and on
which inputs are active, so this is not exposed as a `select` entity. For
reliable HDMI switching, use discrete IR codes with an IR blaster or HDMI-CEC.

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
  portal, so the media title and channel select state are blank there.
- There is **no input-source selection over HTTP**. HDMI/AV switching requires
  the TV's source menu; see [Input sources (HDMI)](#input-sources-hdmi).
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
