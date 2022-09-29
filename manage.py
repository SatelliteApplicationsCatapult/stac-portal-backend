import os

from flask_cli import FlaskGroup
from flask_cors import CORS
from flask_migrate import Migrate

from app import blueprint
from app.main import create_app, db

app = create_app(os.getenv('FLASK_ENV') or 'dev')
app.register_blueprint(blueprint)
app.app_context().push()
CORS(app, resources={r"/*": {"origins": "*"}})
cli = FlaskGroup(app)

migrate = Migrate()
migrate.init_app(app, db)
# add the flask migrate command to the manager
# manager.add_command('db', MigrateCommand)
# manager.add_command('db', MigrateCommand)
FLASK_APP = "manage.py"


def run():
    # app.run on 0.0.0.0:5000
    # print current app config mode
    app.run(host='0.0.0.0', port=5000)
    db.create_all()


print("Current app config mode: " + app.config["ENV"])

# def test():
#     """Runs the unit tests."""
#     tests = unittest.TestLoader().discover('app/test', pattern='test*.py')
#     result = unittest.TextTestRunner(verbosity=2).run(tests)
#     if result.wasSuccessful():
#         return 0
#     return 1
if __name__ == '__main__':
    cli()
