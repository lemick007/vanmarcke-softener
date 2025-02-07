from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import voluptuous as vol
from .api import ErieAPI
from .const import DOMAIN, CONF_USERNAME, CONF_PASSWORD
from .exceptions import CannotConnect, InvalidAuth

class VanmarckeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        errors = {}

        # Définir le schéma en dehors de la condition
        data_schema = vol.Schema({
            vol.Required(CONF_USERNAME): str,
            vol.Required(CONF_PASSWORD): str
        })

        if user_input is not None:
            session = async_get_clientsession(self.hass)
            api = ErieAPI(
                username=user_input[CONF_USERNAME],
                password=user_input[CONF_PASSWORD],
                session=session
            )
            try:
                if await api.authenticate():
                    return self.async_create_entry(
                        title=f"Vanmarcke ({user_input[CONF_USERNAME]})",
                        data=user_input
                    )
                errors["base"] = "invalid_auth"
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception as e:
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors
        )
