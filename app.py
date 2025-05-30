import time
import os
from datetime import datetime, date
from flask import Flask, flash, render_template, request, redirect, session, send_from_directory
from flask_mysqldb import MySQL
from contextlib import contextmanager
from MySQLdb import OperationalError
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


app = Flask(__name__)
app.secret_key = "develoteca"

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'sitio'

mysql = MySQL(app)

@contextmanager
def get_db_cursor():
    conexion = mysql.connection
    cursor = conexion.cursor()
    try:
        yield cursor
    finally:
        cursor.close()


def execute_with_retry(query, params=None, retries=3, delay=2):
    for attempt in range(retries):
        try:
            with get_db_cursor() as cursor:
                cursor.execute(query, params or ())
                return cursor.fetchall()
        except OperationalError as e:
            if attempt == retries - 1:
                raise  
            time.sleep(delay)  

@app.route('/')
def inicio():
    return render_template('sitio/index.html')

@app.route('/img/<imagen>')
def imagenes(imagen):
    print(imagen)
    return send_from_directory(os.path.join('templates/sitio/img/'), imagen)

@app.route('/css/<archivocss>')
def css_link(archivocss):
    return send_from_directory(os.path.join('/static/css'), archivocss)

@app.route('/fotos', methods=['GET'])
def fotos():
    categoria = request.args.get('categoria')
    query = "SELECT * FROM `fotos`" if not categoria else "SELECT * FROM `fotos` WHERE `categoria_fotografia` = %s"
    params = (categoria,) if categoria else None

    fotos = execute_with_retry(query, params)
    return render_template('sitio/fotos.html', fotos=fotos)

@app.route('/nosotros')
def nosotros():
    return render_template('sitio/nosotros.html')

@app.route('/producto')
def producto():
    return render_template('sitio/producto.html')

@app.route('/contacto')
def contacto():
    return render_template('sitio/contacto.html')

@app.route('/admin/')
def admin_index():
    if not 'login' in session:
        return redirect("/admin/login")
    return render_template('admin/index.html')

