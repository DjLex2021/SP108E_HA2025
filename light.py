from .pyledshop import WifiLedShopLight
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up sp108e lights."""
    host = entry.data.get("host")
    name = entry.data.get("name")

    _LOGGER.debug("Setting up SP108E entity for host: %s", entry.data.get("host"))

    # Erstelle die Instanz des Lichts
    light = WifiLedShopLight(host, name)
    
    # Speichere die Instanz in hass.data, damit andere Plattformen darauf zugreifen können
    hass.data[DOMAIN][entry.entry_id] = light

    # Füge die Entität für das Licht hinzu
    async_add_entities([light], update_before_add=True)

    return True
