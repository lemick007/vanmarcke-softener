from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import SENSOR_TYPES

class VanmarckeSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, sensor_type):
        super().__init__(coordinator)
        self._type = sensor_type
        self._attr_unique_id = f"vanmarcke_{sensor_type}"
        self._attr_name = SENSOR_TYPES[sensor_type]["name"]
        self._attr_icon = SENSOR_TYPES[sensor_type]["icon"]
        self._attr_native_unit_of_measurement = SENSOR_TYPES[sensor_type]["unit"]
        
        if coordinator.device_info:
            self._attr_device_info = coordinator.device_info

    @property
    def native_value(self):
        return self.coordinator.data.get(self._type)
