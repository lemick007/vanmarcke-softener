# coordinator.py
from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ErieAPI, ErieAPIError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class VanmarckeWaterCoordinator(DataUpdateCoordinator):
    """Coordinateur principal pour la collecte des données"""

    def __init__(self, hass: HomeAssistant, api: ErieAPI):
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=5),
        )
        self.api = api
        self._device_id = None

    async def _async_update_data(self) -> dict[str, Any]:
        """Mise à jour des données avec gestion robuste des erreurs"""
        try:
            # 1. Récupération des appareils
            if not self._device_id:
                devices = await self.api.get_devices()
                if not devices:
                    raise UpdateFailed("Aucun appareil Vanmarcke trouvé")
                self._device_id = devices[0]["id"]

            # 2. Collecte des données principales
            dashboard = await self.api.get_dashboard_data(self._device_id)
            settings = await self.api.get_settings(self._device_id)

            # 3. Structuration des données
            return {
                "salt_level": dashboard.get("saltLevelPercentage"),
                "water_hardness": settings.get("waterHardness"),
                "current_flow": dashboard.get("currentFlowRate"),
                "total_consumption": dashboard.get("totalConsumption"),
                "last_regeneration": dashboard.get("lastRegenerationDate"),
            }

        except ErieAPIError as err:
            raise UpdateFailed(f"Erreur API: {err}") from err
        except KeyError as err:
            raise UpdateFailed(f"Données manquantes: {err}") from err
