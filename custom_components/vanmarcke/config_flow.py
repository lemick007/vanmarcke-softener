from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import voluptuous as vol

from .api import ErieAPI
from .const import DOMAIN, CONF_USERNAME, CONF_PASSWORD

class VanmarckeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Flux de configuration Vanmarcke"""
    
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        errors = {}
        

        session = async_get_clientsession(self.hass)
        api = ErieAPI(
            username=user_input[CONF_USERNAME],
            password=user_input[CONF_PASSWORD],
            session=session  # Session correctement passée
        )

        if user_input is not None:
            # Validation des identifiants
            session = async_get_clientsession(self.hass)
            api = ErieAPI(user_input[CONF_USERNAME], user_input[CONF_PASSWORD], session)
            
            try:
                if await api.authenticate():
                    return self.async_create_entry(
                        title=f"Vanmarcke {user_input[CONF_USERNAME]}",
                        data=user_input
                    )
                errors["base"] = "invalid_auth"
            except Exception:
                errors["base"] = "cannot_connect"

        # Schéma de formulaire
        data_schema = vol.Schema({
            vol.Required(CONF_USERNAME): str,
            vol.Required(CONF_PASSWORD): str
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors
        )
