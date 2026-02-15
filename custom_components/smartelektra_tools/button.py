from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from . import async_run_blocking, get_client, get_state
from .const import DOMAIN


@dataclass(frozen=True, kw_only=True)
class SEToolsButtonDescription(ButtonEntityDescription):
    key_action: str


DESCRIPTIONS: tuple[SEToolsButtonDescription, ...] = (
    SEToolsButtonDescription(
        key="apply_slave",
        key_action="apply_slave",
        name="Apply new slave",
        icon="mdi:content-save",
    ),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    async_add_entities([SEToolsButton(hass, entry, d) for d in DESCRIPTIONS])


class SEToolsButton(ButtonEntity):
    _attr_has_entity_name = True

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, description: SEToolsButtonDescription) -> None:
        self.hass = hass
        self.entry = entry
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "SmartElektra Tools",
        }

    async def async_press(self) -> None:
        state = get_state(self.hass, self.entry.entry_id)
        client = get_client(self.hass, self.entry.entry_id)

        target_slave = int(state.get("target_slave", 0))
        new_slave = int(state.get("new_slave", 1))
        hr_address = int(state.get("hr_new_slave", 0))

        if not (1 <= new_slave <= 247):
            raise ValueError("New slave must be 1..247")
        if not (0 <= target_slave <= 247):
            raise ValueError("Target slave must be 0..247")

        try:
            await async_run_blocking(self.hass, client.write_register, hr_address, new_slave, target_slave)
        except Exception:
            # broadcast commonly yields no reply
            if target_slave == 0:
                return
            raise
