from flask import Blueprint, render_template, request, redirect, url_for, flash
from .auth import login_required
from .config.config import get_db  # Asegúrate de tener una función para obtener la conexión a la base de datos
import psycopg2

bp = Blueprint('alta_libros', __name__, url_prefix='/alta_libros')


@bp.route('/register', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        db = get_db()
        
        # Registro de un nuevo libro
        titulo = request.form['titulo']
        autores = request.form['autores']
        genero = request.form['genero']
        editorial = request.form['editorial']
        anio_publicacion = request.form['anio_publicacion']
        isbn = request.form['isbn']
        numero_paginas = request.form['numero_paginas']
        descripcion = request.form['descripcion']
        libro_estado = request.form['libro_estado']
        
        # Validación de datos
        if not all([titulo, autores, genero, editorial, anio_publicacion, isbn, numero_paginas, descripcion, libro_estado]):
            flash('Todos los campos son obligatorios.', 'error')
            return redirect(url_for('alta_libros.index'))

        try:
            # Convertir tipos de datos
            anio_publicacion = int(anio_publicacion)
            numero_paginas = int(numero_paginas)

            # Iniciar una transacción
            with db.cursor() as cursor:
                # Insertar el libro en la tabla libros
                cursor.execute(
                    'INSERT INTO libros (titulo, autores, genero, editorial, anio_publicacion, isbn, numero_paginas, descripcion, libro_estado) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)',
                    (titulo, autores, genero, editorial, anio_publicacion, isbn, numero_paginas, descripcion, libro_estado)
                )
            
            db.commit()  # Commit solo si todo fue exitoso
            flash('Libro registrado exitosamente.', 'success')
            return redirect(url_for('alta_libros.index'))

        except Exception as e:
            db.rollback()  # Deshacer cambios en caso de error
            print(f'Error al insertar en la base de datos: {e}')  # Imprimir error para depuración
            flash('Error al registrar el libro. Inténtalo de nuevo.', 'error')

    return render_template('libros/alta_libros.html')


@bp.route('/edit/<int:book_id>', methods=['GET', 'POST'])
@login_required
def edit(book_id):
    db = get_db()
    
    if request.method == 'POST':
        # Modificación de un libro existente
        titulo = request.form['titulo']
        autores = request.form['autores']
        genero = request.form['genero']
        editorial = request.form['editorial']
        anio_publicacion = request.form['anio_publicacion']
        isbn = request.form['isbn']
        numero_paginas = request.form['numero_paginas']
        descripcion = request.form['descripcion']
        libro_estado = request.form['libro_estado']
        
        with db.cursor() as cursor:
            # Actualizar los datos del libro
            cursor.execute(
                'UPDATE libros SET titulo = %s, autores = %s, genero = %s, editorial = %s, anio_publicacion = %s, isbn = %s, numero_paginas = %s, descripcion = %s, libro_estado = %s WHERE id = %s',
                (titulo, autores, genero, editorial, anio_publicacion, isbn, numero_paginas, descripcion, libro_estado, book_id)
            )
            db.commit()
        
        flash('Libro modificado exitosamente.', 'success')
        return redirect(url_for('alta_libros.list_books'))

    # Obtener los datos del libro para mostrarlos en el formulario
    with db.cursor() as cursor:
        cursor.execute('''
            SELECT id, titulo, autores, genero, editorial, anio_publicacion, isbn, 
                   numero_paginas, descripcion,
                   CASE
                       WHEN libro_estado = 1 THEN 'Habilitado'
                       WHEN libro_estado = 2 THEN 'Deshabilitado'
                       WHEN libro_estado = 3 THEN 'Solo en biblioteca'
                       ELSE 'Otro estado'
                   END AS libro_estado
            FROM libros WHERE id = %s
        ''', (book_id,))
        libro = cursor.fetchone()

        # Obtener el stock de idiomas para el libro
        cursor.execute('SELECT idioma, cantidad_copias FROM stock_libros WHERE libro_id = %s', (book_id,))
        stock_idiomas = cursor.fetchall()

    return render_template('libros/edit_libro.html', libro=libro, stock_idiomas=stock_idiomas)


@bp.route('/delete/<int:book_id>', methods=['GET','POST'])
@login_required
def delete(book_id):
    db = get_db()
    
    with db.cursor() as cursor:
        # Primero, eliminamos el stock del libro
        cursor.execute('DELETE FROM stock_libros WHERE libro_id = %s', (book_id,))
        
        # Luego, eliminamos el libro
        cursor.execute('DELETE FROM libros WHERE id = %s', (book_id,))
        db.commit()
    
    flash('Libro eliminado exitosamente.', 'success')
    return redirect(url_for('alta_libros.list_books'))


@bp.route('/list', methods=['GET'])
@login_required
def list_books():
    db = get_db()
    with db.cursor() as cursor:
        # Obtener todos los libros de la base de datos
        cursor.execute('SELECT * FROM libros')
        libros = cursor.fetchall()
    
    return render_template('libros/inicio.html', libros=libros)


@bp.route('/stock/<book_id>', methods=['GET', 'POST'])
@login_required
def stock(book_id):
    db = get_db()
    
    if request.method == 'POST':
        # Obtener datos del formulario
        cantidad_copias = request.form['cantidad_copias']
        idioma = request.form['idioma']
        
        
        with db.cursor() as cursor:
            cursor.execute('select * from stock_libros where libro_id = %s and idioma = %s', (book_id, idioma))
            existing_stock = cursor.fetchone()

            if existing_stock:
                #actualizar el stock
                cursor.execute('update stock_libros set cantidad_copias = %s where libro_id = %s and idioma = %s',
                               (cantidad_copias, book_id, idioma))
                flash('Stock actualizado correctamente', 'success')
            else:
            # Insertar o actualizar el stock del libro
                cursor.execute(
                    'INSERT INTO stock_libros (libro_id, cantidad_copias, idioma, copias_disponibles) VALUES (%s, %s, %s, %s)',
                    (book_id, cantidad_copias, idioma, cantidad_copias)
                )
                flash('Stock insertado correctamente', 'success')
            db.commit()
        
        return redirect(url_for('alta_libros.list_books', book_id=book_id))

    # Obtener el stock existente para el libro
    with db.cursor() as cursor:
        cursor.execute('SELECT * FROM stock_libros WHERE libro_id = %s', (book_id,))
        stock_libros = cursor.fetchall()

    return render_template('libros/stock_libros.html', stock_libros=stock_libros, book_id=book_id)

@bp.route('/ubicaciones', methods=['GET', 'POST'])
def listar_ubicaciones():
    db = get_db()
    with db.cursor() as cursor:
        # Obtener todas las ubicaciones
        cursor.execute('''
            SELECT u.id, u.libro_id, l.titulo, u.seccion, u.estanteria, u.columna 
            FROM ubicaciones u 
            JOIN libros l ON u.libro_id = l.id
        ''')
        ubicaciones = cursor.fetchall()

        # Obtener todos los libros para el formulario
        cursor.execute("SELECT id, titulo FROM libros")
        libros = cursor.fetchall()
    
    return render_template('libros/ubicaciones.html', ubicaciones=ubicaciones, libros=libros)

@bp.route('/ubicaciones/nueva', methods=['GET', 'POST'])
def registrar_ubicacion():
    db = get_db()
    if request.method == 'POST':
        libro_id = request.form['libro_id']
        seccion = request.form['seccion']
        estanteria = request.form['estanteria']
        columna = request.form['columna']
        
        print(f"libro_id: {libro_id}, seccion: {seccion}, estanteria: {estanteria}, columna: {columna}")
        
        try:
            with db.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO ubicaciones (libro_id, seccion, estanteria, columna) VALUES (%s, %s, %s, %s)",
                    (libro_id, seccion, estanteria, columna)
                )
                db.commit()
            flash('Ubicación registrada correctamente.')
            return redirect(url_for('alta_libros.listar_ubicaciones'))
        except psycopg2.IntegrityError as e:
            db.rollback()
            flash(f"Error de integridad: {str(e)}")
        except Exception as e:
            db.rollback()
            flash(f"Error al registrar la ubicación: {str(e)}")

    # Obtener todos los libros para el formulario
    with db.cursor() as cursor:
        cursor.execute("SELECT id, titulo FROM libros")
        libros = cursor.fetchall()
    return render_template('libros/ubicaciones.html', libros=libros)

