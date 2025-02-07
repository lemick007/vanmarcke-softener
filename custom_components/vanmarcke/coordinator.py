import logging
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)

class ErieWaterSoftenerCoordinator(DataUpdateCoordinator):
    """Gère la récupération des données depuis l'API Erie."""

    def __init__(self, hass, api):
        """Initialise le coordinateur."""
        self.api = api
        super().__init__(
            hass,
            _LOGGER,
            name="erie_water_softener",
            update_interval=timedelta(minutes=10),  # Mise à jour toutes les 10 minutes
        )

    async def _async_update_data(self):
        """Récupère les données depuis l'API."""
        try:
            data = await self.api.get_full_data()
            if not data:
                raise UpdateFailed("Aucune donnée reçue de l'API")
            return data
        except Exception as err:
            _LOGGER.error("Erreur lors de la mise à jour des données: %s", err)
            raise UpdateFailed(err)
