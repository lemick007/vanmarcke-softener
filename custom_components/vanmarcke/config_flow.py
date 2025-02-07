import logging
import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

AUTH_URL = "https://connectmysoftenerapi.pentair.eu/api/erieapp/v1/auth/sign_in"
SOFTENERS_URL = "https://connectmysoftenerapi.pentair.eu/api/erieapp/v1/water_softeners"

# Classe personnalisée pour forcer "Token-Type" à "Bearer"
class FixedTokenTypeRequest(aiohttp.ClientRequest):
    def update_headers(self, headers):
        super().update_headers(headers)
        # On force la valeur du header "Token-Type" à "Bearer"
        self.headers["Token-Type"] = "Bearer"

class CannotConnect(HomeAssistantError):
    """Erreur de connexion à l'API."""

class InvalidAuth(HomeAssistantError):
    """Identifiants invalides."""

class NoSoftenerFound(HomeAssistantError):
    """Aucun adoucisseur trouvé pour cet utilisateur."""

async def async_authenticate(hass: HomeAssistant, email: str, password: str):
    """
    Tente de s'authentifier auprès de l'API et récupère l'ID du premier adoucisseur.
    
    Pour la requête POST d'authentification, on utilise la session HA standard.
    Pour la requête GET sur les adoucisseurs, on utilise une session dédiée avec
    une classe de requête personnalisée pour forcer le header "Token-Type".
    """
    # --- Étape 1 : Authentification (POST) ---
    ha_session = async_get_clientsession(hass)
    _LOGGER.debug("Tentative d'authentification pour %s", email)
    try:
        response = await ha_session.post(AUTH_URL, json={"email": email, "password": password})
    except aiohttp.ClientError as err:
        _LOGGER.error("Erreur de connexion lors de l'authentification: %s", err)
        raise CannotConnect from err

    _LOGGER.debug("Réponse d'authentification: %s", response.status)
    if response.status != 200:
        _LOGGER.error("Échec de l'authentification, statut %s", response.status)
        raise InvalidAuth

    # Récupération des en-têtes tels que reçus
    headers = response.headers
    access_token = headers.get("Access-Token")
    client = headers.get("Client")
    uid = headers.get("Uid")
    token_type = headers.get("Token-Type", "Bearer")  # Devrait être "Bearer" dans le test

    if not access_token or not client or not uid or not token_type:
        _LOGGER.error("Les en-têtes d'authentification sont incomplets: %s", headers)
        raise CannotConnect

    _LOGGER.debug("En-têtes reçus: Access-Token=%s, Client=%s, Uid=%s, Token-Type=%s",
                  access_token, client, uid, token_type)

    # Construction du dictionnaire d'en-têtes pour la suite
    # (On souhaite que Token-Type reste "Bearer", mais nous allons la forcer dans la session GET)
    auth_headers = {
        "Access-Token": access_token.strip(),
        "Client": client.strip(),
        "Uid": uid.strip(),
        "Token-Type": token_type.strip(),
    }
    _LOGGER.debug("En-têtes d'authentification envoyés pour POST: %s", auth_headers)

    # --- Étape 2 : Récupération des adoucisseurs (GET) ---
    _LOGGER.debug("Tentative de récupération des adoucisseurs")
    # Utilisation d'une session temporaire avec notre classe FixedTokenTypeRequest
    try:
        async with aiohttp.ClientSession(request_class=FixedTokenTypeRequest) as custom_session:
            response = await custom_session.get(SOFTENERS_URL, headers=auth_headers)
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
