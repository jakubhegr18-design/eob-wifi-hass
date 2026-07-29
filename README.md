# EOB WiFi Home Assistant Integration

> ⚠️ **BETA** — Tato integrace je ve aktivním vývoji. Některé funkce mohou být nestabilní nebo neúplné. Použití na vlastní nebezpečí.

[![GitHub Release](https://img.shields.io/github/v/release/jakubhegr18-design/eob-wifi-hass?style=for-the-badge)](https://github.com/jakubhegr18-design/eob-wifi-hass/releases)
[![HACS](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/jakubhegr18-design/eob-wifi-hass)
[![GitHub](https://img.shields.io/github/license/jakubhegr18-design/eob-wifi-hass?style=for-the-badge)](LICENSE)

## Supported devices

- TS11 WiFi
- Další kompatibilní zařízení

## Description

Integrace pro zařízení používající aplikaci EOB WiFi.

## Features

- Ovládání teploty
- MQTT komunikace
- Lokální / WiFi řízení

## Installation

### HACS (doporučeno)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=jakubhegr18-design&repository=eob-wifi-hass&category=Integration)

1. Otevřete HACS v Home Assistant
2. Přejděte na **Integrations → Custom repositories**
3. Přidejte `https://github.com/jakubhegr18-design/eob-wifi-hass` jako kategorii **Integration**
4. Klikněte na **Download** u EOB WiFi integrace
5. Restartujte Home Assistant

### Manual

1. Zkopírujte adresář `custom_components/eob_wifi/` do `config/custom_components/` ve vaší HA instalaci
2. Restartujte Home Assistant

## Configuration

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=eob_wifi)

1. Přejděte do Settings → Devices & Services → Add Integration
2. Vyhledejte "EOB WiFi"
3. Zadejte své **uživatelské jméno/e-mail** a **heslo** (stejné jako v mobilní aplikaci EOB WiFi)
4. Potvrďte

Entity se vytvoří automaticky.

## Disclaimer

Nejedná se o oficiální integraci od společnosti Elektrobock. Použití na vlastní nebezpečí.
