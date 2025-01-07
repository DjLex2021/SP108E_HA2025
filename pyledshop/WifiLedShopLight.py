import socket
import asyncio
import logging
from .effects import MONO_EFFECTS, PRESET_EFFECTS
from .constants import Command, CommandFlag
from .utils import clamp
from .WifiLedShopLightState import WifiLedShopLightState
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_EFFECT,
    ATTR_HS_COLOR,
    ColorMode,
    LightEntity,
    LightEntityFeature
)
import homeassistant.util.color as color_util
from time import sleep

_LOGGER = logging.getLogger(__name__)

class WifiLedShopLight(LightEntity):
    def __init__(self, ip, name, port=8189, timeout=1, retries=5):
        self._name = name
        self._ip = ip
        self._port = port
        self._timeout = timeout
        self._retries = retries
        self._state = WifiLedShopLightState()
        self._sock = None
        self._unique_id = None  # Will be set during the first sync

    async def async_added_to_hass(self):
        """Run when entity is added to Home Assistant."""
        await self.async_update()

    async def async_update(self):
        """Asynchronously update the light state."""
        if self._unique_id is None:
            _LOGGER.debug(f"Attempting to fetch unique_id for {self._name} ({self._ip})")
            unique_id = await asyncio.to_thread(self.send_command, Command.GET_ID, [])
            if unique_id:
                self._unique_id = unique_id.decode("utf-8")
                _LOGGER.info(f"Fetched unique_id for {self._name}: {self._unique_id}")
            else:
                _LOGGER.warning(f"Failed to fetch unique_id for {self._name} ({self._ip})")

        result = await asyncio.to_thread(self.send_command, Command.SYNC, [])
        if result:
            state = bytearray(result)
            self._state.update_from_sync(state)
        else:
            _LOGGER.warning(f"Failed to update state for {self._name} ({self._ip}).")

    def update(self):
        response = self.send_command(Command.SYNC, [])
        state = bytearray(response)
        self._state.update_from_sync(state)
        return

    def send_command(self, command, data=[]):
        result = None
        min_data_len = 3
        padded_data = data + [0] * (min_data_len - len(data))
        raw_data = [CommandFlag.START, *padded_data, command, CommandFlag.END]
        attempts = 0
        while True:
            try:
                self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._sock.settimeout(self._timeout)
                self._sock.connect((self._ip, self._port))
                
                _LOGGER.debug(f"Sending raw data ({self._ip}: {self.name}): {raw_data} to {self._ip}:{self._port}")
                
                self._sock.sendall(bytes(raw_data))
                if command in (Command.GET_ID, Command.SYNC):
                    result = self._sock.recv(1024)
        
                _LOGGER.debug(f"Received data ({self._ip}: {self.name}): {result}")
                
                self._sock.shutdown(socket.SHUT_RDWR)
                self._sock.close()
                self._sock = None
                return result
            except (socket.timeout, BrokenPipeError):
                if (attempts < self._retries):
                    attempts += 1
                    if self._sock:
                        self._sock.close()
                else:
                    raise

    def set_color(self, r=0, g=0, b=0):
        r, g, b = map(clamp, (r, g, b))
        _LOGGER.debug(f"Setting color: R={r}, G={g}, B={b} for {self._name} ({self._ip})")
        self._state.color = (r, g, b)
        response = self.send_command(Command.SET_COLOR, [int(r), int(g), int(b)])

    def set_brightness(self, brightness=0):
        brightness = clamp(brightness)
        self._state.brightness = brightness
        self.send_command(Command.SET_BRIGHTNESS, [int(brightness)])

    def set_effect(self, effect):
        effects = {**MONO_EFFECTS, **PRESET_EFFECTS}
        preset = clamp(effects.get(effect, 0))
        self._state.mode = preset
        self.send_command(Command.SET_PRESET, [int(preset)])

    def toggle(self):
        """
        Toggles the state of the light without checking the current state
        """
        initial_state = self._state.is_on
        self.send_command(Command.TOGGLE, [])
        self.update()
        _LOGGER.debug(f"Toggle! {self._ip}: {self._name} - Current state is: {self._state.is_on}")
        while initial_state == self._state.is_on:
            sleep(0.5)
            self.toggle()

    def turn_on(self, **kwargs):
        _LOGGER.debug(f"turn_on called with kwargs: {kwargs}")
        if ATTR_BRIGHTNESS in kwargs:
            _LOGGER.debug(f"Setting brightness to {kwargs[ATTR_BRIGHTNESS]} for {self._name}")
            self.set_brightness(kwargs[ATTR_BRIGHTNESS])
        if "rgb_color" in kwargs:  # Prüfung auf rgb_color
            r, g, b = kwargs["rgb_color"]
            _LOGGER.debug(f"RGB Color detected: R={r}, G={g}, B={b}")
            self.set_color(r, g, b)
        if ATTR_EFFECT in kwargs:
            _LOGGER.debug(f"Setting effect to {kwargs[ATTR_EFFECT]} for {self._name}")
            self.set_effect(kwargs[ATTR_EFFECT])
        if not self._state.is_on:
            _LOGGER.debug(f"Light {self._name} is off, toggling it on.")
            self.toggle()
        else:
            _LOGGER.debug(f"Light {self._name} is already on")
    
    def turn_off(self):
        if self._state.is_on:
            self.toggle()
        else:
            _LOGGER.debug(f"Already off ({self._ip}: {self._name})")

    @property
    def unique_id(self):
        if not self._unique_id:
            result = self.send_command(Command.GET_ID, [])
            if result:
                self._unique_id = result.decode('utf-8')
        return self._unique_id

    @property
    def device_info(self):
        return {
            "identifiers": {("wifi-led-strip-controller", self._unique_id)},
            "manufacturer": "BTF-LIGHTING",
            "name": self._name,
            "model": "SP108E",
        }

    @property
    def name(self):
        return self._name

    @property
    def brightness(self):
        return self._state.brightness

    @property
    def is_on(self):
        return self._state.is_on

    @property
    def hs_color(self):
        """Return the current color in HS format."""
        r, g, b = self._state.color
        h, s = color_util.color_RGB_to_hs(r, g, b)
        _LOGGER.debug(f"Current HS color: H={h}, S={s} (from RGB: R={r}, G={g}, B={b})")
        return h, s
        
    @property
    def rgb_color(self):
        """Return the current color in RGB format."""
        r, g, b = self._state.color
        _LOGGER.debug(f"Current RGB color is: R={r}, G={g}, B={b}")
        return self._state.color

    @property
    def effect_list(self):
        return list({**MONO_EFFECTS, **PRESET_EFFECTS})

    @property
    def effect(self):
        effects = {**MONO_EFFECTS, **PRESET_EFFECTS}
        return next((key for key, val in effects.items() if val == self._state.mode), None)

    @property
    def supported_color_modes(self):
        return {ColorMode.RGB}

    @property
    def color_mode(self):
        """Return the color mode of the light."""
        effects = {**MONO_EFFECTS, **PRESET_EFFECTS}
        current_effect = next((key for key, val in effects.items() if val == self._state.mode), None)
    
        if current_effect == "Solid (custom color)":
            return ColorMode.RGB
        return ColorMode.BRIGHTNESS

    @property
    def supported_features(self):
        return LightEntityFeature.EFFECT
