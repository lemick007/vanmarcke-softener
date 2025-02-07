import asyncio
import json
import logging
import shlex

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
    # --- Première étape : authentification avec aiohttp (si cela fonctionne) ---
    # Vous pouvez aussi utiliser curl ici si nécessaire, mais supposons que le POST fonctionne bien.
    import aiohttp
    session = aiohttp.ClientSession()
    try:
        async with session.post(AUTH_URL, json={"email": email, "password": password}) as response:
            if response.status != 200:
                _LOGGER.error("Échec de l'authentification, statut %s", response.status)
                raise InvalidAuth
            headers = response.headers
            # Construction des en-têtes comme dans votre test
            auth_headers = {
                "Access-Token": headers.get("Access-Token", "").strip(),
                "Client": headers.get("Client", "").strip(),
                "Uid": headers.get("Uid", "").strip(),
                "Token-Type": headers.get("Token-Type", "Bearer").strip(),
            }
            _LOGGER.debug("En-têtes d'authentification reçus: %s", auth_headers)
    finally:
        await session.close()

    # Optionnel : attendre un court délai
    await asyncio.sleep(0.2)
    
    # --- Deuxième étape : récupération des adoucisseurs en appelant curl en externe ---
    # Construire la commande curl avec les mêmes en-têtes
    # Note : veillez à bien échapper les quotes et à remplacer YOUR_ACCESS_TOKEN, YOUR_CLIENT par les valeurs obtenues.
    curl_command = (
        f'curl -s -X GET "{SOFTENERS_URL}" '
        f'-H "Access-Token: {auth_headers["Access-Token"]}" '
        f'-H "Client: {auth_headers["Client"]}" '
        f'-H "Uid: {auth_headers["Uid"]}" '
        f'-H "Token-Type: {auth_headers["Token-Type"]}"'
    )
    _LOGGER.debug("Commande curl: %s", curl_command)
    # Exécute la commande en mode asynchrone
    process = await asyncio.create_subprocess_shell(
        curl_command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        err_msg = stderr.decode().strip()
        _LOGGER.error("Erreur lors de l'appel curl: %s", err_msg)
        raise CannotConnect(f"curl error: {err_msg}")
    result = stdout.decode().strip()
    _LOGGER.debug("Sortie de curl: %s", result)
    try:
        data = json.loads(result)
    except Exception as err:
        _LOGGER.error("Erreur lors du décodage JSON de curl: %s", err)
        raise CannotConnect from err

    if not data or not isinstance(data, list) or len(data) == 0:
        _LOGGER.error("Aucun adoucisseur trouvé dans les données.")
        raise NoSoftenerFound

    softener_id = data[0]["profile"]["id"]
    _LOGGER.debug("ID de l'adoucisseur récupéré: %s", softener_id)
    return auth_headers, softener_id

class VanmarckeWaterFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Flux de configuration pour l'intégration Vanmarcke Water Softener."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
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
