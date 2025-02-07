class ErieAPI:
    def __init__(self, email: str, password: str, session: aiohttp.ClientSession):
        self._email = email
        self._password = password
        self._session = session
        self._auth_headers = {}
        self._device_id = None
        self._base_url = "https://connectmysoftenerapi.pentair.eu/api/erieapp/v1"

    async def authenticate(self):
        url = f"{self._base_url}/auth/sign_in"
        data = {"email": self._email, "password": self._password}
        
        async with self._session.post(url, json=data) as response:
            if response.status != 200:
                raise InvalidAuth(f"Erreur {response.status}")
            
            self._auth_headers = {
                "Access-Token": response.headers["Access-Token"],
                "Client": response.headers["Client"],
                "Uid": response.headers["Uid"]
            }
            return True

    async def get_device_data(self):
        if not self._device_id:
            url = f"{self._base_url}/water_softeners"
            async with self._session.get(url, headers=self._auth_headers) as response:
                devices = await response.json()
                self._device_id = devices[0]["profile"]["id"]
        return self._device_id

    async def get_full_data(self):
        device_id = await self.get_device_data()
        
        endpoints = {
            "dashboard": f"water_softeners/{device_id}/dashboard",
            "settings": f"water_softeners/{device_id}/settings",
            "regenerations": f"water_softeners/{device_id}/regenerations",
            "info": f"water_softeners/{device_id}/info",
            "flow": f"water_softeners/{device_id}/flow"
        }
        
        data = {}
        for key, endpoint in endpoints.items():
            try:
                async with self._session.get(f"{self._base_url}/{endpoint}", headers=self._auth_headers) as response:
                    data[key] = await response.json()
            except Exception as e:
                _LOGGER.error("Erreur récupération %s: %s", key, str(e))
        
        return self._parse_data(data)

    def _parse_data(self, raw_data):
        """Transforme les données brutes en format utilisable"""
        parsed = {}
        
        # Dashboard
        dashboard = raw_data.get("dashboard", {})
        if status := dashboard.get("status"):
            parsed.update({
                "salt_level": status.get("percentage"),
                "water_volume": status.get("extra").split()[0],  # "1331 L" → 1331
                "days_remaining": status.get("days_remaining")
            })
        
        # Settings
        if settings := raw_data.get("settings", {}).get("settings"):
            parsed["water_hardness"] = settings.get("install_hardness")
            parsed["current_hardness"] = settings.get("hard_units", {}).get("value")
        
        # Dernière régénération
        if regens := raw_data.get("regenerations"):
            last_regen = regens[0] if regens else {}
            parsed.update({
                "last_regeneration": last_regen.get("datetime"),
                "salt_used": last_regen.get("salt_used")
            })
        
        # Info générale
        if info := raw_data.get("info", {}):
            parsed.update({
                "total_volume": info.get("total_volume").split()[0],
                "software_version": info.get("software")
            })
        
        # Débit d'eau
        if flow := raw_data.get("flow", {}):
            parsed["current_flow"] = flow.get("flow")
        
        return parsed
