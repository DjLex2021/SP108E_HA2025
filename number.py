from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .pyledshop.effect_speed_entity import EffectSpeedEntity
from .const import DOMAIN
import asyncio
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the number entities for SP108E."""
    light = hass.data[DOMAIN][entry.entry_id]

    # Warte, bis die unique_id der Licht-Entität verfügbar ist
    for _ in range(10):  # Maximal 10 Versuche (ca. 5 Sekunden)
        if light.unique_id:
            break
        await asyncio.sleep(0.5)
    else:
        _LOGGER.error("Unique ID for light entity not available; skipping number entity setup")
        return

    # Wenn unique_id vorhanden, erstelle die Number-Entität
    speed_entity = EffectSpeedEntity(light)
    async_add_entities([speed_entity], update_before_add=True)
