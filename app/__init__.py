from flask_restx import Api
from flask import Blueprint

from .main.controller.user_controller import api as user_ns
from .main.controller.auth_controller import api as auth_ns
from .main.controller.collection_controller import api as collection_ns
from .main.controller.validate_controller import api as validate_ns
from .main.controller.public_catalogs_contoller import api as public_catalogs_ns
from .main.controller.status_reporting_controller import api as status_controller_ns
from .main.controller.file_controller import api as file_ns

blueprint = Blueprint('api', __name__)
authorizations = {
    'apikey': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization'
    }
}

api = Api(blueprint,
          title='STAC Portal',
          version='1.0',
          description='Portal for accessing STAC PDA resources',
          authorizations=authorizations,
          security='apikey')

api.add_namespace(user_ns, path='/user')
api.add_namespace(auth_ns)
api.add_namespace(collection_ns, path='/collections')
api.add_namespace(validate_ns, path='/validate')
api.add_namespace(public_catalogs_ns, path='/public_catalogs')
api.add_namespace(status_controller_ns, path='/status_reporting')
api.add_namespace(file_ns, path='/file')
