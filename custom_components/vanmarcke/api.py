import aiohttp
import logging
from typing import Any, Dict

_LOGGER = logging.getLogger(__name__)

class ErieAPI:
    def __init__(self, email: str, password: str, session: aiohttp.ClientSession):
        self._email = email
        self._password = password
        self._session = session
        self._auth_headers = {}
        self._device_id = None
        self._base_url = "https://connectmysoftenerapi.pentair.eu/api/erieapp/v1"

    async def authenticate(self) -> bool:
        try:
            async with self._session.post(
                f"{self._base_url}/auth/sign_in",
                json={"email": self._email, "password": self._password}
            ) as response:
                if response.status != 200:
                    raise Exception(f"HTTP Error: {response.status}")
                
                self._auth_headers = {
                    "Access-Token": response.headers["Access-Token"],
                    "Client": response.headers["Client"],
                    "Uid": response.headers["Uid"]
                }
                return True
                
        except aiohttp.ClientError as e:
            _LOGGER.error("Network error: %s", str(e))
            raise
        except KeyError as e:
            _LOGGER.error("Missing header: %s", str(e))
            raise

    async def get_full_data(self) -> Dict[str, Any]:
        try:
            device_id = await self._get_device_id()
        except Exception as e:
            _LOGGER.error("Unable to retrieve device ID: %s", str(e))
            return {}

        endpoints = {
            "dashboard": f"water_softeners/{device_id}/dashboard",
            "settings": f"water_softeners/{device_id}/settings",
            "regenerations": f"water_softeners/{device_id}/regenerations",
            "info": f"water_softeners/{device_id}/info"
        }
        
        data = {}
        for key, endpoint in endpoints.items():
            try:
                async with self._session.get(
                    f"{self._base_url}/{endpoint}", 
                    headers=self._auth_headers
                ) as response:
                    if response.status != 200:
                        _LOGGER.error(f"Error fetching {key}: HTTP {response.status}")
                        continue
                    data[key] = await response.json()
            except Exception as e:
                _LOGGER.error("Error fetching %s: %s", key, str(e))
        
        return self._parse_data(data)

    async def _get_device_id(self) -> str:
        if not self._device_id:
            try:
                async with self._session.get(
                    f"{self._base_url}/water_softeners",
                    headers=self._auth_headers
                ) as response:
                    if response.status != 200:
                        raise Exception(f"HTTP error {response.status}")
                    
                    devices = await response.json()
                    if not devices or not isinstance(devices, list):
                        raise ValueError("No devices found")
                    
                    self._device_id = devices[0]["profile"]["id"]
            except Exception as e:
                _LOGGER.error("Error retrieving device ID: %s", str(e))
                raise
        return self._device_id

    def _parse_data(self, raw_data: Dict) -> Dict:
        parsed = {}
        try:
            # Dashboard data
            dashboard = raw_data.get("dashboard", {}).get("status", {})
            parsed.update({
                "salt_level": dashboard.get("percentage"),
                "water_volume": dashboard.get("extra", "0 L").split()[0],
                "days_remaining": dashboard.get("days_remaining")
            })
            
            # Settings
            settings = raw_data.get("settings", {}).get("settings", {})
            parsed["water_hardness"] = settings.get("install_hardness")
            
            # Last regeneration
            regenerations = raw_data.get("regenerations", [])
            if regenerations:
                parsed["last_regeneration"] = regenerations[0].get("datetime")
                parsed["salt_used"] = regenerations[0].get("salt_used")
            
            # Device info
            info = raw_data.get("info", {})
            parsed["total_volume"] = info.get("total_volume", "0 L").split()[0]
            parsed["software_version"] = info.get("software")
            
        except Exception as e:
            _LOGGER.error("Error parsing data: %s", str(e))
        
        return parsed