@app.route('/register')
def admin_register():
    return render_template('admin/register.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        _usuario = request.form['txtUsuario'].strip()
        _password = request.form['txtPassword'].strip()

        if not _usuario or not _password:
            return render_template("admin/login.html", mensaje="Usuario y contraseña son obligatorios")

        try:
            with get_db_cursor() as cursor:
                cursor.execute("SELECT id_usuario, nombre_usuario, contrasena FROM usuario WHERE nombre_usuario = %s", (_usuario,))
                usuario = cursor.fetchone()

                if usuario is None:
                    return render_template("admin/login.html", mensaje="Usuario no encontrado")
                elif usuario[2].strip() == _password:
                    session["login"] = True
                    session["usuario"] = usuario[1]
                    session["id_usuario"] = usuario[0]
                    return redirect("/admin")
                else:
                    return render_template("admin/login.html", mensaje="Contraseña incorrecta")
        except OperationalError as e:
            print(f"Error de conexión a la base de datos: {e}")
            return render_template("admin/login.html", mensaje="Error de conexión a la base de datos")
        except Exception as e:
            print(f"Error inesperado: {e}")
            return render_template("admin/login.html", mensaje="Error inesperado")

    return render_template('admin/login.html')

@app.route('/admin/cerrar')
def admin_login_cerrar():
    session.clear()
    return redirect('/admin/login')

@app.route('/admin/fotos')
def admin_fotos():
    if 'login' not in session:
        return redirect("/admin/login")

    fotos = execute_with_retry("SELECT * FROM `fotos`")
    today = date.today().strftime('%Y-%m-%d')
    return render_template("admin/fotos.html", fotos=fotos, today=today)

@app.route('/admin/fotos/guardar', methods=['POST'])
def admin_libros_guardar():
    _nombre = request.form['txtNombre']
    _archivo = request.files['txtImagen']
    _categoria = request.form['txtCategoria']
    _date = request.form['txtDate']

    tiempo = datetime.now()
    horaActual = tiempo.strftime('%Y%H%M%S')

    nuevoNombre = None
    if _archivo.filename != "":
        nuevoNombre = horaActual + "_" + _archivo.filename
        _archivo.save("templates/sitio/img/" + nuevoNombre)

    if _archivo.filename == "":
        flash("Error: No se ha subido ninguna imagen.", "error")
        return redirect('/admin/fotos')

    try:
        with get_db_cursor() as cursor:
            sql = "INSERT INTO `fotos` (`id_foto`, `nombre_fotografia`, `imagen`, `categoria_fotografia`, `fecha_subida`) VALUES (NULL, %s, %s, %s, %s);"
            datos = (_nombre, nuevoNombre, _categoria, _date)
            cursor.execute(sql, datos)

            id_foto = cursor.lastrowid

            sql_interaccion = """
            INSERT INTO `interacciones` (`id_interacciones`, `tipo_interaccion`, `fecha_interaccion`, `id_foto`, `id_usuario`, `nombre_fotografia`, `imagen`)
            VALUES (NULL, 'subida', %s, %s, %s, %s, %s);
            """
            id_usuario = session.get("id_usuario", 1)
            datos_interaccion = (_date, id_foto, id_usuario, _nombre, nuevoNombre)
            cursor.execute(sql_interaccion, datos_interaccion)

            mysql.connection.commit()
    except Exception as e:
        print(f"Error al guardar la foto: {e}")
        flash("Error al guardar la foto.", "error")
        return redirect('/admin/fotos')

    return redirect('/admin/fotos')

@app.route('/admin/fotos/borrar', methods=['POST'])
def admin_fotos_borrar():
    if 'login' not in session:
        return redirect("/admin/login")

    _id = request.form.get('txtID')
    if not _id:
        return "Error: No se proporcionó el ID de la foto.", 400

    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT imagen, nombre_fotografia FROM `fotos` WHERE id_foto = %s", (_id,))
            foto = cursor.fetchone()

            if foto:
                imagen, nombre_fotografia = foto
                ruta_imagen = os.path.join("templates/sitio/img/", imagen)
                if os.path.exists(ruta_imagen):
                    os.unlink(ruta_imagen)

                sql_interaccion = """
                INSERT INTO `interacciones` (
                    `id_interacciones`, 
                    `tipo_interaccion`, 
                    `fecha_interaccion`, 
                    `id_foto`, 
                    `id_usuario`, 
                    `nombre_fotografia`, 
                    `imagen`, 
                    `mensaje_comentario`
                )
                VALUES (NULL, 'borrado', NOW(), %s, %s, %s, %s, %s);
                """
                id_usuario = session.get("id_usuario")
                if id_usuario is None:
                    return "Error: No se ha iniciado sesión.", 401

                datos_interaccion = (_id, id_usuario, nombre_fotografia, imagen, "Sin comentario")  
                cursor.execute(sql_interaccion, datos_interaccion)

                cursor.execute("DELETE FROM fotos WHERE id_foto = %s", (_id,))
                mysql.connection.commit()
            else:
                return "Error: La foto no existe.", 404
    except Exception as e:
        print(f"Error al borrar la foto: {e}")
        return f"Error: {e}", 500

    return redirect('/admin/fotos')

# Configura tu email y contraseña de aplicación

EMAIL_USER = 'clarkcordobainti@gmail.com'
EMAIL_PASSWORD = 'ozne oxmx oqto hndb'

@app.route('/sitio_web/contacto', methods=['GET', 'POST'])
def email():
    if request.method == "POST":
        nombre = request.form.get('nombre', '').strip()
        asunto = request.form.get('asunto', '').strip()
        correo = request.form.get('email', '').strip()
        mensaje = request.form.get('mensaje', '').strip()

        # Validaciones del lado del servidor
        if not nombre or not asunto or not correo or not mensaje:
            flash('Todos los campos son obligatorios.', 'danger')
            return redirect('/sitio_web/contacto')  # Redirige para mostrar el mensaje

        # Validación simple de correo electrónico
        if "@" not in correo or "." not in correo:
            flash('El correo electrónico no es válido.', 'danger')
            return redirect('/sitio_web/contacto')  # Redirige para mostrar el mensaje

        # Cuerpo del correo
        body = f"""
        Nuevo mensaje del formulario:

        Nombre y Apellido: {nombre}
        Asunto: {asunto}
        Correo del cliente: {correo}
        Mensaje: {mensaje}
        """

        # Preparar y enviar
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = EMAIL_USER
        msg['Subject'] = f'Nueva consulta: {asunto}'
        msg.attach(MIMEText(body, 'plain'))

        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_USER, EMAIL_USER, msg.as_string())
            server.quit()
            flash('Correo enviado correctamente.', 'success')  # Mensaje de éxito
            
        except Exception as e:
            print(e)
            flash('Error al enviar el correo.', 'danger')  # Mensaje de error

        return redirect('/sitio_web/contacto')  # Redirige para mostrar el mensaje flash

    return render_template("sitio/contacto.html")

if __name__ == "__main__":
    app.run(debug=True)
