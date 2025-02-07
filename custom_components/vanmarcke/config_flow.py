from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import voluptuous as vol

from .api import ErieAPI
from .const import DOMAIN, CONF_EMAIL, CONF_PASSWORD
from .exceptions import CannotConnect, InvalidAuth

class VanmarckeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                session = async_get_clientsession(self.hass)
                api = ErieAPI(
                    email=user_input[CONF_EMAIL],
                    password=user_input[CONF_PASSWORD],
                    session=session
                )
                
                if await api.authenticate():
                    return self.async_create_entry(
                        title=f"Vanmarcke ({user_input[CONF_EMAIL]})", 
                        data=user_input
                    )
                    
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:
                errors["base"] = "unknown"

        data_schema = vol.Schema({
            vol.Required(CONF_EMAIL): str,
            vol.Required(CONF_PASSWORD): str
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors
        )
