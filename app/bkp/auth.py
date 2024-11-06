import functools

from flask import (
    Blueprint, flash, g, make_response, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from .config.config import get_db

import psycopg2

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        cursor = get_db().cursor()
        cursor.execute(
            'SELECT * FROM "usuarios" WHERE id = %s', (user_id,)
        )
        g.user = cursor.fetchone()
        
        # Si el usuario no existe en la base de datos, limpiar la sesión
        if g.user is None:
            session.clear()

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if 'user_id' not in session or g.user is None:
            return redirect(url_for('auth.login'))
        return view(**kwargs)
    return wrapped_view

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['contra']
        db = get_db()
        error = None
        cursor = db.cursor()
        cursor.execute(
            'SELECT * FROM "usuarios" WHERE username = %s', (username,)
        )
        user = cursor.fetchone()

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['contra'], password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('dash.index'))

        flash(error)

    return render_template('auth/login.html')

@bp.route('/register', methods=('GET', 'POST'))
@login_required
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['contra']
        db = get_db()
        cursor = db.cursor()
        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'

        if error is None:
            try:
                cursor.execute(
                    "INSERT INTO usuarios (username, contra) VALUES (%s, %s)",
                    (username, generate_password_hash(password)),
                )
            except psycopg2.IntegrityError:
                db.rollback()
                error = f"User {username} is already registered."
            else:
                db.commit()
                return redirect(url_for("auth.login"))

        flash(error)

    return render_template('auth/register.html')

@bp.route('/logout')
def logout():
    # Limpiar la sesión completamente
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('auth.login'))