from flask import Flask, render_template_string, request, redirect, session, url_for
import sqlite3

app = Flask(__name__)
app.secret_key = 'clave_secreta_segura'

DB_NAME = 'operaciones.db'

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS operaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT,
                cliente TEXT,
                vendedor TEXT,
                modelo_vehiculo TEXT,
                version TEXT,
                precio_catalogo REAL,
                precio_transporte REAL,
                promo1 REAL,
                promo2 REAL,
                promo3 REAL,
                usuario_id INTEGER,
                FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
            )
        ''')
        c.execute("INSERT OR IGNORE INTO usuarios (username, password) VALUES (?, ?)", ('admin', 'admin'))
        conn.commit()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT id FROM usuarios WHERE username=? AND password=?", (username, password))
            user = c.fetchone()
            if user:
                session['user_id'] = user[0]
                return redirect(url_for('index'))
            else:
                return "Credenciales incorrectas"
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM operaciones WHERE usuario_id=?", (session['user_id'],))
        operaciones = c.fetchall()
    return render_template_string(TEMPLATE, operaciones=operaciones)

@app.route('/add', methods=['POST'])
def add():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    def safe_float(value):
        try:
            return float(value)
        except ValueError:
            return 0.0

    data = (
        request.form['fecha'],
        request.form['cliente'],
        request.form['vendedor'],
        request.form['modelo_vehiculo'],
        request.form['version'],
        safe_float(request.form['precio_catalogo']),
        safe_float(request.form['precio_transporte']),
        safe_float(request.form['promo1']),
        safe_float(request.form['promo2']),
        safe_float(request.form['promo3']),
        session['user_id']
    )
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("""
            INSERT INTO operaciones (fecha, cliente, vendedor, modelo_vehiculo, version, 
                                     precio_catalogo, precio_transporte, promo1, promo2, promo3, usuario_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, data)
        conn.commit()
    return redirect('/')

LOGIN_TEMPLATE = '''
<!doctype html>
<title>Login</title>
<h2>Iniciar Sesión</h2>
<form method="post">
  Usuario: <input type="text" name="username"><br>
  Contraseña: <input type="password" name="password"><br>
  <input type="submit" value="Entrar">
</form>
'''

TEMPLATE = '''
<!doctype html>
<title>Operaciones</title>
<a href="/logout">Cerrar sesión</a>
<h2>Agregar Operación</h2>
<form method=post action="/add">
  Fecha: <input type=text name=fecha><br>
  Cliente: <input type=text name=cliente><br>
  Vendedor: <input type=text name=vendedor><br>
  Modelo Vehículo: <input type=text name=modelo_vehiculo><br>
  Versión: <input type=text name=version><br>
  Precio Catálogo: <input type=number step=0.01 name=precio_catalogo><br>
  Precio Transporte: <input type=number step=0.01 name=precio_transporte><br>
  Promo1: <input type=number step=0.01 name=promo1><br>
  Promo2: <input type=number step=0.01 name=promo2><br>
  Promo3: <input type=number step=0.01 name=promo3><br>
  <input type=submit value="Guardar">
</form>
<h2>Operaciones Registradas</h2>
<table border=1>
<tr><th>ID</th><th>Fecha</th><th>Cliente</th><th>Vendedor</th><th>Modelo</th><th>Versión</th><th>Precio Catálogo</th><th>Precio Transporte</th><th>Promo1</th><th>Promo2</th><th>Promo3</th></tr>
{% for op in operaciones %}
<tr>{% for item in op[:-1] %}<td>{{ item }}</td>{% endfor %}</tr>
{% endfor %}
</table>
'''

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=10000)

