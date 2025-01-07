from .pyledshop import WifiLedShopLight
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
import logging

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up sp108e lights."""
    host = entry.data.get("host")
    name = entry.data.get("name")
    
    _LOGGER.debug("Setting up SP108E entity for host: %s", entry.data.get("host"))

    # Erstelle die Entität für das Licht
    entity = WifiLedShopLight(host, name)
    async_add_entities([entity], update_before_add=True)
    return True
