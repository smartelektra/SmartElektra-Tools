from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.restore_state import RestoreEntity

from . import async_run_blocking, get_client, get_state
from .const import DOMAIN


@dataclass(frozen=True, kw_only=True)
class SEToolsSwitchDescription(SwitchEntityDescription):
    key_state: str


DESCRIPTIONS: tuple[SEToolsSwitchDescription, ...] = (
    SEToolsSwitchDescription(
        key="test_output",
        key_state="test_output",
        name="Test output",
        icon="mdi:flash",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    async_add_entities([SEToolsSwitch(hass, entry, d) for d in DESCRIPTIONS])


class SEToolsSwitch(SwitchEntity, RestoreEntity):
    _attr_has_entity_name = True

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, description: SEToolsSwitchDescription) -> None:
        self.hass = hass
        self.entry = entry
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "SmartElektra Tools",
        }

    @property
    def is_on(self) -> bool:
        state = get_state(self.hass, self.entry.entry_id)
        return bool(state.get(self.entity_description.key_state, False))

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last is None or last.state in (None, "unknown", "unavailable"):
            return
        state = get_state(self.hass, self.entry.entry_id)
        state[self.entity_description.key_state] = last.state == "on"
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs) -> None:
        await self._write(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self._write(False)

    async def _write(self, value: bool) -> None:
        state = get_state(self.hass, self.entry.entry_id)
        client = get_client(self.hass, self.entry.entry_id)

        slave = int(state.get("target_slave", 0))
        coil_address = int(state.get("coil_test_output", 0))

        if slave == 0:
            raise ValueError("Set Target slave (current) to the device ID first (not 0/broadcast)")

        await async_run_blocking(self.hass, client.write_coil, coil_address, bool(value), slave)

        state[self.entity_description.key_state] = bool(value)
        self.async_write_ha_state()
