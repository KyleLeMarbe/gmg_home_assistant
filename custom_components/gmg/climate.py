"""Green Mountain Grill"""


from ast import Not
from html import entities
from importlib.metadata import entry_points
from .gmg import grills, grill, createGrillObject
import logging
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from typing import List, Optional
from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature, UnitOfTemperature, ATTR_TEMPERATURE
from homeassistant.components.climate import PLATFORM_SCHEMA
from homeassistant.components.climate.const import HVACMode

from homeassistant.const import CONF_HOST

_LOGGER = logging.getLogger(__name__)

CONF_GRILL_NAME = "grill_name"
DEFAULT_NAME = "GMGGrill"

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_HOST): cv.string,
    vol.Optional(CONF_GRILL_NAME, default=DEFAULT_NAME): cv.string
})

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    entities = []
    _LOGGER.debug("Looking for grills")

    hostIP = config.get(CONF_HOST)
    hostName = config.get(CONF_GRILL_NAME)

    _LOGGER.debug(f"hostIP from config file: {hostIP}")

    if hostIP is None:
        # look for grills.. timeout = 2
        _LOGGER.debug("No grills configured in yml, autodiscovering grills.")
        all_grills = grills(2)
    else:
        _LOGGER.debug(f"Grill found in configuration file. {hostIP},{hostName}")
        all_grills = createGrillObject(hostIP, hostName)

    for my_grill in all_grills: 
        _LOGGER.debug(f"Found grill IP: {my_grill._ip} Serial: {my_grill._serial_number}")

        entities.append(GmgGrill(my_grill))

        count = 1
        probe_count = 2

        while count <= probe_count:
            entities.append(GmgGrillProbe(my_grill, count))
            count += 1

    async_add_entities(entities)

    return

class GmgGrill(ClimateEntity):
    """Representation of a Green Mountain Grill smoker"""

    def __init__(self, grill) -> None:
        """Initialize the Grill."""
        self._grill = grill
        self._unique_id = "{}".format(self._grill._serial_number)
        
        _LOGGER.debug(f"Found grill IP: {self._grill._ip} Serial: {self._grill._serial_number}")
        
        self.update()


    def set_temperature(self, **kwargs):
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        _currentTargetTemp = self.target_temperature

        if temperature is None:
            return
        if temperature == _currentTargetTemp:
            return
        
        # Add in section if grill is not on to error... 
        if self.hvac_mode == HVACMode.OFF:
            _LOGGER.warning("Grill is not on, cannot set temperature")
            # TODO: Add in section to turn on grill.. May not do this to prevent accidential turning on of grill. 
            return

        grillTemp = self.current_temperature

        if grillTemp < 140:
            # GMG manual says need to wait until 150 F at least before changing temp 
            _LOGGER.warning(f"Grill is not 150 F, cannot set temperature. Temp is {grillTemp}")
            return

        try:
            _LOGGER.debug(f"Setting temperature to {temperature}")
            self._grill.set_temp(int(temperature))
        except Exception as ex:
            _LOGGER.error(f"Error setting temperature: {temperature}")

    def set_hvac_mode(self, hvac_mode: str) -> None:
        """Set the operation mode"""
        if hvac_mode == HVACMode.HEAT:
            self._grill.power_on()
        elif hvac_mode == HVACMode.OFF:
            self._grill.power_off()
        elif hvac_mode == HVACMode.FAN_ONLY:
            self._grill.power_on_cool()
        else:
            _LOGGER.error(f"Unsupported hvac mode: {hvac_mode}")

        self.update()

    def turn_off(self):
        """Turn device off."""
        return self._grill.power_off()
    
    @property
    def supported_features(self):
        """Return the list of supported features."""
        return (ClimateEntityFeature.TARGET_TEMPERATURE)
    
    @property
    def icon(self):
        return "mdi:grill"

    @property
    def hvac_modes(self) -> List[str]:
        """Return the supported operations."""
        return [ HVACMode.HEAT, HVACMode.FAN_ONLY, HVACMode.OFF]

    @property
    def hvac_mode(self):
        """Return current HVAC operation."""
        if self._state['on'] == 1:
            return HVACMode.HEAT
        elif self._state['on'] == 2:
            return HVACMode.FAN_ONLY

        return HVACMode.OFF

    @property
    def name(self)  -> None:
        """Return unique ID of grill which is GMGSERIAL_NUMBER"""
        return self._unique_id

    # Climate Properties
    @property
    def temperature_unit(self) -> None:
        """Return the unit of measurement for the grill"""
        return UnitOfTemperature.FAHRENHEIT

    @property
    def current_temperature(self) -> None:
        """Return current temp of the grill"""
        grillTemp = self._state.get('temp')
        tempMultiplier = self._state.get('temp_high')

        if tempMultiplier == 1:
            grillTemp = 256 + grillTemp

        return grillTemp

    @property
    def target_temperature_step(self) -> None:
        """Return the supported step of target temp"""
        return 1
        
    @property
    def target_temperature(self) -> None:
        """Return what the temp is set to go to"""
        grillSetTemp = self._state.get('grill_set_temp')
        tempMultiplier = self._state.get('grill_set_temp_high')

        if tempMultiplier == 1:
            grillSetTemp = 256 + grillSetTemp

        return grillSetTemp

    @property
    def max_temp(self) -> None:
        """Return the maximum temperature."""
        return self._grill.MAX_TEMP_F

    @property
    def min_temp(self) -> None:
        """Return the minimum temperature."""
        return self._grill.MIN_TEMP_F

    @property
    def unique_id(self) -> None:
        """Return a unique ID."""
        return self._unique_id

    def update(self) -> None:
        """Get latest data."""
        self._state = self._grill.status()

        _LOGGER.debug(f"State: {self._state}")

