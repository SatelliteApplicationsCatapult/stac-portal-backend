from typing import Dict, Any

import requests
from flask import current_app

from ..util.get_ip_from_cird_range import get_ip_from_cird_range


def validate_json(data: Dict[str, Any]) -> tuple[str, int]:
    """Validate JSON."""

    STAC_VALIDATOR_API_PORT = current_app.config["STAC_VALIDATOR_API_PORT"]
    STAC_VALIDATOR_ENDPOINT = current_app.config["STAC_VALIDATOR_ENDPOINT"]

    try:
        validate_endpoint = f"{STAC_VALIDATOR_ENDPOINT}:{STAC_VALIDATOR_API_PORT}"
        response = requests.post(
            validate_endpoint, json=data, timeout=0)
        return response.text, response.status_code
    except requests.exceptions.RequestException as e:
        return str(e), 500