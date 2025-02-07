from typing import Any, Dict
import logging
from .curl_wrapper import async_curl_get, CannotConnect

_LOGGER = logging.getLogger(__name__)

class ErieAPI:
    def __init__(self, email: str, password: str, session):
        self._email = email
        self._password = password
        self._session = session  # Ici vous pouvez conserver la session HA pour d'autres appels si nécessaire
        self._auth_headers = {}
        self._device_id = None
        self._base_url = "https://connectmysoftenerapi.pentair.eu/api/erieapp/v1"

    async def authenticate(self) -> bool:
        # Reste inchangé (utilisation d'aiohttp pour le POST d'authentification)
        try:
            async with self._session.post(
                f"{self._base_url}/auth/sign_in",
                json={"email": self._email, "password": self._password}
            ) as response:
                if response.status != 200:
                    _LOGGER.error("Échec de l'authentification: HTTP %s", response.status)
                    return False
                headers = response.headers
                self._auth_headers = {
                    "Access-Token": headers.get("Access-Token", "").strip(),
                    "Client": headers.get("Client", "").strip(),
                    "Uid": headers.get("Uid", "").strip(),
                    "Token-Type": headers.get("Token-Type", "").strip()
                }
                _LOGGER.debug("En-têtes récupérés après l'authentification: %s", self._auth_headers)
                return True
        except Exception as e:
            _LOGGER.error("Erreur lors de l'authentification: %s", str(e))
            return False

    async def _get_device_id(self) -> str:
        """Utilise le wrapper curl pour récupérer l'ID du premier adoucisseur d'eau."""
        if not self._device_id:
            url = f"{self._base_url}/water_softeners"
            _LOGGER.debug("En-têtes envoyés avec curl: %s", headers)
            _LOGGER.debug("En-têtes 2 envoyés avec curl: %s", self._auth_headers)
            try:
                data = await async_curl_get(url, self._auth_headers)
            except Exception as e:
                _LOGGER.error("Erreur lors de la récupération du device_id via curl: %s", str(e))
                return None
            if isinstance(data, list) and data:
                self._device_id = data[0]["profile"]["id"]
            else:
                _LOGGER.warning("Aucun adoucisseur trouvé")
                return None
        return self._device_id

    async def get_full_data(self) -> Dict[str, Any]:
        """Récupère toutes les données pertinentes de l'adoucisseur en utilisant le wrapper pour GET."""
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
            url = f"{self._base_url}/{endpoint}"
            try:
                data[key] = await async_curl_get(url, self._auth_headers)
            except Exception as e:
                _LOGGER.error("Erreur %s en récupérant %s: %s", e, key, str(e))
        return self._parse_data(data)

    def _parse_data(self, raw_data: Dict) -> Dict:
        parsed = {}
        try:
            dashboard = raw_data.get("dashboard", {}).get("status", {})
            info = raw_data.get("info", {})
            settings = raw_data.get("settings", {}).get("settings", {})
            flow = raw_data.get("flow", {})
            parsed.update({
                "salt_level": dashboard.get("percentage"),
                "water_volume": dashboard.get("extra", "0 L").split()[0],
                "days_remaining": dashboard.get("days_remaining")
            })
            parsed["water_hardness"] = settings.get("install_hardness")
            regenerations = raw_data.get("regenerations", [])
            if regenerations:
                parsed["last_regeneration"] = regenerations[0].get("datetime")
            parsed["total_volume"] = info.get("total_volume", "0 L").split()[0]
            parsed["software_version"] = info.get("software")
            parsed["flow"] = flow.get("flow")
        except Exception as e:
            _LOGGER.error("Erreur lors du parsing des données: %s", str(e))
        return parsed
