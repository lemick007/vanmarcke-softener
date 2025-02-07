DOMAIN = "vanmarcke_water"
CONF_EMAIL = "email"
CONF_PASSWORD = "password"

SENSOR_TYPES = {
    "salt_level": {"name": "Niveau de sel", "unit": "%", "icon": "mdi:shaker"},
    "water_volume": {"name": "Volume traité", "unit": "L", "icon": "mdi:water"},
    "days_remaining": {"name": "Jours restants", "unit": "jours", "icon": "mdi:calendar"},
    "water_hardness": {"name": "Dureté configurée", "unit": "°fH", "icon": "mdi:water-alert"},
    "last_regeneration": {"name": "Dernière régénération", "unit": None, "icon": "mdi:calendar-sync"},
    "total_volume": {"name": "Volume total", "unit": "L", "icon": "mdi:chart-bar"},
    "software_version": {"name": "Version logicielle", "unit": None, "icon": "mdi:chip"}
}
