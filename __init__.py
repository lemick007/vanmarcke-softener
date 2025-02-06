from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    hass.data.setdefault(DOMAIN, {})
    
    try:
        api = ErieConnect(
            entry.data[CONF_EMAIL],
            entry.data[CONF_PASSWORD]
        )
        
        hass.data[DOMAIN][entry.entry_id] = api
        await hass.async_add_executor_job(api.initialize)
        
    except Exception as exc:
        _LOGGER.error("Erreur d'initialisation: %s", exc)
        return False

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )
    
    return True
