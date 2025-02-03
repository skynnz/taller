import os
from flask import Flask, g, session
from .config.config import get_db

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
    from . import prestamos
    from . import caja
    from . import alta_usuarios
    from . import informes
    #url
    app.register_blueprint(auth.bp)
    app.register_blueprint(dash.bp)
    app.register_blueprint(pass_recover.bp)
    app.register_blueprint(alta_libros.bp)
    app.register_blueprint(prestamos.bp)
    app.register_blueprint(caja.bp)
    app.register_blueprint(alta_usuarios.bp)
    app.register_blueprint(informes.bp)


    @app.before_request
    def load_rutas():
        if 'user_id' in session:
            g.rutas = obtener_rutas_por_rol(g.user['gru_cod'])
        else:
            g.rutas = []

    return app

def obtener_rutas_por_rol(gru_cod):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute('''
            SELECT c.mod_nombre AS titulo, b.pag_nombre AS subtitulo, b.pag_direc AS url
            FROM permisos a
            JOIN paginas b ON b.pag_cod = a.pag_cod
            JOIN modulos c ON c.mod_cod = b.mod_cod
            WHERE a.gru_cod = %s
            ORDER BY c.mod_cod, b.pag_cod;
        ''', (gru_cod,))
        return cursor.fetchall()