class GmgGrillProbe(ClimateEntity):
    """Representation of a Green Mountain Grill smoker food probes"""

    def __init__(self, grill, probe_count) -> None:
        """Initialize the Grill."""
        self._grill = grill
        self._unique_id = f"{self._grill._serial_number}_probe_{probe_count}"
        self._probe_count = probe_count

        _LOGGER.debug(f"From grill: {self._grill._serial_number} init probe: {probe_count}")

        self.update()


    def set_temperature(self, **kwargs):
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)

        if temperature is None:
            return
        if temperature == self._state['probe1_set_temp']:
            return
        
        # Add in section if grill is not on to error... 
        if self._state['on'] == 0:
            _LOGGER.error("Grill is not on, cannot set temperature")
            return

        try:
            _LOGGER.debug(f"Setting probe temperature to {temperature}")
            self._grill.set_temp_probe(int(temperature), self._probe_count)
        except Exception as ex:
            _LOGGER.error(f"Error setting temperature: {temperature}")


    @property
    def hvac_modes(self) -> List[str]:
        """Return the supported operations."""
        return [HVACMode.OFF]

    @property
    def hvac_mode(self):
        """Return current HVAC operation."""

        # Probe temp is 89 when it is not plugged in... need to find out if better way to find if connected or not..
        if self._state['on'] == 1 and self._state[f'probe{self._probe_count}_temp'] != 89:
            return HVACMode.HEAT

        return HVACMode.OFF

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return (ClimateEntityFeature.TARGET_TEMPERATURE)
    
    @property
    def icon(self):
        return "mdi:thermometer-lines"

    @property
    def name(self)  -> None:
        """Return unique ID of grill which is GMGSERIAL_NUMBER_probe_count"""
        return self._unique_id

    @property
    def temperature_unit(self) -> None:
        """Return the unit of measurement for the probe"""
        return UnitOfTemperature.FAHRENHEIT

    @property
    def current_temperature(self) -> None:
        """Return current temp of the grill"""
        return self._state.get(f'probe{self._probe_count}_temp')

    @property
    def target_temperature_step(self) -> None:
        """Return the supported step of target temp"""        
        return 1
        
    @property
    def target_temperature(self) -> None:
        """Return what the temp is set to go to"""
        return self._state.get(f'probe{self._probe_count}_set_temp')

    @property
    def max_temp(self) -> None:
        """Return the maximum temperature."""
        return self._grill.MAX_TEMP_F_PROBE

    @property
    def min_temp(self) -> None:
        """Return the minimum temperature."""
        return self._grill.MIN_TEMP_F_PROBE

    @property
    def unique_id(self) -> None:
        """Return a unique ID."""
        return self._unique_id

    def update(self) -> None:
        """Get latest data."""
        self._state = self._grill.status()

        _LOGGER.debug(f"State: {self._state}")
