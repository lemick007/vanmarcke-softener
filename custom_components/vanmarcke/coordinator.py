from datetime import timedelta
import logging
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

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
            if not self.device_info:
                self.device_info = {
                    "identifiers": {("vanmarcke_water", self.api._device_id)},
                    "name": f"Vanmarcke Softener {self.api._device_id}",
                    "manufacturer": "Vanmarcke",
                    "model": "Erie Connect",
                }
            return data
        except Exception as e:
            _LOGGER.error("Update failed: %s", str(e))
            raise
