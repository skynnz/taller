import os

from flask import Flask

from app.auth import login_required


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, static_url_path='/static', static_folder='static')
    app.config.from_mapping(
        SECRET_KEY='dev',
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path, exist_ok=True)  # Updated to include exist_ok=True to prevent raising an error if the directory already exists
    except OSError:
        pass

    #imports bps

    from . import auth
    from . import dash
    from . import pass_recover
    from . import alta_libros
    #url
    app.register_blueprint(auth.bp)
    app.register_blueprint(dash.bp)
    app.register_blueprint(pass_recover.bp)
    app.register_blueprint(alta_libros.bp)
    
    return app