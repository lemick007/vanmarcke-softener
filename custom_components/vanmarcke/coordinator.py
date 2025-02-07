class VanmarckeWaterCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, api):
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=15),
        )
        self.api = api
        self.device_info = None

    async def _async_update_data(self):
        try:
            data = await self.api.get_full_data()
            if not self.device_info:
                self.device_info = {
                    "identifiers": {(DOMAIN, self.api._device_id)},
                    "name": f"Vanmarcke Softener {self.api._device_id}",
                    "manufacturer": "Vanmarcke",
                    "model": "Erie Connect",
                    "sw_version": data.get("software_version"),
                }
            return data
        except Exception as e:
            raise UpdateFailed(f"Erreur de mise à jour: {str(e)}")
