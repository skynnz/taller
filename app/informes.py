from flask import Flask, request, jsonify, send_file, Blueprint, redirect, render_template, url_for, flash, Response
from config.config import get_db
from reportlab.lib.pagesizes import letter
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


@bp.route('/', methods=['GET', 'POST'])
def obtener_informes():
    if request.method == 'POST':
        estado = request.form.get('libro_estado')
        autor = request.form.get('autores')

        db = get_db()
        with db.cursor() as cursor:
            query = "SELECT * FROM libros WHERE libro_estado=%s AND autores=%s"
            cursor.execute(query, (estado, autor))
            informes = cursor.fetchall()

        if not informes:
            flash("No se encontraron informes para los criterios dados.", "warning")
            return redirect(url_for('informes.obtener_informes'))

        # Generar PDF
        pdf_buffer = io.BytesIO()
        c = canvas.Canvas(pdf_buffer, pagesize=letter)

        # Títulos de la tabla
        c.setFont("Arial", 12)
        c.drawString(240, 780, "Informes Generados")  # Título
        y = 750  # Posición inicial para los datos

        # Agregar un salto de línea
        y -= 20  # Espacio entre el título y los encabezados

        # Encabezados de la tabla
        headers = ["ID", "Título", "Autor", "Género", "Editorial", "Año"]
        x_positions = [80, 130, 250, 350, 450, 550]


        # Dibujar encabezados y líneas
        for i, header in enumerate(headers):
            c.drawString(x_positions[i], y, header)

        # Dibujar línea horizontal debajo de los encabezados
        c.line(80, y - 5, 720, y - 5)  # Línea horizontal

        y -= 20  # Espacio entre los encabezados y los datos

        # Dibujar los datos
        for informe in informes:
            for i, data in enumerate(informe):
                if i < len(x_positions):  # Verificar que el índice esté dentro del rango
                    c.drawString(x_positions[i], y, str(data))  # Dibujar cada dato
                else:
                    print(f"Advertencia: Informe tiene más datos de los que se pueden mostrar. Datos: {informe}")

            # Dibujar línea horizontal debajo de cada fila de datos
            c.line(80, y - 5, 720, y - 5)  # Línea horizontal

            y -= 20  # Mover hacia abajo para la siguiente fila

            # Verificar si se ha llegado al final de la página
            if y < 50:  # Si queda poco espacio en la página
                c.showPage()  # Crear una nueva página
                y = 750  # Reiniciar la posición vertical

        c.save()
        pdf_buffer.seek(0)

        # Devolver el PDF como respuesta
        return Response(pdf_buffer.getvalue(), mimetype='application/pdf', headers={"Content-Disposition": "inline; filename=informes.pdf"})
    
    return render_template('informes/realizar_informe.html')

# ... otras rutas y lógica de la aplicación ...
