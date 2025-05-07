from typing import Any, Dict
import logging
from .curl_wrapper import async_curl_get, CannotConnect
from datetime import date

MAX_DAILY_CONSUMPTION = 1000  # litres (évite les valeurs aberrentes)
_LOGGER = logging.getLogger(__name__)

class ErieAPI:
    def __init__(self, email: str, password: str, session):
        self._email = email
        self._password = password
        self._session = session  # Utilisé pour le POST d'authentification
        self._auth_headers = {}
        self._device_id = None  # Doit être assigné via la config_flow
        self._base_url = "https://connectmysoftenerapi.pentair.eu/api/erieapp/v1"

    async def authenticate(self) -> bool:
        """Authentifie l'utilisateur et stocke les en-têtes nécessaires."""
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

    async def get_all_devices(self) -> list:
        """Récupère la liste de tous les adoucisseurs disponibles."""
        url = f"{self._base_url}/water_softeners"
        try:
            data = await async_curl_get(url, self._auth_headers)
        except Exception as e:
            _LOGGER.error("Erreur lors de la récupération des appareils via curl: %s", str(e))
            return []
        devices = []
        if isinstance(data, list):
            for item in data:
                if "profile" in item:
                    devices.append({
                        "id": item["profile"]["id"],
                        "name": item["profile"].get("name", "Adoucisseur")
                    })
        return devices

    async def _get_device_id(self) -> str:
        """Retourne l'ID de l'appareil déjà sélectionné dans la configuration."""
        return self._device_id

    async def get_full_data(self) -> Dict[str, Any]:
        """Récupère toutes les données pertinentes de l'adoucisseur en utilisant le wrapper pour GET."""
        device_id = await self._get_device_id()
        if not device_id:
            return {}
        # Définir les endpoints : on inclut désormais "graph" et on se passe de "regenerations"
        today = date.today()
        endpoints = {
            "dashboard": f"water_softeners/{device_id}/dashboard",
            "settings": f"water_softeners/{device_id}/settings",
            "info": f"water_softeners/{device_id}/info",
            "flow": f"water_softeners/{device_id}/flow",
            "graph": f"water_softeners/{device_id}/graphs/day?day={today.day}&month={today.month}&year={today.year}" #set todays date
        }
        data = {}
        for key, endpoint in endpoints.items():
            url = f"{self._base_url}/{endpoint}"
            try:
                data[key] = await async_curl_get(url, self._auth_headers)
            except Exception as e:
                _LOGGER.error("Erreur en récupérant %s: %s", key, str(e))
        return self._parse_data(data)

    def _parse_data(self, raw_data: Dict) -> Dict:
        parsed = {}
        try:
            # Dashboard
            dashboard = raw_data.get("dashboard", {}).get("status", {})
            # Info (contient last_regeneration et nr_regenerations et total_volume)
            info = raw_data.get("info", {})
            # Settings
            settings = raw_data.get("settings", {}).get("settings", {})
            # Flow
            flow = raw_data.get("flow", {})
            # Graph (pour la consommation journalière)
            graph_obj = raw_data.get("graph", {})

            # Calcul de la consommation journalière brute depuis le graph
            if isinstance(graph_obj, dict):
                graph_data = graph_obj.get("graph", [])
            elif isinstance(graph_obj, list):
                graph_data = graph_obj
            else:
                graph_data = []
            daily_raw = sum(int(item.get("y", 0)) for item in graph_data)

            # Récupération du volume total traité pour servir de plafond
            total_vol = 0
            try:
                total_vol = int(info.get("total_volume", "0").split()[0])
            except Exception:
                total_vol = 0

            # Clamp : si négatif ou > MAX_DAILY_CONSUMPTION, on remet à zéro
            if daily_raw < 0 or daily_raw > MAX_DAILY_CONSUMPTION:
                # _LOGGER.warning("Conso journalière aberrante (%s L), remise à 0", daily_raw)
                daily_consumption = 0
            else:
                daily_consumption = daily_raw
            
            parsed.update({
                "salt_level": dashboard.get("percentage"),
                "water_volume": dashboard.get("extra", "0 L").split()[0],
                "days_remaining": dashboard.get("days_remaining"),
                # Utilisation des informations issues de "info"
                "last_regeneration": info.get("last_regeneration"),
                "nr_regenerations": info.get("nr_regenerations"),
                "total_volume": info.get("total_volume", "0 L").split()[0],
                "software_version": info.get("software"),
                "flow": flow.get("flow"),
                "daily_consumption": daily_consumption,
            })
            # Ajout d'une information supplémentaire si nécessaire
        except Exception as e:
            _LOGGER.error("Erreur lors du parsing des données: %s", str(e))
        return parsed
