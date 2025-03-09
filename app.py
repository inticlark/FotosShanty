import os
from datetime import datetime, date
from flask import Flask, flash, render_template, request, redirect, session, send_from_directory
from flask_mysqldb import MySQL


app = Flask(__name__)
app.secret_key = "develoteca"

# Configuración de MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'sitio'

# Inicialización de MySQL
mysql = MySQL(app)

@app.route('/') 
def inicio():
    return render_template('sitio/index.html')

@app.route('/img/<imagen>')
def imagenes(imagen):
    print(imagen) 
    return send_from_directory(os.path.join('templates/sitio/img/'),imagen)

@app.route('/css/<archivocss>')
def css_link(archivocss):
    return send_from_directory(os.path.join('/static/css'), archivocss)

@app.route('/fotos', methods=['GET'])
def fotos():
    
    categoria = request.args.get('categoria')


    conexion = mysql.connection
    cursor = conexion.cursor()
    if categoria:
        cursor.execute("SELECT * FROM `fotos` WHERE `categoria_fotografia` = %s", (categoria,))
    else:
        cursor.execute("SELECT * FROM `fotos`")

    fotos = cursor.fetchall()
    conexion.commit()

    return render_template('sitio/fotos.html', fotos=fotos)


@app.route('/nosotros')
def nosotros():
    return render_template('sitio/nosotros.html')

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
        _usuario = request.form['txtUsuario'].strip()  # Eliminar espacios en blanco
        _password = request.form['txtPassword'].strip()  # Eliminar espacios en blanco

        print(f"Usuario ingresado: {_usuario}")  # Verifica que el nombre de usuario sea el esperado
        print(f"Contraseña ingresada: {_password}")  # Verifica la contraseña ingresada

        # Validar que el usuario y la contraseña no estén vacíos
        if not _usuario or not _password:
            return render_template("admin/login.html", mensaje="Usuario y contraseña son obligatorios")

        cursor = None
        try:
            # Conectar a la base de datos
            conexion = mysql.connection
            cursor = conexion.cursor()

            # Ejecuta la consulta para obtener el id_usuario, nombre_usuario y contrasena
            cursor.execute("SELECT id_usuario, nombre_usuario, contrasena FROM usuario WHERE nombre_usuario = %s", (_usuario,))
            usuario = cursor.fetchone()  # Obtén la primera fila (el usuario)

            # Depuración: Imprime la tupla completa
            print(f"Resultado de la consulta: {usuario}")

            # Verificar si la consulta devolvió un resultado
            if usuario is None:
                print("El usuario no existe en la base de datos.")  # Mensaje de depuración
                return render_template("admin/login.html", mensaje="Usuario no encontrado")
            else:
                print(f"Usuario encontrado: {usuario[1]}")  # Verifica el nombre de usuario
                print(f"Contraseña almacenada: {usuario[2]}")  # Verifica la contraseña almacenada

                # Compara la contraseña almacenada con la ingresada
                if usuario[2].strip() == _password:
                    session["login"] = True
                    session["usuario"] = usuario[1]  # Asignamos el nombre de usuario a la sesión
                    session["id_usuario"] = usuario[0]  # Asignamos el id_usuario a la sesión
                    return redirect("/admin")  # Redirige a la página de administración
                else:
                    return render_template("admin/login.html", mensaje="Contraseña incorrecta")

        
        except Exception as e:
            print(f"Error inesperado: {e}")
            return render_template("admin/login.html", mensaje="Error inesperado")
        finally:
            # Cierra solo el cursor
            if cursor:
                cursor.close()

    return render_template('admin/login.html')

@app.route('/admin/cerrar') 
def admin_login_cerrar():
        session.clear()
        return redirect('/admin/login')

