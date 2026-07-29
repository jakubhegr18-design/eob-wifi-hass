# EOB WiFi Home Assistant Integration

> ⚠️ **BETA** — This integration is under active development. Some features may be buggy or incomplete. Use at your own risk.

[![GitHub Release](https://img.shields.io/github/v/release/jakubhegr18-design/eob-wifi-hass?style=for-the-badge)](https://github.com/jakubhegr18-design/eob-wifi-hass/releases)
[![HACS](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/jakubhegr18-design/eob-wifi-hass)
[![GitHub](https://img.shields.io/github/license/jakubhegr18-design/eob-wifi-hass?style=for-the-badge)](LICENSE)

## Supported devices

- TS11 WiFi
- Other compatible devices

## Description

Integration for devices using the EOB WiFi app.

## Features

- Temperature control
- MQTT communication
- Local / WiFi control

## Installation

### HACS (recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=jakubhegr18-design&repository=eob-wifi-hass&category=Integration)

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

Entities will be created automatically.

## Disclaimer

This is a community integration, not officially supported by Elektrobock. Use at your own risk.
