from homeassistant.components.sensor import SensorEntity
from homeassistant.const import PERCENTAGE
from homeassistant.util.unit_conversion import UnitOfVolume  # Pour UnitOfVolume.LITERS
# Définition locale pour l'unité de débit d'eau
FLOW_LITERS_PER_MINUTE = "L/min"

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

SENSOR_TYPES = {
    "salt_level": ["Capacité restante", PERCENTAGE, "mdi:shaker-outline", None],
    "water_volume": ["Volume d'eau restant", UnitOfVolume.LITERS, "mdi:water", None],
    "days_remaining": ["Jours restants avant régénération", "jours", "mdi:calendar", None],
    "last_regeneration": ["Dernière régénération", None, "mdi:history", None],
    "nr_regenerations": ["Nombre de régénérations", None, "mdi:counter", None],
    "total_volume": ["Volume total traité", UnitOfVolume.LITERS, "mdi:chart-bar", "water"],
    "software_version": ["Version du logiciel", None, "mdi:information-outline", None],,
    "flow": ["Débit d'eau", FLOW_LITERS_PER_MINUTE, "mdi:water-pump", None],
    "daily_consumption": ["Consommation journalière", UnitOfVolume.LITERS, "mdi:counter", "water"],
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
        if coordinator.device_info:
            self._attr_device_info = coordinator.device_info

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
