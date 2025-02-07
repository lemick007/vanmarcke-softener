import logging
import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN  # Assure-toi d'avoir un fichier const.py avec DOMAIN défini

_LOGGER = logging.getLogger(__name__)

AUTH_URL = "https://connectmysoftenerapi.pentair.eu/api/erieapp/v1/auth/sign_in"
SOFTENERS_URL = "https://connectmysoftenerapi.pentair.eu/api/erieapp/v1/water_softeners"


async def async_authenticate(hass: HomeAssistant, email: str, password: str):
    """Tente de s'authentifier et de récupérer l'ID de l'adoucisseur."""
    async with aiohttp.ClientSession() as session:
        async with session.post(AUTH_URL, json={"email": email, "password": password}) as response:
            if response.status != 200:
                _LOGGER.error("Échec de l'authentification. Vérifie tes identifiants.")
                raise InvalidAuth

            headers = response.headers
            auth_headers = {
                "Access-Token": headers.get("Access-Token"),
                "Client": headers.get("Client"),
                "Uid": headers.get("Uid"),
                "Token-Type": headers.get("Token-Type"),
            }

        async with session.get(SOFTENERS_URL, headers=auth_headers) as response:
            if response.status != 200:
                _LOGGER.error("Impossible de récupérer les adoucisseurs.")
                raise CannotConnect

            data = await response.json()
            if not data or not isinstance(data, list) or len(data) == 0:
                _LOGGER.error("Aucun adoucisseur trouvé pour cet utilisateur.")
                raise NoSoftenerFound

            softener_id = data[0]["profile"]["id"]
            return auth_headers, softener_id


class VanmarckeWaterFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Gère le flux de configuration pour Vanmarcke Water Softener."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Gère le formulaire de configuration."""
        errors = {}

        if user_input is not None:
            email = user_input["email"]
            password = user_input["password"]

            try:
                auth_headers, softener_id = await async_authenticate(self.hass, email, password)

                return self.async_create_entry(
                    title=f"Adoucisseur {softener_id}",
                    data={
                        "email": email,
                        "auth_headers": auth_headers,
                        "softener_id": softener_id,
                    },
                )

            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except NoSoftenerFound:
                errors["base"] = "no_softener"

        schema = vol.Schema(
            {
                vol.Required("email"): str,
                vol.Required("password"): str,
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)


class CannotConnect(HomeAssistantError):
    """Erreur de connexion à l'API."""


class InvalidAuth(HomeAssistantError):
    """Erreur d'authentification."""


class NoSoftenerFound(HomeAssistantError):
    """Aucun adoucisseur trouvé."""
