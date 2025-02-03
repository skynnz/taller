from flask import Blueprint, render_template, request, jsonify, flash, redirect, session, url_for, send_file
from .config.config import get_db  # Asegúrate de importar tu función para obtener la conexión a la base de datos
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
from datetime import datetime

bp = Blueprint('caja', __name__, url_prefix='/caja')

@bp.route('/abrir_caja', methods=['POST','GET'])
def abrir_caja():
    if request.method == 'POST':
        monto_apertura = request.form['monto_apertura']
        usuario_id = request.form['usuario_id']  # Obtener el ID del usuario del formulario
        db = get_db()
    
        with db.cursor() as cursor:
            # Verificar si ya hay una caja abierta por el mismo usuario
            cursor.execute('SELECT * FROM caja WHERE estado = %s AND usuario_id = %s', ('abierta', usuario_id))
            if cursor.fetchone():
                flash('Ya hay una caja abierta por este usuario. No se puede abrir otra.', 'danger')
                return redirect(url_for('caja.abrir_caja'))  # Cambia 'caja.index' por la ruta correspondiente
            
            # Abrir nueva caja
            cursor.execute('INSERT INTO caja (usuario_id, monto_apertura, estado) VALUES (%s, %s, %s)', (usuario_id, monto_apertura, 'abierta'))
            db.commit()
            
            flash('Caja abierta exitosamente.', 'success')
            return redirect(url_for('caja.abrir_caja'))  # Cambia 'caja.index' por la ruta correspondiente
    
    return render_template('caja/apertura.html')

@bp.route('/cerrar_caja', methods=['POST','GET'])
def cerrar_caja():
    if request.method == 'POST':
        monto_cierre = request.form['monto_cierre']
        usuario_id = request.form['usuario_id']
        db = get_db()
    
        with db.cursor() as cursor:
            # Verificar si hay una caja abierta
            cursor.execute('SELECT * FROM caja WHERE estado = %s AND usuario_id = %s', ('abierta', usuario_id))
            caja_abierta = cursor.fetchone()
            
            if not caja_abierta:
                flash('No hay ninguna caja abierta para cerrar.', 'danger')
                return redirect(url_for('caja.cerrar_caja'))  # Cambia 'caja.index' por la ruta correspondiente
            
            # Verificar que el monto_cierre sea igual a la suma de los montos en movimientos
            cursor.execute('SELECT SUM(monto) FROM movimientos WHERE usuario_id = %s AND estado = %s', (usuario_id, 'cobrado'))
            total_movimientos = cursor.fetchone()[0] or 0  # Manejar el caso donde no hay movimientos
            
            if float(monto_cierre) != total_movimientos:
                flash(f'El monto de cierre debe ser igual a la suma de los montos cobrados: {total_movimientos}.', 'danger')
                return redirect(url_for('caja.cerrar_caja'))  # Cambia 'caja.index' por la ruta correspondiente
            
            # Si se cumplen las condiciones, cerrar la caja
            cursor.execute('UPDATE caja SET fecha_cierre = CURRENT_TIMESTAMP, estado = %s, monto_cierre = %s WHERE id = %s', ('cerrada', monto_cierre, caja_abierta['id']))
            db.commit()
            
            flash('Caja cerrada exitosamente.', 'success')
            return redirect(url_for('caja.cerrar_caja'))  # Cambia 'caja.index' por la ruta correspondiente
        
    return render_template('caja/cierre.html')

