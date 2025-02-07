from homeassistant.components.sensor import SensorEntity
from homeassistant.const import PERCENTAGE, FLOW_LITERS_PER_MINUTE
from homeassistant.util.unit_conversion import UnitOfVolume  # Pour UnitOfVolume.LITERS
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

SENSOR_TYPES = {
    "salt_level": ["Niveau de sel", PERCENTAGE, "mdi:shaker-outline"],
    "water_volume": ["Volume d'eau restant", UnitOfVolume.LITERS, "mdi:water"],
    "days_remaining": ["Jours restants avant régénération", "jours", "mdi:calendar"],
    "last_regeneration": ["Dernière régénération", None, "mdi:history"],
    "total_volume": ["Volume total traité", UnitOfVolume.LITERS, "mdi:chart-bar"],
    "software_version": ["Version du logiciel", None, "mdi:information-outline"],
    "flow": ["Débit d'eau", FLOW_LITERS_PER_MINUTE, "mdi:water-pump"],
}

async def async_setup_entry(hass, entry, async_add_entities):
    """Configure les capteurs Vanmarcke Water depuis une entrée de configuration."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(ErieSensor(coordinator, sensor) for sensor in SENSOR_TYPES)

class ErieSensor(CoordinatorEntity, SensorEntity):
    """Représente un capteur Vanmarcke Water Softener."""

    def __init__(self, coordinator, sensor_type):
        """Initialise le capteur."""
        super().__init__(coordinator)
        self._sensor_type = sensor_type
        self._attr_name = SENSOR_TYPES[sensor_type][0]
        self._attr_icon = SENSOR_TYPES[sensor_type][2]
        self._attr_native_unit_of_measurement = SENSOR_TYPES[sensor_type][1]

    @property
    def native_value(self):
        """Retourne la valeur actuelle du capteur."""
        return self.coordinator.data.get(self._sensor_type)

    @property
    def unique_id(self):
        """Retourne un ID unique basé sur le type de capteur."""
        return f"erie_{self._sensor_type}"

    @property
    def should_poll(self):
        """Désactive le polling, car nous utilisons le DataUpdateCoordinator."""
        return False
