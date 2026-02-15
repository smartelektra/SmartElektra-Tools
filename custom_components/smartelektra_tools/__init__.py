from __future__ import annotations

import asyncio
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import (
    DOMAIN,
    CONF_HOST,
    CONF_PORT,
    CONF_TIMEOUT,
    DEFAULT_HR_NEW_SLAVE,
)
from .modbus_client import ModbusTcpClientCompat


PLATFORMS: list[str] = []


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]
    timeout = entry.data[CONF_TIMEOUT]

    client = ModbusTcpClientCompat(host=host, port=port, timeout=timeout)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = client

    async def _run_blocking(func, *args):
        return await hass.async_add_executor_job(func, *args)

    async def handle_set_slave_id(call: ServiceCall) -> None:
        new_slave = call.data["new_slave"]
        # use broadcast by default (0)
        target_slave = call.data.get("target_slave", 0)
        hr_address = call.data.get("hr_address", DEFAULT_HR_NEW_SLAVE)

        # Validate ranges
        if not (1 <= new_slave <= 247):
            raise vol.Invalid("new_slave must be in range 1..247")
        if not (0 <= target_slave <= 247):
            raise vol.Invalid("target_slave must be in range 0..247 (0=broadcast)")

        # Broadcast often yields no reply; pymodbus may throw because of timeout/None.
        # We treat broadcast as 'best effort' and do not fail on missing response.
        try:
            await _run_blocking(client.write_register, hr_address, int(new_slave), int(target_slave))
        except Exception:
            if int(target_slave) == 0:
                # swallow broadcast no-reply errors
                return
            raise

    async def handle_write_coil(call: ServiceCall) -> None:
        slave = call.data["slave"]
        address = call.data["address"]
        value = call.data["value"]
        await _run_blocking(client.write_coil, int(address), bool(value), int(slave))

    async def handle_write_register(call: ServiceCall) -> None:
        slave = call.data["slave"]
        address = call.data["address"]
        value = call.data["value"]
        await _run_blocking(client.write_register, int(address), int(value), int(slave))

    hass.services.async_register(
        DOMAIN,
        "set_slave_id",
        handle_set_slave_id,
        schema=vol.Schema(
            {
                vol.Required("new_slave"): vol.All(vol.Coerce(int), vol.Range(min=1, max=247)),
                vol.Optional("target_slave", default=0): vol.All(vol.Coerce(int), vol.Range(min=0, max=247)),
                vol.Optional("hr_address", default=DEFAULT_HR_NEW_SLAVE): vol.All(vol.Coerce(int), vol.Range(min=0, max=65535)),
            }
        ),
    )

    hass.services.async_register(
        DOMAIN,
        "write_coil",
        handle_write_coil,
        schema=vol.Schema(
            {
                vol.Required("slave"): vol.All(vol.Coerce(int), vol.Range(min=0, max=247)),
                vol.Required("address"): vol.All(vol.Coerce(int), vol.Range(min=0, max=65535)),
                vol.Required("value"): cv.boolean,
            }
        ),
    )

    hass.services.async_register(
        DOMAIN,
        "write_register",
        handle_write_register,
        schema=vol.Schema(
            {
                vol.Required("slave"): vol.All(vol.Coerce(int), vol.Range(min=0, max=247)),
                vol.Required("address"): vol.All(vol.Coerce(int), vol.Range(min=0, max=65535)),
                vol.Required("value"): vol.All(vol.Coerce(int), vol.Range(min=0, max=65535)),
            }
        ),
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    client: ModbusTcpClientCompat = hass.data[DOMAIN].pop(entry.entry_id)
    await hass.async_add_executor_job(client.close)
    if not hass.data[DOMAIN]:
        hass.data.pop(DOMAIN)
    return True
