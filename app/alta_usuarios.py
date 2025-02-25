import psycopg2
from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash
from .config.config import get_db

bp = Blueprint('alta_usuarios', __name__, url_prefix='/alta_usuarios')

@bp.route('/alta', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['contra']
        email = request.form['email']
        fullname = request.form['fullname']
        gru_cod = request.form.get('gru_cod')  # Obtener el rol del formulario
        pregunta = request.form.get('pregunta')
        respuesta = request.form['respuesta']
        db = get_db()
        error = None

        # Validaciones
        if not username:
            error = 'El nombre de usuario es obligatorio.'
        elif not password:
            error = 'La contraseña es obligatoria.'
        elif not email:
            error = 'El email es obligatorio.'
        elif not fullname:
            error = 'El nombre completo es obligatorio.'
        elif not gru_cod:
            error = 'El rol es obligatorio.'
        elif not pregunta:
            error = 'Elija una pregunta'
        elif not respuesta:
            error = 'Indique una respuesta a la pregunta'

        if error is None:
            with db.cursor() as cursor:
                # Verificar si el usuario ya existe
                cursor.execute("SELECT id FROM usuarios WHERE username = %s", (username,))
                existing_user = cursor.fetchone()
                
                if existing_user:
                    error = f"El usuario {username} ya está registrado."
                else:
                    try:
                        cursor.execute(
                            "INSERT INTO usuarios (username, contra,email,full_name,gru_cod,estado) VALUES (%s, %s, %s, %s, %s, %s) returning id",
                            (username, generate_password_hash(password), email, fullname, gru_cod, 1),
                        )
                        user_id = cursor.fetchone()[0]
                        cursor.execute(
                            "insert into preguntas_seguridad (user_id, pregunta, respuesta) values (%s, %s, %s) returning id", (user_id, pregunta, respuesta)
                        )
                        db.commit()
                        flash('Usuario registrado correctamente.')
                        return redirect(url_for("alta_usuarios.register"))

                    except psycopg2.IntegrityError:
                        db.rollback()
                        error = f"Error al registrar el usuario."

        flash(error)

    return render_template('usuarios/alta_usuarios.html')

@bp.route('/usuarios', methods=['GET'])
def listar_usuarios():
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute('''SELECT u.id, u.username, u.email, u.full_name,
        case
        when ru.gru_cod = 1 then 'Admin'
        when ru.gru_cod = 2 then 'Cajero'
        when ru.gru_cod = 3 then 'Bibliotecario'
        when ru.gru_cod = 4 then 'Gerente'
        when ru.gru_cod = 5 then 'Asistente biblioteca'
        end as gru_cod,
        case
        when u.estado = 1 then 'Habilitado'
        when u.estado = 2 then 'Deshabilitado'
        end as estado
        FROM usuarios u JOIN grupos ru ON u.gru_cod = ru.gru_cod''')
        usuarios = cursor.fetchall()
    return render_template('usuarios/inicio_usuarios.html', usuarios=usuarios)

@bp.route('/usuarios/anular/<usuario_id>', methods=['POST'])
def anular_usuario(usuario_id):
    motivo = request.form['motivo']
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("UPDATE usuarios SET estado = 2 WHERE id = %s", (usuario_id,))
        db.commit()
    flash('Usuario deshabilitado correctamente.')
    return redirect(url_for('alta_usuarios.listar_usuarios'))


@bp.route('/usuarios/edit/<usuario_id>', methods=['GET', 'POST'])
def edit_usuario(usuario_id):
    db = get_db()
    if request.method == 'POST':
        fullname = request.form['fullname']
        email = request.form['email']
        username = request.form['username']
        gru_cod = request.form['gru_cod']
        estado = request.form['estado']
        pregunta = request.form['pregunta']
        respuesta = request.form['respuesta']

        with db.cursor() as cursor:
            cursor.execute(
                "UPDATE usuarios SET full_name = %s, email = %s, username = %s, gru_cod = %s, estado = %s WHERE id = %s",
                (fullname, email, username, gru_cod, estado, usuario_id)
            )
            cursor.execute(
                "UPDATE preguntas_seguridad SET pregunta = %s, respuesta = %s WHERE user_id = %s",
                (pregunta, respuesta, usuario_id)
            )
            db.commit()

        flash('Datos del usuario actualizados correctamente.')
        return redirect(url_for('alta_usuarios.listar_usuarios'))

    with db.cursor() as cursor:
        cursor.execute('''
            SELECT u.id, u.username, u.email, u.full_name, u.gru_cod, u.estado, ps.pregunta, ps.respuesta
            FROM usuarios u
            JOIN preguntas_seguridad ps ON u.id = ps.user_id
            WHERE u.id = %s
        ''', (usuario_id,))
        usuario = cursor.fetchone()
    
    return render_template('usuarios/edit_usuarios.html', usuario=usuario)