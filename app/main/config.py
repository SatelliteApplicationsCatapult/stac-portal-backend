import os

# uncomment the line below for postgres database url from environment variable
# postgres_local_base = os.environ['DATABASE_URL']

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    # here are global variables available for all environments
    SECRET_KEY = os.getenv('SECRET_KEY', 'my_precious_secret_key')
    DEBUG = False
    # Swagger
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    RESTX_MASK_SWAGGER = False
    STAC_SELECTIVE_INGESTER_PORT = os.getenv('STAC_SELECTIVE_INGESTER_PORT', 80)
    STAC_SELECTIVE_INGESTER_PROTOCOL = os.getenv('STAC_SELECTIVE_INGESTER_PROTOCOL', "http")
    AZURE_STORAGE_BLOB_NAME_FOR_STAC_ITEMS = os.getenv('AZURE_STORAGE_BLOB_NAME_FOR_STAC_ITEMS', "stac-items")
    STAC_VALIDATOR_API_PORT = os.getenv('STAC_VALIDATOR_API_PORT', 80)
    STAC_VALIDATOR_PROTOCOL = os.getenv('STAC_VALIDATOR_PROTOCOL', "http")


class DevelopmentConfig(Config):
    # here are variables available only for development environment
    DEBUG = True
    ENV = "Dev"
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(
        basedir, 'flask_boilerplate_main.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    STAC_VALIDATOR_API_CIDR_RANGE = os.getenv('STAC_VALIDATOR_API_CIDR_RANGE', "172.17.0.1/32")
    STAC_VALIDATOR_API_PORT = os.getenv('STAC_VALIDATOR_API_PORT', 9000)
    STAC_VALIDATOR_PROTOCOL = os.getenv('STAC_VALIDATOR_PROTOCOL', "http")
    
    TARGET_STAC_API_SERVER = os.getenv('TARGET_STAC_API_SERVER', "https://stac-api-server.azurewebsites.net")
    STAC_SELECTIVE_INGESTER_CIDR_RANGE = os.getenv('STAC_SELECTIVE_INGESTER_CIDR_RANGE', "172.17.0.1/32")
    STAC_SELECTIVE_INGESTER_CALLBACK_ENDPOINT = os.getenv("STAC_SELECTIVE_INGESTER_CALLBACK_ENDPOINT",
                                                          "http://172.17.0.1:5000/status_reporting/loading_public_stac_records")
    STAC_SELECTIVE_INGESTER_PORT = os.getenv('STAC_SELECTIVE_INGESTER_PORT', 9001)
    STAC_SELECTIVE_INGESTER_PROTOCOL = os.getenv('STAC_SELECTIVE_INGESTER_PROTOCOL', "http")
    AZURE_STORAGE_CONNECTION_STRING = os.getenv('AZURE_STORAGE_CONNECTION_STRING', "")


class StagingConfig(Config):
    DEBUG = False
    ENV = "Staging"
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres")
    print("SQLALCHEMY_DATABASE_URI: ", SQLALCHEMY_DATABASE_URI)
    STAC_VALIDATOR_API_CIDR_RANGE = os.getenv('STAC_VALIDATOR_API_CIDR_RANGE', '')
    STAC_SELECTIVE_INGESTER_CIDR_RANGE = os.getenv('STAC_SELECTIVE_INGESTER_CIDR_RANGE', "")
    TARGET_STAC_API_SERVER = os.getenv('TARGET_STAC_API_SERVER', "")
    STAC_SELECTIVE_INGESTER_CALLBACK_ENDPOINT = os.getenv("STAC_SELECTIVE_INGESTER_CALLBACK_ENDPOINT", "")
    AZURE_STORAGE_CONNECTION_STRING = os.getenv('AZURE_STORAGE_CONNECTION_STRING', "")
    THIS_APP_FQDN = os.getenv('THIS_APP_FQDN', "")
    STAC_SELECTIVE_INGESTER_CALLBACK_ENDPOINT = THIS_APP_FQDN + "/status_reporting/loading_public_stac_records"



class ProductionConfig(Config):
    DEBUG = False
    ENV = "Production"
    # uncomment the line below to use postgres
    # SQLALCHEMY_DATABASE_URI = postgres_local_base


config_by_name = dict(
    dev=DevelopmentConfig,
    development=DevelopmentConfig,
    staging=StagingConfig,
    prod=ProductionConfig,
    production=ProductionConfig)

key = Config.SECRET_KEY
