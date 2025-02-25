from flask import Blueprint, redirect, render_template, request, flash, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from .config.config import get_db

bp = Blueprint('pss-recover', __name__, url_prefix='/pss-recover')

@bp.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form['username']
        action = request.form['action']
        db = get_db()

        if action == 'recover_password':
            with db.cursor() as cursor:
                cursor.execute(
                    'SELECT * FROM usuarios WHERE username = %s', (username,)
                )
                user = cursor.fetchone()

            if user is None:
                flash('El usuario no existe.', 'error')  # Mensaje de error
                return render_template('auth/pass-recover.html')

            # Obtener preguntas de seguridad del usuario
            with db.cursor() as cursor:
                cursor.execute(
                    'SELECT pregunta FROM preguntas_seguridad WHERE user_id = %s', (user['id'],)
                )
                preguntas = cursor.fetchall()

            return render_template('auth/pass-recover.html', preguntas=preguntas, username=username)

        elif action == 'validate_answers':
            # Lógica para validar las respuestas
            return validate_answers(username)

    return render_template('auth/pass-recover.html')

@bp.route('/validate_answers', methods=['POST'])
def validate_answers(username):
    username = request.form['username']
    db = get_db()

    with db.cursor() as cursor:
        cursor.execute(
            'SELECT id FROM usuarios WHERE username = %s', (username,)
        )
        user = cursor.fetchone()

        if user is None:
            flash('El usuario no existe.', 'error')
            return redirect(url_for('index'))

        user_id = user['id']
        respuestas_correctas = True

        for index in range(1, len(request.form) - 1):
            respuesta_usuario = request.form[f'respuesta_{index}']
            cursor.execute(
                'SELECT respuesta FROM preguntas_seguridad WHERE user_id = %s AND id = %s',
                (user_id, index)
            )
            respuesta_correcta = cursor.fetchone()

            if respuesta_correcta is None or respuesta_usuario != respuesta_correcta['respuesta']:
                respuestas_correctas = False
                break

        if respuestas_correctas:
            # Mostrar formulario para nueva contraseña
            return render_template('auth/reset-password.html', username=username)

        flash('Una o más respuestas son incorrectas.', 'error')

    return redirect(url_for('pss-recover.index'))

@bp.route('/update_password', methods=['POST'])
def update_password():
    username = request.form['username']
    new_password = request.form['new_password']
    confirm_password = request.form['confirm_password']

    if new_password != confirm_password:
        flash('Las contraseñas no coinciden.', 'error')
        return redirect(url_for('index'))

    hashed_password = generate_password_hash(new_password)

    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            'UPDATE usuarios SET contra = %s WHERE username = %s',
            (hashed_password, username)
        )
        db.commit()

    flash('Contraseña restablecida con éxito. Puedes iniciar sesión.', 'success')
    return redirect(url_for('auth.login'))