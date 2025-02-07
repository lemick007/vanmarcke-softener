from datetime import timedelta
import logging
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.exceptions import ConfigEntryAuthFailed

from .api import ErieAPI

_LOGGER = logging.getLogger(__name__)

class VanmarckeWaterCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, api: ErieAPI):
        super().__init__(
            hass,
            _LOGGER,
            name="Vanmarcke Water",
            update_interval=timedelta(minutes=15),
        )
        self.api = api
        self.device_info = None

    async def _async_update_data(self):
        try:
            data = await self.api.get_full_data()
            if not data:
                raise UpdateFailed("Empty data received from API")
            
            # Check for essential keys
            required_keys = ["salt_level", "water_volume"]
            for key in required_keys:
                if key not in data:
                    raise UpdateFailed(f"Missing key in data: {key}")
            
            if not self.device_info:
                self.device_info = {
                    "identifiers": {("vanmarcke_water", self.api._device_id)},
                    "name": f"Vanmarcke Softener {self.api._device_id}",
                    "manufacturer": "Vanmarcke",
                    "model": "Erie Connect",
                    "sw_version": data.get("software_version")
                }
            return data
        except Exception as e:
            _LOGGER.error("Fatal error updating data: %s", str(e))
            raise UpdateFailed(f"Error updating data: {str(e)}")
