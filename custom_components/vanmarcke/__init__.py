from __future__ import annotations
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ErieAPI
from .const import DOMAIN
from .coordinator import VanmarckeWaterCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Configure l'intégration à partir d'une entrée de configuration."""
    session = async_get_clientsession(hass)
    api = ErieAPI(
        email=entry.data["email"],
        password=entry.data["password"],
        session=session,
    )
    # Assigner le device_id choisi par l'utilisateur (lors de la config_flow)
    api._device_id = entry.data["device_id"]

    coordinator = VanmarckeWaterCoordinator(hass, api)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Forward the sensor platforms (await added)
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Désinstalle l'intégration et ses plateformes."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor"])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
