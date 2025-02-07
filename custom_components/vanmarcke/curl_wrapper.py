import asyncio
import json
import logging
from typing import Dict, Any

_LOGGER = logging.getLogger(__name__)

class CannotConnect(Exception):
    """Exception levée en cas d'échec de la connexion via curl."""
    pass

async def async_curl_get(url: str, headers: Dict[str, str]) -> Any:
    """
    Effectue une requête GET via la commande curl, en passant exactement les headers spécifiés.
    Retourne les données décodées en JSON.
    """
    # Vérifie que tous les headers nécessaires sont présents
    required_headers = ["Access-Token", "Client", "Uid", "Token-Type"]
    missing_headers = [h for h in required_headers if h not in headers or not headers[h]]
    if missing_headers:
        _LOGGER.error("En-têtes d'authentification manquants: %s", missing_headers)
        raise CannotConnect(f"En-têtes manquants: {missing_headers}")

    # Construit la chaîne des headers pour curl
    header_str = " ".join([f'-H "{k}: {v}"' for k, v in headers.items()])
    cmd = f'curl -s -X GET "{url}" {header_str}'
    
    _LOGGER.debug("Exécution de la commande curl: %s", cmd)
    
    process = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    
    if process.returncode != 0:
        err_msg = stderr.decode().strip()
        _LOGGER.error("Erreur lors de l'exécution de curl: %s", err_msg)
        raise CannotConnect(f"Erreur curl: {err_msg}")

    output = stdout.decode().strip()
    
    if not output:
        _LOGGER.error("Réponse vide reçue de l'API")
        raise CannotConnect("Réponse vide reçue de l'API")

    _LOGGER.debug("Sortie de curl: %s", output)

    try:
        data = json.loads(output)
    except json.JSONDecodeError as exc:
        _LOGGER.error("Erreur lors du parsing JSON: %s", exc)
        raise CannotConnect(f"Erreur JSON: {exc}") from exc

    return data
