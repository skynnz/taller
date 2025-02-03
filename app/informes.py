from flask import Flask, request, jsonify, send_file, Blueprint, redirect, render_template, url_for, flash, Response
from config.config import get_db
from reportlab.lib.pagesizes import letter, A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io
import base64  # Asegúrate de importar el módulo base64

bp = Blueprint('informes', __name__, url_prefix='/informes')

# Registrar una fuente
pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf'))


@bp.route('/exportar_pdf', methods=['GET', 'POST'])
def exportar_pdf():
    if request.method == 'POST':
        estado = request.form.get('libro_estado')
        autor = request.form.get('autores')

        db = get_db()
        with db.cursor() as cursor:
            query = '''SELECT libros.id,
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
                    FROM libros WHERE libro_estado=%s AND autores=%s'''
            cursor.execute(query, (estado, autor))
            informes = cursor.fetchall()

        if not informes:
            flash("No se encontraron informes para los criterios dados.", "warning")
            return redirect(url_for('informes.obtener_informes'))

        # Llamar a la función para exportar a PDF
        pdf_buffer = export_to_pdf(informes)

        # Enviar el archivo PDF generado al cliente
        return send_file(pdf_buffer, as_attachment=False, download_name="informes.pdf", mimetype='application/pdf')

    return render_template('informes/realizar_informe.html')

def export_to_pdf(data):
    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=landscape(A4))
    w, h = landscape(A4)
    max_rows_per_page = 45
    x_offset = 50
    y_offset = 50
    padding = 15
    
    # Definir las posiciones de las columnas
    xlist = [x + x_offset for x in [0, 50, 150, 200, 260, 320, 380, 440, 500, 560, 620]]
    headers = ["ID", "Título", "Autor", "Género", "Editorial", "Año","ISBN","N°. Paginas", "Descripción", "Estado"]
    
    # Dibujar encabezados
    c.setFont("Arial", 10)
    for i, header in enumerate(headers):
        c.drawString(xlist[i], h - y_offset, header)
    
    # Draw horizontal line under headers
    c.line(x_offset, h - y_offset - 5, w - x_offset, h - y_offset - 5)
    
    y = h - y_offset - 20  # Initial position for data

    # Draw data
    c.setFont("Arial", 10)
    for index, row in enumerate(data):
        if index >= max_rows_per_page:  # Check if the max rows per page is reached
            c.showPage()  # Create a new page
            y = h - y_offset - 20  # Reset vertical position
            # Redraw headers on the new page
            for i, header in enumerate(headers):
                c.drawString(xlist[i], y, header)
            c.line(x_offset, y - 5, w - x_offset, y - 5)
            y -= 20  # Move down for the next row

        for i, cell in enumerate(row):
            if i < len(xlist):  # Ensure index is within range
                c.drawString(xlist[i], y, str(cell))
        y -= padding  # Move down for the next row

    c.save()
    pdf_buffer.seek(0)

    return pdf_buffer

# ... otras rutas y lógica de la aplicación ...
