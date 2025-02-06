from homeassistant import config_entries
from erie_connect import ErieConnect, AuthenticationException

class VanmarckeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input=None):
        errors = {}
        
        if user_input is not None:
            try:
                api = ErieConnect(
                    user_input[CONF_EMAIL],
                    user_input[CONF_PASSWORD]
                )
                await self.hass.async_add_executor_job(api.authenticate)
                
                return self.async_create_entry(
                    title="Vanmarcke Softener", 
                    data=user_input
                )
                
            except AuthenticationException:
                errors["base"] = "invalid_auth"
            except Exception:  
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_EMAIL): str,
                vol.Required(CONF_PASSWORD): str
            }),
            errors=errors
        )
