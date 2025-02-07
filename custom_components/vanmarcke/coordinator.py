"""
Gestionnaire de mise à jour des données pour l'intégration Vanmarcke Water Softener.
"""

from datetime import timedelta
import logging

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ErieAPI  # Assure-toi que ton fichier api.py définit bien ErieAPI

_LOGGER = logging.getLogger(__name__)

class VanmarckeWaterCoordinator(DataUpdateCoordinator):
    """Classe qui se charge de récupérer périodiquement les données depuis l'API."""

    def __init__(self, hass, api: ErieAPI):
        """Initialise le coordinateur."""
        self.api = api
        super().__init__(
            hass,
            _LOGGER,
            name="Vanmarcke Water Softener",
            update_interval=timedelta(minutes=15),
        )
        self.device_info = None

    async def _async_update_data(self):
        """Méthode exécutée pour mettre à jour les données."""
        try:
            data = await self.api.get_full_data()
            if not data:
                raise UpdateFailed("Aucune donnée reçue de l'API.")
            
            # Vérification de la présence de quelques clés essentielles
            for key in ["salt_level", "water_volume"]:
                if key not in data:
                    raise UpdateFailed(f"Clé manquante dans les données: {key}")
            
            if not self.device_info:
                # On initialise les informations du dispositif pour Home Assistant
                self.device_info = {
                    "identifiers": {("vanmarcke_water", self.api._device_id)},
                    "name": f"Vanmarcke Softener {self.api._device_id}",
                    "manufacturer": "Vanmarcke",
                    "model": "Erie Connect",
                    "sw_version": data.get("software_version"),
                }
            return data

        except Exception as e:
            _LOGGER.error("Erreur lors de la mise à jour des données: %s", e)
            raise UpdateFailed(f"Erreur lors de la mise à jour des données: {e}")
