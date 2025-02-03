from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file
from .config.config import get_db 
import datetime
from datetime import date
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io

bp = Blueprint('prestamos', __name__, url_prefix='/prestamos')

def calcular_dias_atraso(fecha_devolucion):
    fecha_actual = date.today()
    dias_atraso = (fecha_actual - fecha_devolucion).days
    return max(dias_atraso, 0)  # Ensure no negative days

@bp.route('/', methods=['GET', 'POST'])
def index():
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute('SELECT * FROM prestamos ')
        prestamos = cursor.fetchall()
    return render_template('prestamos/inicio_prestamos.html', prestamos=prestamos)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    db = get_db()
    
    if request.method == 'POST':
        libro_id = request.form['libro_id']
        usuario_id = session['user_id']  # Obtener el usuario de la sesión
        fecha_prestamo = request.form['fecha_prestamo']
        fecha_devolucion = request.form['fecha_devolucion']
        estado = request.form['estado']  # Obtener el estado del formulario
        cliente_id = request.form['cliente_id']
        
        with db.cursor() as cursor:
            # Insertar el préstamo
            cursor.execute(
                'INSERT INTO prestamos (libro_id, usuario_id, fecha_prestamo, fecha_devolucion, estado, cliente_id) VALUES (%s, %s, %s, %s, %s, %s)',
                (libro_id, usuario_id, fecha_prestamo, fecha_devolucion, estado, cliente_id)
            )
            
            # Reducir la cantidad de copias en stock
            cursor.execute(
                'UPDATE stock_libros SET copias_disponibles = copias_disponibles - 1 WHERE libro_id = %s AND copias_disponibles > 0',
                (libro_id,)
            )
            db.commit()
        
        flash('Préstamo registrado exitosamente.', 'success')
        return redirect(url_for('prestamos.index'))

    # Obtener libros para el select
    with db.cursor() as cursor:
        cursor.execute('SELECT id, titulo, autores, isbn, editorial FROM libros WHERE libro_estado = 1')
        libros = cursor.fetchall()

    # Obtener clientes para el select
    with db.cursor() as cursor:
        cursor.execute('SELECT id, nombres, apellidos FROM clientes')
        clientes = cursor.fetchall()

    return render_template('prestamos/alta_prestamos.html', libros=libros, clientes=clientes)

@bp.route('/edit/<int:prestamo_id>', methods=['GET', 'POST'])
def edit(prestamo_id):
    db = get_db()
    
    if request.method == 'POST':
        libro_id = request.form['libro_id']
        usuario_id = request.form['usuario_id']
        fecha_prestamo = request.form['fecha_prestamo']
        estado = request.form['estado']
        
        with db.cursor() as cursor:
            cursor.execute(
                'UPDATE prestamos SET libro_id = %s, usuario_id = %s, fecha_prestamo = %s, estado = %s WHERE id = %s',
                (libro_id, usuario_id, fecha_prestamo, estado, prestamo_id)
            )
            db.commit()
        
        flash('Préstamo actualizado exitosamente.', 'success')
        return redirect(url_for('prestamos.index'))

    with db.cursor() as cursor:
        cursor.execute('SELECT * FROM prestamos WHERE id = %s', (prestamo_id,))
        prestamo = cursor.fetchone()

    # Obtener libros para el select
    with db.cursor() as cursor:
        cursor.execute('SELECT id, titulo FROM libros')  # Asegúrate de que la tabla libros tenga un campo titulo
        libros = cursor.fetchall()

    return render_template('prestamos/edit_prestamo.html', prestamo=prestamo, libros=libros)

@bp.route('/anular/<prestamo_id>', methods=['GET', 'POST'])
def anular(prestamo_id):
    if request.method == 'POST':
        motivo = request.form['motivo']
        print(f"Anulando préstamo ID: {prestamo_id} con motivo: {motivo}")  # Mensaje de depuración
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute(
                'UPDATE prestamos SET estado = %s WHERE id = %s',
                ('anulado', prestamo_id)
            )
            db.commit()
        
        flash('Préstamo anulado exitosamente. Motivo: ' + motivo, 'success')
        return redirect(url_for('prestamos.index'))

    return render_template('prestamos/inicio_prestamos.html', prestamo_id=prestamo_id)

