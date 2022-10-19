from typing import Dict, Any

import requests
from flask import current_app


def validate_json(data: Dict[str, Any]) -> tuple[str, int]:
    """Validate JSON."""

    STAC_VALIDATOR_ENDPOINT = current_app.config["STAC_VALIDATOR_ENDPOINT"]

    try:
        validate_endpoint = f"{STAC_VALIDATOR_ENDPOINT}"
        response = requests.post(
            validate_endpoint, json=data, timeout=120)
        return response.json(), response.status_code
    except requests.exceptions.RequestException as e:
        print("Error: " + str(e))
        return str(e), 500
