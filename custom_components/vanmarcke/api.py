# api.py - Client API réécrit en asyncio
import aiohttp
import async_timeout
from typing import Optional, Dict, Any
import logging

_LOGGER = logging.getLogger(__name__)

class ErieAPIError(Exception):
    """Exception générique pour les erreurs API"""

class ErieAuthError(ErieAPIError):
    """Erreur d'authentification"""

class ErieAPI:
    def __init__(self, username: str, password: str):
        self._username = username
        self._password = password
        self._auth: Optional[Dict[str, str]] = None
        self._device_id: Optional[int] = None
        self._base_url = "https://connectmysoftenerapi.pentair.eu/api/erieapp/v1"
        self._session = aiohttp.ClientSession()

    async def authenticate(self) -> bool:
        """Authentification asynchrone"""
        try:
            async with async_timeout.timeout(10):
                response = await self._session.post(
                    f"{self._base_url}/auth/sign_in",
                    json={"email": self._username, "password": self._password},
                    headers={
                        "User-Agent": "HomeAssistant/2025.1",
                        "Accept": "application/json"
                    }
                )
                
                if response.status == 200:
                    self._auth = {
                        "Client": response.headers.get("Client"),
                        "Access-Token": response.headers.get("Access-Token"),
                        "uid": response.headers.get("uid")
                    }
                    return True
                
                raise ErieAuthError(f"Erreur {response.status}: {await response.text()}")
        
        except Exception as e:
            raise ErieAuthError(str(e))

    async def get_devices(self) -> list:
        """Récupération des appareils"""
        await self._ensure_auth()
        
        try:
            async with async_timeout.timeout(10):
                response = await self._session.get(
                    f"{self._base_url}/water_softeners",
                    headers=self._auth_headers
                )
                return await self._handle_response(response)
        
        except Exception as e:
            raise ErieAPIError(f"Erreur devices: {str(e)}")

    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Données du tableau de bord"""
        await self._ensure_device()
        
        try:
            async with async_timeout.timeout(10):
                response = await self._session.get(
                    f"{self._base_url}/water_softeners/{self._device_id}/dashboard",
                    headers=self._auth_headers
                )
                return await self._handle_response(response)
        
        except Exception as e:
            raise ErieAPIError(f"Erreur dashboard: {str(e)}")

    @property
    def _auth_headers(self) -> Dict[str, str]:
        """En-têtes d'authentification"""
        if not self._auth:
            return {}
            
        return {
            "Client": self._auth["Client"],
            "Access-Token": self._auth["Access-Token"],
            "uid": self._auth["uid"]
        }

    async def _ensure_auth(self):
        """Vérification de l'authentification"""
        if not self._auth and not await self.authenticate():
            raise ErieAuthError("Échec de l'authentification")

    async def _ensure_device(self):
        """Sélection automatique du premier appareil"""
        if not self._device_id:
            devices = await self.get_devices()
            if devices:
                self._device_id = devices[0]['profile']['id']
            else:
                raise ErieAPIError("Aucun appareil trouvé")

    @staticmethod
    async def _handle_response(response) -> Any:
        """Gestion centralisée des réponses"""
        if response.status != 200:
            raise ErieAPIError(f"Erreur HTTP {response.status}")
            
        try:
            return await response.json()
        except aiohttp.ContentTypeError:
            raise ErieAPIError("Réponse JSON invalide")

    async def close(self):
        """Fermeture propre de la session"""
        await self._session.close()
