import logging
import aiohttp
import asyncio
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

AUTH_URL = "https://connectmysoftenerapi.pentair.eu/api/erieapp/v1/auth/sign_in"
SOFTENERS_URL = "https://connectmysoftenerapi.pentair.eu/api/erieapp/v1/water_softeners"

class CannotConnect(HomeAssistantError):
    """Erreur de connexion à l'API."""

class InvalidAuth(HomeAssistantError):
    """Identifiants invalides."""

class NoSoftenerFound(HomeAssistantError):
    """Aucun adoucisseur trouvé pour cet utilisateur."""

async def async_authenticate(hass: HomeAssistant, email: str, password: str):
    _LOGGER.debug("Tentative d'authentification pour %s", email)
    # --- Première session pour l'authentification (POST) ---
    async with aiohttp.ClientSession() as auth_session:
        try:
            response = await auth_session.post(AUTH_URL, json={"email": email, "password": password})
        except aiohttp.ClientError as err:
            _LOGGER.error("Erreur de connexion lors de l'authentification: %s", err)
            raise CannotConnect from err

        _LOGGER.debug("Réponse d'authentification: %s", response.status)
        _LOGGER.debug("Réponse d'authentification headers: %s", response.headers)
        _LOGGER.debug("Réponse d'authentification body: %s", response.body)
        if response.status != 200:
            _LOGGER.error("Échec de l'authentification, statut %s", response.status)
            raise InvalidAuth

        headers = response.headers
        auth_headers = {
            "Access-Token": headers.get("Access-Token", ""),
            "Client": headers.get("Client", ""),
            "Uid": headers.get("Uid", ""),
            "Token-Type": headers.get("Token-Type", "Bearer"),
        }

    # -- Nouvelle session pour la requête GET --
    await asyncio.sleep(2)
    _LOGGER.debug("Création d'une nouvelle session pour récupérer les adoucisseurs")
    async with aiohttp.ClientSession() as get_session:
        try:
            _LOGGER.debug("En-têtes d'authentification: %s", auth_headers)
            response = await get_session.get(SOFTENERS_URL, headers=auth_headers)
            _LOGGER.debug("resp: %s", response)
        except aiohttp.ClientError as err:
            _LOGGER.error("Erreur lors de la récupération des adoucisseurs: %s", err)
            raise CannotConnect from err

        _LOGGER.debug("Réponse GET water_softeners: %s", response.status)
        if response.status != 200:
            text = await response.text()
            _LOGGER.error("Impossible de récupérer les adoucisseurs, statut %s", response.status)
            _LOGGER.debug("Réponse du serveur: %s", text)
            raise CannotConnect

        try:
            data = await response.json()
        except Exception as err:
            _LOGGER.error("Erreur lors du décodage de la réponse JSON: %s", err)
            raise CannotConnect from err

        _LOGGER.debug("Données reçues: %s", data)
        if not data or not isinstance(data, list) or len(data) == 0:
            _LOGGER.error("Aucun adoucisseur trouvé pour cet utilisateur.")
            raise NoSoftenerFound

        softener_id = data[0]["profile"]["id"]
        _LOGGER.debug("ID de l'adoucisseur récupéré: %s", softener_id)
        return auth_headers, softener_id

class VanmarckeWaterFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Flux de configuration pour l'intégration Vanmarcke Water Softener."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Gère le formulaire de configuration présenté à l'utilisateur."""
        errors = {}

        if user_input is not None:
            email = user_input.get("email")
            password = user_input.get("password")

            try:
                auth_headers, softener_id = await async_authenticate(self.hass, email, password)
                return self.async_create_entry(
                    title=f"Adoucisseur {softener_id}",
                    data={
                        "email": email,
                        "password": password,
                        "auth_headers": dict(auth_headers),
                        "softener_id": softener_id,
                    },
                )
            except InvalidAuth:
                errors["base"] = "Invalid credentials or Auth!"
            except CannotConnect:
                errors["base"] = "Unable to connect!"
            except NoSoftenerFound:
                errors["base"] = "No softener found on your account!"
            except Exception as err:
                _LOGGER.exception("Erreur inattendue: %s", err)
                errors["base"] = "Unknown Error..."

        schema = vol.Schema({
            vol.Required("email"): str,
            vol.Required("password"): str,
        })

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