@app.route('/admin/fotos') 
def admin_fotos():
    if 'login' not in session:
        return redirect("/admin/login")

    conexion = mysql.connection
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM `fotos`")
    fotos = cursor.fetchall()
    conexion.commit()

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

    # Asignar un valor predeterminado a nuevoNombre
    nuevoNombre = None  # o puedes usar un valor como "default_image.jpg"

    if _archivo.filename != "":
        nuevoNombre = horaActual + "_" + _archivo.filename
        _archivo.save("templates/sitio/img/" + nuevoNombre)

    # Verificar si nuevoNombre tiene un valor antes de usarlo
    if _archivo.filename == "":
        flash("Error: No se ha subido ninguna imagen.", "error")  # Mensaje de error
        return redirect('/admin/fotos')  # Redirigir de vuelta a la página de fotos

    # Insertar en la tabla fotos
    sql = "INSERT INTO `fotos` (`id_foto`, `nombre_fotografia`, `imagen`, `categoria_fotografia`, `fecha_subida`) VALUES (NULL, %s, %s, %s, %s);"
    datos = (_nombre, nuevoNombre, _categoria, _date)
    conexion = mysql.connection
    cursor = conexion.cursor()
    cursor.execute(sql, datos)
    
    # Obtener el id_foto recién insertado
    id_foto = cursor.lastrowid

    # Insertar en la tabla interacciones
    sql_interaccion = """
    INSERT INTO `interacciones` (`id_interacciones`, `tipo_interaccion`, `fecha_interaccion`, `id_foto`, `id_usuario`, `nombre_fotografia`, `imagen`)
    VALUES (NULL, 'subida', %s, %s, %s, %s, %s);
    """
    
    # Aquí asumimos que el id_usuario se obtiene de la sesión o de alguna otra manera
    id_usuario = session.get("id_usuario", 1)  # Cambia esto según tu lógica de obtención del id_usuario
    
    datos_interaccion = (_date, id_foto, id_usuario, _nombre, nuevoNombre)
    cursor.execute(sql_interaccion, datos_interaccion)
    
    conexion.commit()
    conexion.close()

    print(_nombre)
    print(_archivo)
    print(_categoria)
    print(_date)

    return redirect('/admin/fotos')

@app.route('/admin/fotos/borrar', methods=['POST'])
def admin_fotos_borrar():
    # Verificar si el usuario está logeado
    if 'login' not in session:
        return redirect("/admin/login")

    # Obtener el id_foto desde el formulario
    _id = request.form.get('txtID')  # Usar .get() para evitar KeyError si el campo no existe
    if not _id:
        return "Error: No se proporcionó el ID de la foto.", 400

    print(f"ID de la foto a borrar: {_id}")

    conexion = None
    cursor = None
    try:
        # Conectar a la base de datos
        conexion = mysql.connection
        cursor = conexion.cursor()

        # Seleccionar la imagen y otros detalles de la foto
        cursor.execute("SELECT imagen, nombre_fotografia FROM `fotos` WHERE id_foto = %s", (_id,))
        foto = cursor.fetchone()  # Obtén la primera fila (la foto)

        if foto:
            imagen, nombre_fotografia = foto

            # Verificar si se encontró la foto y eliminar el archivo
            ruta_imagen = os.path.join("templates/sitio/img/", imagen)
            if os.path.exists(ruta_imagen):
                os.unlink(ruta_imagen)
                print(f"Archivo de imagen borrado: {ruta_imagen}")
            else:
                print(f"Advertencia: El archivo de imagen no existe: {ruta_imagen}")

            # Registrar la interacción de borrado en la tabla interacciones
            sql_interaccion = """
            INSERT INTO `interacciones` (`id_interacciones`, `tipo_interaccion`, `fecha_interaccion`, `id_foto`, `id_usuario`, `nombre_fotografia`, `imagen`)
            VALUES (NULL, 'borrado', NOW(), %s, %s, %s, %s);
            """
            
            # Obtener el id_usuario de la sesión
            id_usuario = session.get("id_usuario")
            if id_usuario is None:
                return "Error: No se ha iniciado sesión.", 401  # Si no hay id_usuario, devolver un error

            # Datos para la inserción en interacciones
            datos_interaccion = (_id, id_usuario, nombre_fotografia, imagen)
            cursor.execute(sql_interaccion, datos_interaccion)
            print(f"Interacción de borrado registrada: ID {_id}")

            # Eliminar la foto de la base de datos
            cursor.execute("DELETE FROM fotos WHERE id_foto = %s", (_id,))
            print(f"Foto borrada de la base de datos: ID {_id}")

            # Confirmar los cambios en la base de datos
            conexion.commit()

        else:
            return "Error: La foto no existe.", 404

    except Exception as e:
        print(f"Error al borrar la foto o registrar la interacción: {e}")
        if conexion:
            conexion.rollback()  # Revertir cambios en caso de error
        return f"Error: {e}", 500

    finally:
        # Cerrar el cursor y la conexión
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()

    return redirect('/admin/fotos')

if __name__ == '__main__':
    app.run(debug=True)

