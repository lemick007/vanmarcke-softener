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
    def __init__(self, username: str, password: str, session: aiohttp.ClientSession):
        self._username = username
        self._password = password
        self._auth = None
        self._device_id = None
        self._base_url = "https://connectmysoftenerapi.pentair.eu/api/erieapp/v1"
        self._session = session  # Utilise la session fournie au lieu d'en créer une nouvelle

    async def authenticate(self):
        url = f"{self._base_url}/auth/sign_in"
        data = {"email": self._username, "password": self._password}

        try:
            async with async_timeout.timeout(10):
                async with self._session.post(url, json=data) as response:
                    body = await response.json()
                    headers = response.headers

                    if response.status == 200:
                        self._auth = {
                            "Access-Token": headers.get("Access-Token"),
                            "Client": headers.get("Client"),
                            "Uid": headers.get("Uid"),  
                            "Token-Type": headers.get("Token-Type"),
                        }

                        if not self._auth["Uid"]:
                            _LOGGER.error("Erreur: 'Uid' non trouvé dans les headers !")
                            raise KeyError("Uid manquant")

                        return True

                    elif response.status == 401:
                        raise InvalidAuth("Invalid credentials")
                    else:
                        raise CannotConnect(f"HTTP error {response.status}")

        except aiohttp.ClientError as e:
            raise CannotConnect(f"Connection error: {e}")

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
        """Ne plus fermer la session ici car gérée par HA"""
        pass  # Retirer le await self._session.close()
