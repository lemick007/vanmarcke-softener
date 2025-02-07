import logging
import aiohttp
import voluptuous as vol

from homeassistant.util.dt import utcnow
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_create_clientsession
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
    """
    Tente de s'authentifier auprès de l'API et récupère l'ID du premier adoucisseur.
    
    Ce code reprend la logique de ton script test, mais **n'envoie pas le header "Token-Type"** lors de la requête GET.
    """
    session = async_create_clientsession(hass)


    _LOGGER.debug("Tentative d'authentification pour %s", email)
    try:
        response = await session.post(AUTH_URL, json={"email": email, "password": password})
    except aiohttp.ClientError as err:
        _LOGGER.error("Erreur de connexion lors de l'authentification: %s", err)
        raise CannotConnect from err

    _LOGGER.debug("Réponse d'authentification: %s", response.status)
    if response.status != 200:
        _LOGGER.error("Échec de l'authentification, statut %s", response.status)
        raise InvalidAuth
    
    # Récupération des en-têtes tels que reçus dans le script test
    headers = response.headers
    access_token = headers.get("Access-Token")
    client = headers.get("Client")
    uid = headers.get("Uid")
    token_type = headers.get("Token-Type", "Bearer")
    server_time = int(headers.get("Server-Time", headers.get("Server time", "0")))
    if server_time == 0:
        _LOGGER.error("Server-Time non reçu dans les headers... blocage : %s", headers)
        raise CannotConnect

    if not access_token or not client or not uid or not token_type:
        _LOGGER.error("Les en-têtes d'authentification sont incomplets: %s", headers)
        raise CannotConnect

    _LOGGER.debug("En-têtes reçus: Access-Token=%s, Client=%s, Uid=%s, Token-Type=%s",
                  access_token, client, uid, token_type)
    auth_headers = {
        "Access-Token": headers.get("Access-Token", "").strip(),
        "Client": headers.get("Client", "").strip(),
        "Uid": headers.get("Uid", "").strip(),
        "Token-Type": headers.get("Token-Type", "Bearer").strip(),
        "Server-Time": str(server_time),  # Header critique manquant
        "Client-Time": str(int(utcnow().timestamp()))
    }
    _LOGGER.debug("En-têtes : %s", auth_headers)

    server_time = int(response.headers.get("Server-Time", "0"))
    if server_time == 0:
        raise ValueError("Server-Time manquant dans les headers")

    client_time = int(utcnow().timestamp())
    if abs(client_time - server_time) > 300:  # 5 min de marge
        _LOGGER.error("Désynchronisation temporelle serveur/client: %s vs %s", 
                    server_time, client_time)
        raise CannotConnect

    _LOGGER.debug("Tentative de récupération des adoucisseurs")
    try:
        response = await session.get(SOFTENERS_URL, headers=auth_headers)
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
                errors["base"] = "invalid_auth"
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except NoSoftenerFound:
                errors["base"] = "no_softener"
            except Exception as err:
                _LOGGER.exception("Erreur inattendue: %s", err)
                errors["base"] = "unknown"

        schema = vol.Schema({
            vol.Required("email"): str,
            vol.Required("password"): str,
        })

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
