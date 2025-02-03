from flask import Blueprint, render_template, g
from .auth import login_required
from .config.config import get_db

bp = Blueprint('dash', __name__, url_prefix='/dash')


def obtener_rutas_por_rol(gru_cod):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute('''
            SELECT a.pag_cod,
    b.pag_direc,
    b.pag_nombre,
    b.mod_cod,
    c.mod_nombre,
    a.gru_cod,
    d.gru_nombre,
    a.leer,
    a.insertar,
    a.editar,
    a.borrar
   FROM permisos a
     JOIN paginas b ON b.pag_cod = a.pag_cod
     JOIN modulos c ON c.mod_cod = b.mod_cod
     JOIN grupos d ON d.gru_cod = a.gru_cod
     where d.gru_cod = %s
        ''', (gru_cod,))
        return cursor.fetchall()

@bp.route('/')
@login_required
def index():
    rutas = obtener_rutas_por_rol(g.user['gru_cod'])
    return render_template('dashboard.html', rutas=rutas)