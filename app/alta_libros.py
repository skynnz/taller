from flask import Blueprint, render_template, request, redirect, url_for, flash
from .auth import login_required
from .config.config import get_db  # Asegúrate de tener una función para obtener la conexión a la base de datos

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
        
        # Validación de datos
        if not all([titulo, autores, genero, editorial, anio_publicacion, isbn, numero_paginas, descripcion]):
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
                    'INSERT INTO libros (titulo, autores, genero, editorial, anio_publicacion, isbn, numero_paginas, descripcion) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
                    (titulo, autores, genero, editorial, anio_publicacion, isbn, numero_paginas, descripcion)
                )
                libro_id = cursor.lastrowid  # Obtener el ID del libro recién insertado

                # Imprimir el libro_id para depuración
                print(f'libro_id después de la inserción en libros: {libro_id}')

                # Verificar si se obtuvo un ID válido
                if libro_id is None or libro_id == 0:
                    raise Exception("No se pudo obtener el ID del libro insertado.")

                # Insertar el stock por idioma en la tabla stock_libros
                idiomas = request.form.getlist('idiomas')
                cantidades = request.form.getlist('cantidades')

                # Imprimir los datos de idiomas y cantidades para depuración
                print(f'Idiomas: {idiomas}, Cantidades: {cantidades}')

                if idiomas and cantidades and len(idiomas) == len(cantidades):
                    for i in range(len(idiomas)):
                        idioma_nombre = idiomas[i]
                        cantidad_copias = int(cantidades[i])  # Convertir a entero
                        cursor.execute(
                            'INSERT INTO stock_libros (libro_id, idioma, cantidad_copias, copias_disponibles) VALUES (%s, %s, %s, %s)',
                            (libro_id, idioma_nombre, cantidad_copias, cantidad_copias)
                        )
                else:
                    raise Exception("Los idiomas y cantidades no coinciden.")
            
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
        
        with db.cursor() as cursor:
            # Actualizar los datos del libro
            cursor.execute(
                'UPDATE libros SET titulo = %s, autores = %s, genero = %s, editorial = %s, anio_publicacion = %s, isbn = %s, numero_paginas = %s, descripcion = %s WHERE id = %s',
                (titulo, autores, genero, editorial, anio_publicacion, isbn, numero_paginas, descripcion, book_id)
            )
            db.commit()

        # Actualizar el stock por idioma
        # Primero, eliminamos las entradas existentes para este libro
        cursor.execute('DELETE FROM stock_libros WHERE libro_id = %s', (book_id,))
        
        # Luego, insertamos las nuevas entradas
        idiomas = request.form.getlist('idiomas')
        for idioma in idiomas:
            idioma_nombre = idioma['idioma']
            cantidad_copias = idioma['cantidad_copias']
            cursor.execute(
                'INSERT INTO stock_libros (libro_id, idioma, cantidad_copias, copias_disponibles) VALUES (%s, %s, %s, %s)',
                (book_id, idioma_nombre, cantidad_copias, cantidad_copias)
            )
        
        db.commit()
        
        flash('Libro modificado exitosamente.', 'success')
        return redirect(url_for('alta_libros.index'))

    # Obtener los datos del libro para mostrarlos en el formulario
    with db.cursor() as cursor:
        cursor.execute('SELECT * FROM libros WHERE id = %s', (book_id,))
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
    return redirect(url_for('alta_libros.index'))