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
        """Authentifie l'utilisateur et stocke les en-têtes nécessaires."""
        try:
            async with self._session.post(
                f"{self._base_url}/auth/sign_in",
                json={"email": self._email, "password": self._password}
            ) as response:
                if response.status != 200:
                    _LOGGER.error(f"Échec de l'authentification: HTTP {response.status}")
                    return False
                
                headers = response.headers
                self._auth_headers = {
                    "Access-Token": headers.get("Access-Token"),
                    "Client": headers.get("Client"),
                    "Uid": headers.get("Uid"),
                    "Token-Type": headers.get("Token-Type")
                }
                return True

        except aiohttp.ClientError as e:
            _LOGGER.error("Erreur réseau lors de l'authentification: %s", str(e))
            return False
        except KeyError as e:
            _LOGGER.error("En-tête manquant lors de l'authentification: %s", str(e))
            return False

    async def _get_device_id(self) -> str:
        """Récupère l'ID du premier adoucisseur d'eau."""
        if not self._device_id:
            _LOGGER.error("Tentative de récupération ID adoucisseur. Headers : %s",json.dumps(self._auth_headers, default=str))
            try:
                async with self._session.get(
                    f"{self._base_url}/water_softeners",
                    headers=self._auth_headers
                ) as response:
                    if response.status != 200:
                        _LOGGER.error("Échec de récupération du device_id: HTTP %s", response.status)
                        return None
                    
                    data = await response.json()
                    if isinstance(data, list) and data:
                        self._device_id = data[0]["profile"]["id"]
                    else:
                        _LOGGER.warning("Aucun adoucisseur trouvé")
                        return None
            except Exception as e:
                _LOGGER.error("Erreur lors de la récupération du device_id: %s", str(e))
                return None
        
        return self._device_id

    async def get_full_data(self) -> Dict[str, Any]:
        """Récupère toutes les données pertinentes de l'adoucisseur."""
        device_id = await self._get_device_id()
        if not device_id:
            return {}

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
                async with self._session.get(
                    f"{self._base_url}/{endpoint}",
                    headers=self._auth_headers
                ) as response:
                    if response.status == 200:
                        data[key] = await response.json()
                    else:
                        _LOGGER.error(f"Erreur {response.status} en récupérant {key}")
            except Exception as e:
                _LOGGER.error("Erreur en récupérant %s: %s", key, str(e))
        
        return self._parse_data(data)

    def _parse_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transforme les données brutes en données exploitables."""
        if not data:
            return {}

        try:
            dashboard = data.get("dashboard", {})
            info = data.get("info", {})
            settings = data.get("settings", {})
            flow = data.get("flow", {})

            return {
                "salt_level": dashboard.get("status", {}).get("percentage"),
                "water_volume": dashboard.get("status", {}).get("extra"),
                "days_remaining": dashboard.get("status", {}).get("days_remaining"),
                "last_regeneration": info.get("last_regeneration"),
                "total_volume": info.get("total_volume"),
                "software_version": info.get("software"),
                "flow": flow.get("flow")
            }
        except Exception as e:
            _LOGGER.error("Erreur lors du parsing des données: %s", str(e))
            return {}