@bp.route('/cobrar_multa', methods=['POST', 'GET'])
def cobrar_multa():
    if request.method == 'POST':
        prestamo_id = request.form['prestamo_id']
        monto = request.form['monto']
        db = get_db()
    
        with db.cursor() as cursor:
            # Verificar si el préstamo existe y obtener los detalles
            cursor.execute('SELECT p.id, p.cliente_id, m.dias_atraso, m.monto, b.id as libro_id, b.titulo FROM prestamos p JOIN multas m ON p.id = m.prestamo_id JOIN libros b ON p.libro_id = b.id WHERE p.id = %s', (prestamo_id,))
            prestamo = cursor.fetchone()
            
            if not prestamo:
                flash('El préstamo no existe o no tiene multas asociadas.', 'danger')
                return redirect(url_for('caja.cobro_multas'))  # Cambia 'caja.cobro_multas' por la ruta correspondiente
            
            # Asegúrate de que prestamo sea un DictRow
            cliente_id = prestamo['cliente_id']  # Acceso correcto si prestamo es un DictRow
            libro_titulo = prestamo['titulo']  # Acceso al título del libro
            
            # Actualizar la multa como cobrada
            cursor.execute('UPDATE multas SET estado = %s WHERE prestamo_id = %s', ('cobrado', prestamo_id))
            
            # Actualizar el estado del préstamo
            cursor.execute('UPDATE prestamos SET estado = %s WHERE id = %s', ('pagado', prestamo_id))  # Cambia 'pagado' por el estado que desees
            
            # Actualizar el stock de libros
            cursor.execute('UPDATE stock_libros SET copias_disponibles = copias_disponibles + 1 WHERE id = %s', (prestamo['libro_id'],))
            
            # Registrar la multa (si es necesario, puedes omitir esto si solo actualizas)
            cursor.execute('INSERT INTO multas (prestamo_id, monto, estado, dias_atraso) VALUES (%s, %s, %s, %s)', 
                        (prestamo_id, monto, 'cobrado', prestamo['dias_atraso']))  # Usa dias_atraso obtenido
            
            db.commit()
            
            # Obtener detalles del cliente y del usuario que cobró
            cursor.execute('SELECT nombres, apellidos, ci FROM clientes WHERE id = %s', (cliente_id,))
            cliente = cursor.fetchone()
            
            cursor.execute('SELECT full_name FROM usuarios WHERE id = %s', (session['user_id'],))  # Asumiendo que el ID del usuario está en la sesión
            usuario = cursor.fetchone()
            
            # Generar datos para el comprobante
            fecha_hora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            timbrado = "123456"  # Aquí puedes poner el número de timbrado que desees
            fecha_inicio = "2023-01-01"  # Cambia esto por la fecha de inicio real
            fecha_fin = "2023-12-31"  # Cambia esto por la fecha de fin real
            
            # Crear un PDF usando ReportLab
            pdf_buffer = io.BytesIO()
            c = canvas.Canvas(pdf_buffer, pagesize=letter)
            c.drawString(100, 750, "Libros Mágicos")
            c.drawString(100, 730, "Comprobante de Cobro de Multa")
            c.drawString(100, 710, "--------------------------------")
            c.drawString(100, 560, f"Timbrado: {timbrado}")
            c.drawString(100, 540, f"Fecha de Inicio: {fecha_inicio}")
            c.drawString(100, 520, f"Fecha de Fin: {fecha_fin}")
            c.drawString(100, 700, f"ID del Préstamo: {prestamo[0]}")
            c.drawString(100, 680, f"Libro: {libro_titulo}")
            c.drawString(100, 480, f"Días de Atraso: {prestamo[2]}")
            c.drawString(100, 460, f"Usuario que Cobró: {usuario['full_name']}")
            c.drawString(100, 640, f"Fecha/Hora: {fecha_hora}")
            c.drawString(100, 620, f"Cliente: {cliente['nombres']} {cliente['apellidos']}")
            c.drawString(100, 600, f"CI Nro: {cliente['ci']}")
            c.drawString(100, 580, f"Total: {prestamo[3]}")
            c.showPage()
            c.save()
            pdf_buffer.seek(0)

            return send_file(pdf_buffer, as_attachment=True, download_name='comprobante_cobro.pdf', mimetype='application/pdf')
    return render_template('caja/cobro_multas.html')

@bp.route('/buscar_prestamo', methods=['POST', 'GET'])
def buscar_prestamo():
    if request.method == 'POST':
        db = get_db()  # Asegúrate de que esta línea esté presente y que get_db esté correctamente definido
        prestamo_id = request.form['prestamo_id']
    
        with db.cursor() as cursor:
            # Verificar si el préstamo existe y obtener los detalles de la multa
            cursor.execute('SELECT p.id, m.dias_atraso, m.monto FROM prestamos p JOIN multas m ON p.id = m.prestamo_id WHERE p.id = %s AND m.estado = %s', (prestamo_id, 'Pendiente'))
            prestamo = cursor.fetchone()
            
            if not prestamo:
                flash('El préstamo no existe o no tiene multas pendientes.', 'danger')
                return redirect(url_for('caja.cobrar_multa'))  # Cambia 'caja.cobro_multas' por la ruta correspondiente
            
            # Crear un diccionario para facilitar el acceso a los datos
            prestamo_info = {
                'id': prestamo[0],
                'dias_atraso': prestamo[1],
                'monto': prestamo[2]
            }
            
            return render_template('caja/cobro_multas.html', prestamo=prestamo_info)
    return render_template('caja/cobro_multas.html')