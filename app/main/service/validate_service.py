from typing import Dict, Any

import requests
from flask import current_app

from ..util.get_ip_from_cird_range import get_ip_from_cird_range

_WORKING_IP = None


def validate_json(data: Dict[str, Any]) -> tuple[str, int]:
    """Validate JSON."""
    # validate_endpoint = route("VALIDATE")
    global _WORKING_IP
    STAC_VALIDATOR_API_CIDR_RANGE = current_app.config["STAC_VALIDATOR_API_CIDR_RANGE"]
    STAC_VALIDATOR_API_PORT = current_app.config["STAC_VALIDATOR_API_PORT"]
    STAC_VALIDATOR_PROTOCOL = current_app.config["STAC_VALIDATOR_PROTOCOL"]

    if _WORKING_IP is None:
        potential_ips = get_ip_from_cird_range(STAC_VALIDATOR_API_CIDR_RANGE)
        for ip in potential_ips:
            print("Trying IP: " + ip)
            try:
                validate_endpoint = f"{STAC_VALIDATOR_PROTOCOL}://{ip}:{STAC_VALIDATOR_API_PORT}/"
                headers = {"Content-Type": "application/json"}
                # if response takes longer than 1 seconds, assume it's not working

                response = requests.post(validate_endpoint,
                                         json=data["json"],
                                         headers=headers,
                                         timeout=1)
                _WORKING_IP = ip
                return response.text, 200
            except requests.exceptions.ConnectionError:
                continue
        _WORKING_IP = None
        return "Could not connect to STAC Validator API.", 500
    else:
        try:
            validate_endpoint = f"{STAC_VALIDATOR_PROTOCOL}://{_WORKING_IP}:{STAC_VALIDATOR_API_PORT}/"
            headers = {"Content-Type": "application/json"}
            # if response takes longer than 1 seconds, assume it's not working

            response = requests.post(validate_endpoint,
                                     json=data["json"],
                                     headers=headers,
                                     timeout=1)
            return response.text, 200
        except requests.exceptions.ConnectionError:
            _WORKING_IP = None
            return validate_json(data)