@bp.route('/buscar_prestamo', methods=['POST', 'GET'])
def buscar_prestamo():
    if request.method == 'POST':
        busqueda = request.form['busqueda']
        db = get_db()
    
        with db.cursor() as cursor:
            # Intentar buscar por ID
            cursor.execute('SELECT * FROM prestamos WHERE id = %s AND estado = %s', (busqueda, 'activo'))
            prestamos = cursor.fetchall()  # Cambiar a fetchall para obtener múltiples resultados
            
            if not prestamos:
                # Si no se encuentra por ID, intentar buscar por nombre del cliente
                cursor.execute('SELECT * FROM prestamos WHERE cliente_id IN (SELECT id FROM clientes WHERE ci = %s) AND estado = %s', (f'%{busqueda}%', 'activo'))
                prestamos = cursor.fetchall()  # Cambiar a fetchall para obtener múltiples resultados
            
            if prestamos:
                # Aquí puedes calcular los días de atraso para cada préstamo
                prestamos_info = []
                for prestamo in prestamos:
                    dias_atraso = calcular_dias_atraso(prestamo['fecha_devolucion'])
                    prestamos_info.append((prestamo, dias_atraso))
                return render_template('prestamos/devolucion_prestamos.html', prestamos=prestamos_info)
            else:
                flash('No se encontraron préstamos activos.', 'danger')
                return redirect(url_for('prestamos.buscar_prestamo'))
    return render_template('prestamos/devolucion_prestamos.html')

@bp.route('/return/<int:prestamo_id>', methods=['POST'])
def return_book(prestamo_id):
    db = get_db()
    
    with db.cursor() as cursor:
        # Obtener el libro_id, usuario_id y las fechas del préstamo
        cursor.execute('SELECT libro_id, usuario_id, cliente_id, fecha_devolucion FROM prestamos WHERE id = %s', (prestamo_id,))
        result = cursor.fetchone()
        
        if result:
            libro_id, usuario_id, cliente_id, fecha_devolucion = result
            # Calcular si hay días de atraso
            fecha_actual = datetime.date.today()  # Asegúrate de importar datetime
            dias_atraso = (fecha_actual - fecha_devolucion).days
            
            if dias_atraso > 0:
                # Calcular el cargo por atraso 
                cargo = dias_atraso * 5000 
                flash(f'El libro tiene {dias_atraso} días de atraso. Cargo: ${cargo}', 'warning')
                
                # Registrar la multa
                cursor.execute(
                    'INSERT INTO multas (prestamo_id, monto, estado, dias_atraso) VALUES (%s, %s, %s, %s)',
                    (prestamo_id, cargo, 'Pendiente', dias_atraso)
                )
                
                # Registrar la devolución como "Pendiente de cobro"
                cursor.execute(
                    'UPDATE prestamos SET estado = %s WHERE id = %s',
                    ('Pendiente de cobro', prestamo_id)
                )
                
                # Insertar en la tabla de movimientos
                cursor.execute(
                    'INSERT INTO movimientos (prestamo_id, libro_id, usuario_id, cliente_id, tipo_movimiento, monto, estado) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                    (prestamo_id, libro_id, usuario_id, cliente_id, 'devolución', cargo, 'Pendiente de cobro')
                )
                
                db.commit()
                
                flash('Devolución registrada exitosamente.', 'success')
                return redirect(url_for('prestamos.index'))
            else:
                # Si no hay atraso, simplemente marca como devuelto
                cursor.execute(
                    'UPDATE prestamos SET estado = %s WHERE id = %s',
                    ('devuelto', prestamo_id)
                )
                # Aumentar la cantidad de copias en stock
                cursor.execute(
                    'UPDATE stock_libros SET copias_disponibles = copias_disponibles + 1 WHERE libro_id = %s',
                    (libro_id,)
                )
                db.commit()
                flash('Devolución registrada exitosamente.', 'success')
                
                # Obtener detalles del cliente y del usuario
                cursor.execute('SELECT nombres, apellidos FROM clientes WHERE id = %s', (cliente_id,))
                cliente = cursor.fetchone()
                
                cursor.execute('SELECT full_name FROM usuarios WHERE id = %s', (usuario_id,))
                usuario = cursor.fetchone()
                
                # Obtener el título del libro
                cursor.execute('SELECT titulo FROM libros WHERE id = %s', (libro_id,))
                libro = cursor.fetchone()
                
                # Crear un PDF usando ReportLab
                pdf_buffer = io.BytesIO()
                c = canvas.Canvas(pdf_buffer, pagesize=letter)
                c.drawString(100, 750, "Nombre de la Empresa")
                c.drawString(100, 730, "Comprobante de Devolución")
                c.drawString(100, 700, f"Nombre del Cliente: {cliente['nombres']} {cliente['apellidos']}")
                c.drawString(100, 680, f"Usuario que Procesó la Devolución: {usuario['full_name']}")
                c.drawString(100, 660, f"ID del Préstamo: {prestamo_id}")
                c.drawString(100, 640, f"Libro Prestado: {libro['titulo']}")
                c.drawString(100, 620, f"Se recibe el libro {libro['titulo']} y se reconoce la devolución del mismo.")
                c.showPage()
                c.save()
                pdf_buffer.seek(0)

                return send_file(pdf_buffer, download_name='comprobante_devolucion.pdf', as_attachment=True)

        else:
            flash('Préstamo no encontrado.', 'danger')
            return redirect(url_for('prestamos.index'))