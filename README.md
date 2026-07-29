# EOB WiFi

[![GitHub Release](https://img.shields.io/github/v/release/jakubhegr18-design/eob-wifi-hass?style=for-the-badge)](https://github.com/jakubhegr18-design/eob-wifi-hass/releases)
[![HACS](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/jakubhegr18-design/eob-wifi-hass)
[![GitHub](https://img.shields.io/github/license/jakubhegr18-design/eob-wifi-hass?style=for-the-badge)](LICENSE)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=jakubhegr18-design&repository=eob-wifi-hass&category=Integration)

Home Assistant custom integration for controlling **Elektrobock EOB WiFi** devices (thermostats, relays, sensors).

## Features

- Climate control for **EOB WiFi thermostats** (Ts11WiFi, U2)
  - Set target temperature (3–39°C, 0.5°C steps)
  - Switch between Auto / Manual Heat / Off modes
  - Read current temperature
- Switch control for **EOB WiFi relays** (Pt14, Pt14WifOnly)
  - Turn on/off
  - Read output state
- Firmware version sensor for each device
- Polls cloud API every 60 seconds

## Installation

### HACS (recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=jakubhegr18-design&repository=eob-wifi-hass&category=Integration)

Click the badge above, or manually:

1. Open HACS in Home Assistant
2. Go to **Integrations → Custom repositories**
3. Add `https://github.com/jakubhegr18-design/eob-wifi-hass` as category **Integration**
4. Click **Download** on the EOB WiFi integration
5. Restart Home Assistant

### Manual

1. Copy the `custom_components/eob_wifi/` directory to your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant

## Configuration

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=eob_wifi)

1. Go to Settings → Devices & Services → Add Integration
2. Search for "EOB WiFi"
3. Enter your **username/email** and **password** (same as in the EOB WiFi mobile app)
4. Submit

Your devices will appear as climate and/or switch entities automatically.

## API

This integration uses the Elektrobock cloud API at `https://data.elektrobock.cz`. Credentials are stored securely in Home Assistant's credential store.

## Supported Devices

| Device Type | ID | Category |
|---|---|---|
| Ts11WiFi | 8 | Thermostat |
| U2 | 7 | Thermostat |
| Pt14 | 14 | Relay/Switch |
| Pt14WifOnly | 20 | Relay/Switch |

## Disclaimer

This is a community integration, not officially supported by Elektrobock. Use at your own risk.
