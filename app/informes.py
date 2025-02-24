from flask import Flask, request, jsonify, send_file, Blueprint, redirect, render_template, url_for, flash, Response, make_response
from .config.config import get_db
from weasyprint import HTML

bp = Blueprint('informes', __name__, url_prefix='/informes')

@bp.route('/formulario_libros')
def formulario_libros():
    return render_template('informes/realizar_informe.html')

@bp.route('/formulario_pre')
def formulario_pre():
    return render_template('informes/realizar_informe_pre.html')

@bp.route('/exportar_pdf_libros', methods=['GET', 'POST'])
def exportar_pdf_libros():
    if request.method == 'POST':
        estado = request.form.get('libro_estado')

        db = get_db()
        with db.cursor() as cursor:
            cursor.execute('''SELECT libros.id,
                        libros.titulo,
                        libros.autores,
                        libros.genero,
                        libros.editorial,
                        libros.anio_publicacion,
                        libros.isbn,
                        libros.numero_paginas,
                        libros.descripcion,
                    CASE
                        WHEN libros.libro_estado = 1 THEN 'Habilitado'::text
                        WHEN libros.libro_estado = 2 THEN 'Deshabilitado'::text
                        WHEN libros.libro_estado = 3 THEN 'Solo en biblioteca'::text
                        ELSE 'Otro estado'::text
                    END AS libro_estado
                    FROM libros WHERE libro_estado=%s''', (estado,))
            informes = cursor.fetchall()

         # Renderizar la plantilla HTML con los datos
    html = render_template('informes/mostrar_informe.html', informes=informes)

    # Convertir HTML a PDF
    pdf = HTML(string=html).write_pdf()

    # Devolver el PDF como respuesta para mostrarlo en el navegador
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=reporte.pdf'  # "inline" para mostrar en el navegador
    return response

@bp.route('/exportar_pdf_prestamos', methods=['GET', 'POST'])
def exportar_pdf_prestamos():
    informes_pre = []  # Inicializar la variable antes de usarla
    if request.method == 'POST':
        filtro = request.form.get('filtro')

        db = get_db()
        with db.cursor() as cursor:
            cursor.execute('''SELECT a.id, a.libro_id, d.titulo, a.fecha_prestamo, a.fecha_devolucion, a.estado,
                    b.full_name as Nom_Usuario,
                    b.username as Nick_Usuario,
                    CONCAT(c.nombres, ' ', c.apellidos) as Nom_Cliente    
                FROM prestamos a
                JOIN usuarios b ON a.usuario_id = b.id
                JOIN clientes c ON a.cliente_id = c.id
                JOIN libros d ON a.libro_id = d.id WHERE a.estado=%s''', (filtro,))
            informes_pre = cursor.fetchall()  # Asignar el resultado a la variable
            
        # Verificar si se encontraron informes
        if not informes_pre:
            flash("No se encontraron informes para los criterios dados.", "warning")
            return redirect(url_for('informes.formulario_pre'))

        # Renderizar la plantilla HTML con los datos
        html = render_template('informes/mostrar_informe_pre.html', informes_pre=informes_pre)

        # Convertir HTML a PDF
        pdf = HTML(string=html).write_pdf()

        # Devolver el PDF como respuesta para mostrarlo en el navegador
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'inline; filename=reporte.pdf'  # "inline" para mostrar en el navegador
        return response

    return render_template('informes/realizar_informe_pre.html')