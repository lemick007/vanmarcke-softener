# exceptions.py
class CannotConnect(Exception):
    """Impossible de se connecter à l'API Vanmarcke"""

class InvalidAuth(Exception):
    """Identifiants invalides"""
