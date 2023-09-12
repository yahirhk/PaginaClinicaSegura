from flask import Flask, render_template, request, session, url_for, flash, redirect
from flask_mail import Mail, Message
from reportlab.pdfgen import canvas
from flask import send_file
from flask import make_response
from io import BytesIO
import mysql.connector
app = Flask(__name__)
#Esto sirve para al crear la cita se envie un correo
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'yahirrd39@gmail.com' #Aqui tienes que poner el correo desde el que se enviara la informacion de la cita
app.config['MAIL_PASSWORD'] = 'kzxncatiqsofbmxa' #Tienes que crear una contraseña en lo de seguridad de tu cuenta google
mail = Mail(app)

def send_email(subject, recipient, body):
    sender = app.config['MAIL_USERNAME']
    message = Message(subject, sender=sender, recipients=[recipient])
    message.body = body
    mail.send(message)

app.secret_key = 'aries2954013579' #aqui pones cualquier contraseña que quieras

mydb = mysql.connector.connect(
  host="localhost", #host y user no lo cambies son los de defecto para mysql
  user="root",
  password="aries1901", #tu contraseña mysql
  database="clinicasegura" #el nombre que le pongas a la base de datos
)

@app.route("/")
def home():
    return render_template("login.html")

@app.route("/index.html")
def inicio():
    return render_template("index.html")

@app.route("/especialidades.html")
def especialidades():
    return render_template("especialidades.html")

@app.route("/servicios.html")
def servicios():
    return render_template("servicios.html")

@app.route("/citas.html", methods=['GET','POST'])
def citas():
    if request.method == 'POST':
    #obteniendo los datos del formulario
        nombre_completo = request.form['nombre']
        fecha_y_hora = request.form['fecha']
        telefono = request.form['telefono']
        correo_electronico = request.form['correo']
        genero = request.form['genero']
        departamento = request.form['departamento']
        sintomas = request.form['sintomas']

        cursor = mydb.cursor(dictionary=True)
        sql = "INSERT INTO citas (nombre_completo, fecha_y_hora, telefono, correo_electronico, genero, departamento, sintomas) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        val = (nombre_completo, fecha_y_hora, telefono, correo_electronico, genero, departamento, sintomas)
        cursor.execute(sql, val)
        mydb.commit()

        cursor.close()

        # Enviar correo electrónico de confirmación
        subject = 'Cita Registrada'
        recipient = request.form['correo']
        body = 'Tu cita ha sido registrada correctamente.'
        send_email(subject, recipient, body)


    return render_template("citas.html")

# Ruta para mostrar los registros
@app.route("/pacientes.html")
def pacientes():
    cursor = mydb.cursor()
    cursor.execute("SELECT * FROM usuarios")
    data = cursor.fetchall()
    return render_template("pacientes.html", registros=data)

# Ruta para agregar un registro
@app.route('/add', methods=['GET','POST'])
def add():
    cursor = mydb.cursor()

    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']
        nombre = request.form['nombre']
        apellido = request.form['apellido']
    
        cursor.execute("INSERT INTO usuarios (login, password, nombre, apellido) VALUES (%s, %s, %s, %s)", (login, password, nombre, apellido))
        mydb.commit()
        return redirect('pacientes.html')
    return render_template('add.html')

# Ruta para editar un registro
@app.route('/edit/<id>', methods=['POST', 'GET'])
def edit(id):
    cursor = mydb.cursor()
    if request.method == 'GET':
        cursor.execute("SELECT * FROM usuarios WHERE id = %s", (id,))
        data = cursor.fetchone()
        return render_template('edit.html', registro=data)
    else:
        login = request.form['login']
        password = request.form['password']
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        cursor.execute("UPDATE usuarios SET login = %s, password = %s, nombre = %s, apellido = %s WHERE id = %s", (login, password, nombre, apellido, id))
        mydb.commit()
        return redirect('pacientes.html')

# Ruta para eliminar un registro
@app.route('/delete/<int:id>', methods=['POST', 'GET'])
def delete(id):
    cursor = mydb.cursor()
    cursor.execute("DELETE FROM usuarios WHERE id = %s", (id,))
    mydb.commit()
    return redirect(url_for('pacientes'))

#Ruta para descargar el pdf
@app.route('/pdf/<int:id>')
def pdf(id):
    cursor = mydb.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE id = %s", (id,))
    data = cursor.fetchone()

    # Generar el contenido del PDF
    buffer = BytesIO()
    p = canvas.Canvas(buffer)
    p.drawString(100, 700, f"Usuario: {data[1]}")
    p.drawString(100, 650, f"Contraseña: {data[2]}")
    p.drawString(100, 600, f"Nombre: {data[3]}")
    p.drawString(100, 550, f"Apellidos: {data[4]}")
    p.showPage()
    p.save()

    # Generar la respuesta HTTP con el PDF
    buffer.seek(0)
    response = make_response(buffer.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=usuario_{id}.pdf'
    return response

#Buscador para pacientes-----------------------------------------
@app.route('/search', methods=['POST'])
def search():
    query = request.form['query']

    cursor = mydb.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE nombre LIKE %s OR apellido LIKE %s OR id LIKE %s", (f'%{query}%', f'%{query}%', f'%{query}%'))
    patients = cursor.fetchall()

    insertObject = []
    columnNames = [column[0] for column in cursor.description]
    for record in patients:
        insertObject.append(dict(zip(columnNames, record)))
    cursor.close()

    cursor.close()

    return render_template('pacientes.html', patients=insertObject)


@app.route("/contactanos.html")
def contactanos():
    return render_template("contactanos.html")

#Conexion de base de datos
@app.route('/login', methods = ['GET','POST'])
def login():
    if mydb is None:
        return render_template('/login.html', mensaje='Error al conectarse a la base de datos')
    

    login = request.form['username']
    password = request.form['password']

    try:
        mycursor = mydb.cursor()

        mycursor.execute("SELECT * FROM usuarios WHERE login = %s AND password = %s", (login, password))

        usuario = mycursor.fetchone()

        if usuario:
                session['username'] = login # Almacenar el nombre de usuario en la sesión
                return render_template('/index.html', correcta = 'Has iniciado sesión correctamente')
        else:
           
            # Nombre de usuario o contraseña incorrectos
            return render_template('/login.html', error='Nombre de usuario o contraseña incorrectos')

    except mysql.connector.Error as error:
        print("Error al ejecutar la consulta a la base de datos: {}".format(error))
        return render_template('/login.html', error='Error al ejecutar la consulta a la base de datos')


@app.route('/registro.html', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        # Aquí es donde se procesa el formulario de registro y se guardan los datos en la base de datos
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        correo = request.form['email']
        contrasena = request.form['password']
        
        # Aquí se insertan los datos en la tabla "usuarios"
        cursor = mydb.cursor()
        sql = "INSERT INTO usuarios (nombre, apellido, login, password) VALUES (%s, %s, %s, %s)"
        val = (nombre, apellido, correo, contrasena)
        cursor.execute(sql, val)
        mydb.commit()
        cursor.close()
        
    return render_template('/registro.html')


if __name__ == "__main__":
    app.run( debug=True, port=4000, host="0.0.0.0")
