from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.number import NumberEntity, NumberEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.restore_state import RestoreEntity

from . import get_state
from .const import DOMAIN


@dataclass(frozen=True, kw_only=True)
class SEToolsNumberDescription(NumberEntityDescription):
    key_state: str


DESCRIPTIONS: tuple[SEToolsNumberDescription, ...] = (
    SEToolsNumberDescription(
        key="target_slave",
        key_state="target_slave",
        name="Target slave (current)",
        icon="mdi:identifier",
        native_min_value=0,
        native_max_value=247,
        native_step=1,
    ),
    SEToolsNumberDescription(
        key="new_slave",
        key_state="new_slave",
        name="New slave",
        icon="mdi:identifier",
        native_min_value=1,
        native_max_value=247,
        native_step=1,
    ),
    SEToolsNumberDescription(
        key="hr_new_slave",
        key_state="hr_new_slave",
        name="HR address: new slave",
        icon="mdi:format-list-numbered",
        native_min_value=0,
        native_max_value=65535,
        native_step=1,
        entity_category=EntityCategory.CONFIG,
    ),
    SEToolsNumberDescription(
        key="hr_button_mode",
        key_state="hr_button_mode",
        name="HR address: button mode",
        icon="mdi:format-list-numbered",
        native_min_value=0,
        native_max_value=65535,
        native_step=1,
        entity_category=EntityCategory.CONFIG,
    ),
    SEToolsNumberDescription(
        key="hr_output_level",
        key_state="hr_output_level",
        name="HR address: output level",
        icon="mdi:format-list-numbered",
        native_min_value=0,
        native_max_value=65535,
        native_step=1,
        entity_category=EntityCategory.CONFIG,
    ),
    SEToolsNumberDescription(
        key="coil_test_output",
        key_state="coil_test_output",
        name="Coil address: test output",
        icon="mdi:format-list-numbered",
        native_min_value=0,
        native_max_value=65535,
        native_step=1,
        entity_category=EntityCategory.CONFIG,
    ),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    async_add_entities([SEToolsNumber(hass, entry, d) for d in DESCRIPTIONS])


class SEToolsNumber(NumberEntity, RestoreEntity):
    _attr_has_entity_name = True

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, description: SEToolsNumberDescription) -> None:
        self.hass = hass
        self.entry = entry
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "SmartElektra Tools",
        }

    @property
    def native_value(self) -> float | None:
        state = get_state(self.hass, self.entry.entry_id)
        val = state.get(self.entity_description.key_state)
        return float(val) if val is not None else None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        # restore last value if available
        last = await self.async_get_last_state()
        if last is None or last.state in (None, "unknown", "unavailable"):
            return
        try:
            restored = float(last.state)
        except ValueError:
            return
        await self.async_set_native_value(restored)

    async def async_set_native_value(self, value: float) -> None:
        state = get_state(self.hass, self.entry.entry_id)
        state[self.entity_description.key_state] = int(value)
        self.async_write_ha_state()
