
import os
from flask import Flask
from flask import render_template, request, redirect, session
from flask_mysqldb import MySQL
from datetime import datetime
from flask import send_from_directory
from datetime import date
from werkzeug.security import check_password_hash

app=Flask(__name__)
app.secret_key="develoteca"
mysql=MySQL()

app.config['MYSQL_DATABASE_HOST']='localhost'
app.config['MYSQL_DATABASE_USER']='root'
app.config['MYSQL_DATABASE_PASSWORD']=''
app.config['MYSQL_DATABASE_DB']='sitio' 
mysql.init_app(app)

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


    conexion = mysql.connect()
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

        # Conectar a la base de datos
        conexion = mysql.connect()
        cursor = conexion.cursor()

        # Ejecuta la consulta para obtener el nombre de usuario y la contraseña desde la tabla de usuarios
        cursor.execute("SELECT nombre_usuario, contraseña FROM usuario WHERE nombre_usuario = %s", (_usuario,))
        usuario = cursor.fetchone()  # Obtén la primera fila (el usuario)

        conexion.close()  # Cierra la conexión a la base de datos

        if usuario:
            print(f"Usuario encontrado: {usuario[0]}")  # Verifica el nombre de usuario
            print(f"Contraseña almacenada: {usuario[1]}")  # Verifica la contraseña almacenada

            # Compara la contraseña almacenada con la ingresada
            if usuario[1].strip() == _password:
                session["login"] = True
                session["usuario"] = usuario[0]  # Asignamos el nombre de usuario a la sesión
                return redirect("/admin")  # Redirige a la página de administración
            else:
                return render_template("admin/login.html", mensaje="Contraseña incorrecta")
        else:
            return render_template("admin/login.html", mensaje="Usuario no encontrado")

    return render_template('admin/login.html')



@app.route('/admin/cerrar') 
def admin_login_cerrar():
        session.clear()
        return redirect('/admin/login')

@app.route('/admin/fotos') 
def admin_fotos():
    if 'login' not in session:
        return redirect("/admin/login")

    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM `fotos`")
    fotos = cursor.fetchall()
    conexion.commit()

    today = date.today().strftime('%Y-%m-%d')  
    
    return render_template("admin/fotos.html", fotos=fotos, today=today)

@app.route('/admin/fotos/guardar', methods=['POST'])
def admin_libros_guardar():
    _nombre=request.form['txtNombre']
    _archivo=request.files['txtImagen']
    _categoria=request.form['txtCategoria']
    _date=request.form['txtDate']

    tiempo=datetime.now()
    horaActual=tiempo.strftime('%Y%H%M%S')

    if _archivo.filename!="":
        nuevoNombre=horaActual+"_"+_archivo.filename
        _archivo.save("templates/sitio/img/"+nuevoNombre)
    

    sql= "INSERT INTO `fotos` (`id_foto`, `nombre_fotografia`, `imagen`, `categoria_fotografia`, `fecha_subida`) VALUES (NULL, %s, %s, %s, %s);"
    datos=(_nombre,nuevoNombre,_categoria,_date )
    conexion = mysql.connect()
    cursor=conexion.cursor()
    cursor.execute(sql,datos)
    conexion.commit()

    
    print(_nombre)
    print(_archivo)
    print(_categoria)
    print(_date)
    
    
    return redirect('/admin/fotos')

@app.route('/admin/fotos/borrar', methods=['POST'])
def admin_fotos_borrar():

    if not 'login' in session:
        return redirect("/admin/login")
    _id=request.form['txtID']
    print(_id)

    conexion=mysql.connect()
    cursor = conexion.cursor()
    cursor.execute("SELECT imagen FROM `fotos` WHERE id_foto= %s", (_id))
    fotos=cursor.fetchall()
    conexion.commit()
    print(fotos)

    if os.path.exists("templates/sitio/img/"+str(fotos[0][0])):
        os.unlink("templates/sitio/img/"+str(fotos[0][0]))

    conexion=mysql.connect()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM fotos WHERE id_foto=%s", (_id))
    conexion.commit()

    return redirect('/admin/fotos')

if __name__ == '__main__':
    app.run(debug=True)

