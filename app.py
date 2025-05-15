from flask import Flask, render_template_string, request, redirect, session, url_for
import sqlite3

app = Flask(__name__)
app.secret_key = 'clave_secreta_segura'
DB_NAME = 'operaciones.db'

# Inicialización base de datos
def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                rol TEXT NOT NULL
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
                usuario_id INTEGER
            )
        ''')
        c.execute("SELECT * FROM usuarios WHERE username = 'admin'")
        if not c.fetchone():
            c.execute("INSERT INTO usuarios (username, password, rol) VALUES (?, ?, ?)", ('admin', 'admin', 'admin'))
        conn.commit()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT id, username, rol FROM usuarios WHERE username=? AND password=?", (username, password))
            user = c.fetchone()
        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['rol'] = user[2]
            return redirect(url_for('index'))
        else:
            return "Credenciales incorrectas"
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@app.route('/index')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    return f'''
    <h2>Bienvenido, {session['username']} (Rol: {session['rol']})</h2>
    <ul>
        <li><a href="/add">➕ Agregar operación</a></li>
        {'<li><a href="/admin/usuarios">👥 Gestión de usuarios</a></li>' if session.get("rol") == "admin" else ''}
        <li><a href="/logout">🔒 Cerrar sesión</a></li>
    </ul>
    '''

@app.route('/add', methods=['GET', 'POST'])
def add():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        def sf(v): return float(v) if v else 0.0
        data = (
            request.form['fecha'],
            request.form['cliente'],
            request.form['vendedor'],
            request.form['modelo_vehiculo'],
            request.form['version'],
            sf(request.form['precio_catalogo']),
            sf(request.form['precio_transporte']),
            sf(request.form['promo1']),
            sf(request.form['promo2']),
            sf(request.form['promo3']),
            session['user_id']
        )
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute('''INSERT INTO operaciones 
                (fecha, cliente, vendedor, modelo_vehiculo, version, precio_catalogo, 
                 precio_transporte, promo1, promo2, promo3, usuario_id)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', data)
            conn.commit()
        return redirect('/')
    return '''
    <h2>Agregar Operación</h2>
    <form method="post">
        Fecha: <input name="fecha"><br>
        Cliente: <input name="cliente"><br>
        Vendedor: <input name="vendedor"><br>
        Modelo Vehículo: <input name="modelo_vehiculo"><br>
        Versión: <input name="version"><br>
        Precio Catálogo: <input name="precio_catalogo"><br>
        Precio Transporte: <input name="precio_transporte"><br>
        Promo1: <input name="promo1"><br>
        Promo2: <input name="promo2"><br>
        Promo3: <input name="promo3"><br>
        <input type="submit" value="Guardar">
    </form>
    <a href="/">⬅ Volver</a>
    '''

# Gestión de usuarios
@app.route('/admin/usuarios')
def admin_usuarios():
    if session.get("rol") != "admin":
        return redirect(url_for('index'))
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("SELECT id, username, rol FROM usuarios")
        users = c.fetchall()
    return render_template_string(USERS_TEMPLATE, users=users)

@app.route('/admin/usuarios/editar/<int:user_id>', methods=['GET', 'POST'])
def editar_usuario(user_id):
    if session.get("rol") != "admin":
        return redirect(url_for('index'))
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        if request.method == 'POST':
            c.execute("UPDATE usuarios SET username=?, rol=? WHERE id=?", (
                request.form['username'], request.form['rol'], user_id))
            conn.commit()
            return redirect(url_for('admin_usuarios'))
        c.execute("SELECT username, rol FROM usuarios WHERE id=?", (user_id,))
        user = c.fetchone()
    return f'''
    <h2>Editar Usuario</h2>
    <form method="post">
        Nombre: <input name="username" value="{user[0]}"><br>
        Rol: 
        <select name="rol">
            <option value="admin" {"selected" if user[1]=="admin" else ""}>admin</option>
            <option value="usuario" {"selected" if user[1]=="usuario" else ""}>usuario</option>
        </select><br>
        <input type="submit" value="Actualizar">
    </form>
    <a href="/admin/usuarios">⬅ Volver</a>
    '''

@app.route('/admin/usuarios/borrar/<int:user_id>')
def borrar_usuario(user_id):
    if session.get("rol") != "admin":
        return redirect(url_for('index'))
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM usuarios WHERE id=?", (user_id,))
        conn.commit()
    return redirect(url_for('admin_usuarios'))

# Plantillas HTML
LOGIN_TEMPLATE = '''
<h2>Iniciar Sesión</h2>
<form method="post">
  Usuario: <input type="text" name="username"><br>
  Contraseña: <input type="password" name="password"><br>
  <input type="submit" value="Entrar">
</form>
'''

USERS_TEMPLATE = '''
<h2>👥 Gestión de Usuarios</h2>
<table border=1>
<tr><th>ID</th><th>Nombre</th><th>Rol</th><th>Acciones</th></tr>
{% for u in users %}
<tr>
  <td>{{ u[0] }}</td>
  <td>{{ u[1] }}</td>
  <td>{{ u[2] }}</td>
  <td>
    <a href="/admin/usuarios/editar/{{ u[0] }}">✏️ Editar</a> |
    <a href="/admin/usuarios/borrar/{{ u[0] }}">🗑️ Borrar</a>
  </td>
</tr>
{% endfor %}
</table>
<br><a href="/">⬅ Volver</a>
'''

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=10000)
