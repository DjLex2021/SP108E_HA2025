from homeassistant.components.number import NumberEntity
from homeassistant.helpers.entity import EntityCategory
import logging

_LOGGER = logging.getLogger(__name__)

class EffectSpeedEntity(NumberEntity):
    """Representation of the effect speed entity."""

    def __init__(self, light):
        """Initialize the effect speed entity."""
        self._light = light
        self._name = f"{light.name} Effect Speed"
        self._unique_id = f"{light.unique_id}_effect_speed"
        self._state = light.effect_speed if light.effect_speed is not None else 128
        self._min_value = 0
        self._max_value = 255
        self._step = 1
        _LOGGER.debug(f"EffectSpeedEntity initialized: {self._unique_id}, Min: {self._min_value}, Max: {self._max_value}, type: {type(self)}, Attributes: {vars(self)}")

    @property
    def device_info(self):
        """Return device information to link this entity to the light."""
        return {
            "identifiers": {("wifi-led-strip-controller", self._light.unique_id)},
            "manufacturer": "BTF-LIGHTING",
            "name": self._light.name,
            "model": "SP108E",
        }

    @property
    def mode(self):
        """Return the mode of the entity ('slider' or 'box')."""
        return "slider"

    @property
    def name(self):
        """Return the name of the entity."""
        return self._name

    @property
    def unique_id(self):
        """Return the unique ID of the entity."""
        return self._unique_id

    @property
    def native_value(self):
        """Return the current speed."""
        #return self._state
        return self._light.effect_speed

    @property
    def native_min_value(self):
        """Return the minimum speed value."""
        return self._min_value

    @property
    def native_max_value(self):
        """Return the maximum speed value."""
        return self._max_value

    @property
    def native_step(self):
        """Return the step size for the slider."""
        return self._step

    @property
    def entity_category(self):
        """Set the entity category (optional)."""
        return EntityCategory.CONFIG

    def set_native_value(self, value):
        """Set the speed of the light effect."""
        self._light.set_speed(int(value))  # Ensure the value is an integer
        self._state = int(value)
        self.schedule_update_ha_state()

    @property
    def should_poll(self):
        """No polling needed for this entity."""
        return True
