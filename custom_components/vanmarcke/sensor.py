# sensor.py - Entités de capteurs dynamiques
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import callback
from .const import DOMAIN, SENSOR_MAP

class ErieSensor(SensorEntity):
    """Capteur générique pour les données Erie"""
    
    _attr_should_poll = False
    _attr_has_entity_name = True
    
    def __init__(self, coordinator, device_id, key):
        self._coordinator = coordinator
        self._device_id = device_id
        self._key = key
        self._attr_unique_id = f"erie_{device_id}_{key}"
        self._attr_name = SENSOR_MAP[key]["name"]
        self._attr_icon = SENSOR_MAP[key].get("icon")
        self._attr_native_unit_of_measurement = SENSOR_MAP[key].get("unit")

    @property
    def available(self):
        return self._coordinator.last_update_success
    
    @property
    def native_value(self):
        return self._coordinator.data.get(self._key)

    class VanmarckeSensor(SensorEntity):
    """Capteur basé sur les données du coordinateur"""

    def __init__(self, coordinator, sensor_type):
        self._coordinator = coordinator
        self._type = sensor_type
        self._attr_unique_id = f"vanmarcke_{sensor_type}"
        self._attr_name = SENSOR_MAP[sensor_type]["name"]
        self._attr_icon = SENSOR_MAP[sensor_type].get("icon")
        self._attr_native_unit_of_measurement = SENSOR_MAP[sensor_type].get("unit")

    @property
    def native_value(self):
        """Valeur actuelle du capteur"""
        return self._coordinator.data.get(self._type)


    class VanmarckeSensor(SensorEntity):
    """Capteur basé sur les données du coordinateur"""

    def __init__(self, coordinator, sensor_type):
        self._coordinator = coordinator
        self._type = sensor_type
        self._attr_unique_id = f"vanmarcke_{sensor_type}"
        self._attr_name = SENSOR_MAP[sensor_type]["name"]
        self._attr_icon = SENSOR_MAP[sensor_type].get("icon")
        self._attr_native_unit_of_measurement = SENSOR_MAP[sensor_type].get("unit")

    async def async_added_to_hass(self):
        self._coordinator.async_add_listener(self._handle_update)

    async def async_will_remove_from_hass(self):
        self._coordinator.async_remove_listener(self._handle_update)

    @callback
    def _handle_update(self):
        self.async_write_ha_state()

