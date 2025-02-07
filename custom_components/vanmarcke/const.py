DOMAIN = "vanmarcke_water"
CONF_EMAIL = "email"
CONF_PASSWORD = "password"

SENSOR_TYPES = {
    # Dashboard
    "salt_level": {"name": "Niveau de sel", "unit": "%", "icon": "mdi:shaker-outline", "device_class": None},
    "water_volume": {"name": "Volume traité", "unit": "L", "icon": "mdi:water", "device_class": None},
    "days_remaining": {"name": "Jours restants", "unit": "jours", "icon": "mdi:calendar-clock", "device_class": None},
    
    # Settings
    "water_hardness": {"name": "Dureté configurée", "unit": "", "icon": "mdi:water-alert", "device_class": None},
    "current_hardness": {"name": "Dureté actuelle", "unit": "", "icon": "mdi:water-check", "device_class": None},
    
    # Regenerations
    "last_regeneration": {"name": "Dernière régénération", "unit": None, "icon": "mdi:calendar-sync", "device_class": "timestamp"},
    "salt_used": {"name": "Sel consommé", "unit": "g", "icon": "mdi:shaker", "device_class": None},
    
    # Info
    "total_volume": {"name": "Volume total", "unit": "L", "icon": "mdi:water", "device_class": None},
    "software_version": {"name": "Version logicielle", "unit": None, "icon": "mdi:chip", "device_class": None},
    
    # Flow
    "current_flow": {"name": "Débit instantané", "unit": "L/min", "icon": "mdi:waves", "device_class": None},
    
    # Maintenance
    "maintenance_due": {"name": "Maintenance requise", "unit": None, "icon": "mdi:wrench-alert", "device_class": None}
}
