# const.py
DOMAIN = "vanmarcke_water"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"

SENSOR_MAP = {
    "salt_level": {
        "name": "Niveau de sel", 
        "unit": "%",
        "icon": "mdi:shaker-outline"
    },
    "water_hardness": {
        "name": "Dureté de l'eau",
        "unit": "°fH",
        "icon": "mdi:water"
    },
    "water_flow": {
        "name": "Débit d'eau",
        "unit": "L/min",
        "icon": "mdi:hydraulic-oil-flow"
    }
}
