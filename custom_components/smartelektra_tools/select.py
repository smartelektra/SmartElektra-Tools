from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.restore_state import RestoreEntity

from . import async_run_blocking, get_client, get_state
from .const import DOMAIN


@dataclass(frozen=True, kw_only=True)
class SEToolsSelectDescription(SelectEntityDescription):
    key_state: str
    hr_state_key: str
    mapping: dict[str, int]


DESCRIPTIONS: tuple[SEToolsSelectDescription, ...] = (
    SEToolsSelectDescription(
        key="button_mode",
        key_state="button_mode",
        hr_state_key="hr_button_mode",
        name="Button mode",
        icon="mdi:toggle-switch",
        options=["mono", "bi"],
        mapping={"mono": 0, "bi": 1},
        entity_category=EntityCategory.CONFIG,
    ),
    SEToolsSelectDescription(
        key="output_level",
        key_state="output_level",
        hr_state_key="hr_output_level",
        name="Output level",
        icon="mdi:electric-switch",
        options=["low", "high"],
        mapping={"low": 0, "high": 1},
        entity_category=EntityCategory.CONFIG,
    ),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    async_add_entities([SEToolsSelect(hass, entry, d) for d in DESCRIPTIONS])


class SEToolsSelect(SelectEntity, RestoreEntity):
    _attr_has_entity_name = True

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, description: SEToolsSelectDescription) -> None:
        self.hass = hass
        self.entry = entry
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "SmartElektra Tools",
        }

    @property
    def current_option(self) -> str | None:
        state = get_state(self.hass, self.entry.entry_id)
        return state.get(self.entity_description.key_state)

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last is None or last.state in (None, "unknown", "unavailable"):
            return
        if last.state in self.entity_description.options:
            state = get_state(self.hass, self.entry.entry_id)
            state[self.entity_description.key_state] = last.state
            self.async_write_ha_state()

    async def async_select_option(self, option: str) -> None:
        if option not in self.entity_description.options:
            raise ValueError("Invalid option")

        state = get_state(self.hass, self.entry.entry_id)
        client = get_client(self.hass, self.entry.entry_id)

        slave = int(state.get("target_slave", 0))
        hr_address = int(state.get(self.entity_description.hr_state_key, 0))
        value = int(self.entity_description.mapping[option])

        # Don't allow broadcast for config writes here (make it explicit)
        if slave == 0:
            raise ValueError("Set Target slave (current) to the device ID first (not 0/broadcast)")

        await async_run_blocking(self.hass, client.write_register, hr_address, value, slave)

        state[self.entity_description.key_state] = option
        self.async_write_ha_state()
