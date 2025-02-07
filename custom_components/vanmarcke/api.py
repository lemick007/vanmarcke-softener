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
            logging.error("Network error: %s", str(e))
            raise
        except KeyError as e:
            logging.error("Missing header: %s", str(e))
            raise

    async def get_full_data(self) -> Dict[str, Any]:
        device_id = await self._get_device_id()
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
                    data[key] = await response.json()
            except Exception as e:
                logging.error("Error fetching %s: %s", key, str(e))
        
        return self._parse_data(data)

    async def _get_device_id(self) -> str:
        if not self._device_id:
            async with self._session.get(
                f"{self._base_url}/water_softeners",
                headers=self._auth_headers
            ) as response:
                devices = await response.json()
                self._device_id = devices[0]["profile"]["id"]
        return self._device_id

    def _parse_data(self, raw_data: Dict) -> Dict:
        parsed = {}
        try:
            # Dashboard data
            parsed.update({
                "salt_level": raw_data["dashboard"]["status"]["percentage"],
                "water_volume": raw_data["dashboard"]["status"]["extra"].split()[0],
                "days_remaining": raw_data["dashboard"]["status"]["days_remaining"]
            })
            
            # Settings
            parsed["water_hardness"] = raw_data["settings"]["settings"]["install_hardness"]
            
            # Last regeneration
            if raw_data["regenerations"]:
                parsed["last_regeneration"] = raw_data["regenerations"][0]["datetime"]
                parsed["salt_used"] = raw_data["regenerations"][0]["salt_used"]
            
            # Device info
            parsed["total_volume"] = raw_data["info"]["total_volume"].split()[0]
            parsed["software_version"] = raw_data["info"]["software"]
            
        except KeyError as e:
            logging.error("Missing key in data: %s", str(e))
        
        return parsed
