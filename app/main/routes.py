from flask import current_app


def route(path: str, **kwargs) -> str:
    BASE_STAC_URL = current_app.config["TARGET_STAC_API_SERVER"]
    # STAC_VALIDATOR_API_CIDR_RANGE = current_app.config["STAC_VALIDATOR_API_CIDR_RANGE"]

    return {
        "COLLECTIONS": BASE_STAC_URL + "/collections/",
        # "VALIDATE": STAC_VALIDATOR_API_CIDR_RANGE + "/",
    }[path]
