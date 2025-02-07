import logging
import voluptuous as vol
import aiohttp

from homeassistant import config_entries
from homeassistant.core import HomeAssistant

from .api import ErieAPI
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class CannotConnect(Exception):
    """Erreur de connexion à l'API."""
    pass

class InvalidAuth(Exception):
    """Identifiants invalides."""
    pass

class NoSoftenerFound(Exception):
    """Aucun adoucisseur trouvé pour cet utilisateur."""
    pass

class VanmarckeWaterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Flux de configuration pour l'intégration Vanmarcke Water Softener."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            email = user_input.get("email")
            password = user_input.get("password")
            session = aiohttp.ClientSession()
            api = ErieAPI(email, password, session)
            if not await api.authenticate():
                errors["base"] = "invalid_auth"
                await session.close()
                return self.async_show_form(
                    step_id="user",
                    data_schema=vol.Schema({
                        vol.Required("email"): str,
                        vol.Required("password"): str,
                    }),
                    errors=errors
                )
            devices = await api.get_all_devices()
            await session.close()
            if not devices:
                errors["base"] = "no_softener"
                return self.async_show_form(
                    step_id="user",
                    data_schema=vol.Schema({
                        vol.Required("email"): str,
                        vol.Required("password"): str,
                    }),
                    errors=errors
                )
            if len(devices) == 1:
                device_id = devices[0]["id"]
                data = {
                    "email": email,
                    "password": password,
                    "device_id": device_id,
                }
                return self.async_create_entry(title=f"Adoucisseur {device_id}", data=data)
            else:
                self.context["devices"] = devices
                self.context["email"] = email
                self.context["password"] = password
                return await self.async_step_select_device()
        schema = vol.Schema({
            vol.Required("email"): str,
            vol.Required("password"): str,
        })
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_select_device(self, user_input=None):
        devices = self.context["devices"]
        email = self.context["email"]
        password = self.context["password"]
        device_options = {device["id"]: f'{device.get("name", "Adoucisseur")} ({device["id"]})' for device in devices}
        schema = vol.Schema({
            vol.Required("device_id"): vol.In(device_options)
        })
        if user_input is not None:
            selected_device = user_input["device_id"]
            data = {
                "email": email,
                "password": password,
                "device_id": selected_device,
            }
            return self.async_create_entry(title=f"Adoucisseur {selected_device}", data=data)
        return self.async_show_form(step_id="select_device", data_schema=schema)
