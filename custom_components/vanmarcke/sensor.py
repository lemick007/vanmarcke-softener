from homeassistant.components.sensor import SensorEntity
from homeassistant.const import PERCENTAGE, VOLUME_LITERS, TIME_DAYS, FLOW_LITERS_PER_MINUTE

SENSOR_TYPES = {
    "salt_level": ["Niveau de sel", PERCENTAGE, "mdi:shaker-outline"],
    "water_volume": ["Volume d'eau restant", VOLUME_LITERS, "mdi:water"],
    "days_remaining": ["Jours restants avant régénération", TIME_DAYS, "mdi:calendar"],
    "last_regeneration": ["Dernière régénération", None, "mdi:history"],
    "total_volume": ["Volume total traité", VOLUME_LITERS, "mdi:chart-bar"],
    "software_version": ["Version du logiciel", None, "mdi:information-outline"],
    "flow": ["Débit d'eau", FLOW_LITERS_PER_MINUTE, "mdi:water-pump"],
}

async def async_setup_entry(hass, entry, async_add_entities):
    """Configure les capteurs Erie depuis une entrée de configuration."""
    coordinator = hass.data["erie"][entry.entry_id]
    async_add_entities(ErieSensor(coordinator, sensor) for sensor in SENSOR_TYPES)

class ErieSensor(SensorEntity):
    """Représente un capteur Erie Water Softener."""

    def __init__(self, coordinator, sensor_type):
        """Initialise le capteur."""
        self._coordinator = coordinator
        self._sensor_type = sensor_type
        self._attr_name = SENSOR_TYPES[sensor_type][0]
        self._attr_icon = SENSOR_TYPES[sensor_type][2]
        self._attr_native_unit_of_measurement = SENSOR_TYPES[sensor_type][1]

    @property
    def native_value(self):
        """Retourne la valeur actuelle du capteur."""
        return self._coordinator.data.get(self._sensor_type)

    @property
    def unique_id(self):
        """Retourne un ID unique basé sur le type de capteur."""
        return f"erie_{self._sensor_type}"

    async def async_update(self):
        """Demande une mise à jour des données."""
        await self._coordinator.async_request_refresh()