@bp.route('/ubicaciones/editar/<ubicacion_id>', methods=['GET', 'POST'])
def editar_ubicacion(ubicacion_id):
    db = get_db()
    if request.method == 'POST':
        libro_id = request.form['libro_id']
        seccion = request.form['seccion']
        estanteria = request.form['estanteria']
        columna = request.form['columna']

        with db.cursor() as cursor:
            cursor.execute(
                "UPDATE ubicaciones SET libro_id = %s, seccion = %s, estanteria = %s, columna = %s WHERE id = %s",
                (libro_id, seccion, estanteria, columna, ubicacion_id)
            )
            db.commit()
        flash('Ubicación actualizada correctamente.')
        return redirect(url_for('alta_libros.listar_ubicaciones'))


    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM ubicaciones WHERE id = %s", (ubicacion_id,))
        ubicacion = cursor.fetchone()
    
    # Obtener todos los libros para el formulario
    with db.cursor() as cursor:
        cursor.execute("SELECT id, titulo FROM libros")
        libros = cursor.fetchall()
    
    return render_template('libros/ubicaciones.html', ubicacion=ubicacion, libros=libros)

@bp.route('/ubicaciones/eliminar/<ubicacion_id>', methods=['POST'])
def eliminar_ubicacion(ubicacion_id):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("DELETE FROM ubicaciones WHERE id = %s", (ubicacion_id,))
        db.commit()
    flash('Ubicación eliminada correctamente.')
    return redirect(url_for('alta_libros.listar_ubicaciones'))