from datetime import datetime, time
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import PERCENTAGE
from homeassistant.util.unit_conversion import UnitOfVolume  # Pour UnitOfVolume.LITERS
# Définition locale pour l'unité de débit d'eau
FLOW_LITERS_PER_MINUTE = "L/min"

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

# SENSOR_TYPES: [Nom, Unité, Icône, Device_class optionnel]
SENSOR_TYPES = {
    "salt_level": ["Capacité restante", PERCENTAGE, "mdi:shaker-outline", None],
    "water_volume": ["Volume d'eau restant", UnitOfVolume.LITERS, "mdi:water", None],
    "days_remaining": ["Jours restants avant régénération", "jours", "mdi:calendar", None],
    "last_regeneration": ["Dernière régénération", None, "mdi:history", None],
    "nr_regenerations": ["Nombre de régénérations", None, "mdi:counter", None],
    # Pour les capteurs cumulés, le device_class "water" est requis et la state_class doit être "total"
    "total_volume": ["Volume total traité", UnitOfVolume.LITERS, "mdi:chart-bar", "water"],
    "software_version": ["Version du logiciel", None, "mdi:information-outline", None],
    "flow": ["Débit d'eau", FLOW_LITERS_PER_MINUTE, "mdi:water-pump", None],
    # Pour la consommation journalière, on souhaite un cumul qui se réinitialise chaque jour
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
        # Si un device_class est défini, on l'assigne
        if SENSOR_TYPES[sensor_type][3]:
            self._attr_device_class = SENSOR_TYPES[sensor_type][3]
        # Pour les capteurs cumulés (total_volume et daily_consumption), définir state_class "total" et last_reset
        if sensor_type in ["total_volume", "daily_consumption"]:
            self._attr_state_class = "total"
            # Définir last_reset au début du jour courant
            self._attr_last_reset = datetime.combine(datetime.now().date(), time())
        if coordinator.device_info:
            self._attr_device_info = coordinator.device_info

    @property
    def native_value(self):
        """Retourne la valeur actuelle du capteur."""
        current_value = self.coordinator.data.get(self._sensor_type)
    
        if self._sensor_type == "total_volume" and current_value is not None and current_value == 0:
            return None  # Ignore les valeurs "0" pour total_volume
        return current_value

    @property
    def unique_id(self):
        """Retourne un ID unique basé sur le type de capteur."""
        return f"erie_{self._sensor_type}"

    @property
    def should_poll(self):
        """Désactive le polling, car nous utilisons le DataUpdateCoordinator."""
        return False
