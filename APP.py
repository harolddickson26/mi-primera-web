import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "clave_secreta_super_segura")

# Detectar la base de datos en Render o usar SQLite como respaldo local
db_url = os.environ.get("DATABASE_URL", "sqlite:///" + os.path.join(os.path.abspath(os.path.dirname(__file__)), "inventario.db"))

# Asegurar el uso del driver psycopg (psycopg3) para SQLAlchemy 2.x
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+psycopg://", 1)
elif db_url.startswith("postgresql://") and not db_url.startswith("postgresql+psycopg://"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Modelo para la tabla de Clientes
class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    nit_cedula = db.Column(db.String(50), nullable=False, unique=True)
    direccion = db.Column(db.String(200), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    celular = db.Column(db.String(50), nullable=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.now)

# Crear la base de datos y las tablas al iniciar la aplicación
with app.app_context():
    db.create_all()

# Credenciales de prueba
USUARIO_CORRECTO = "DICKSON"
PASSWORD_CORRECTO = "1234"

@app.route("/")
def inicio():
    if "usuario" in session:
        return render_template("index.html", usuario=session["usuario"])
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        usuario_ingresado = request.form["username"]
        password_ingresado = request.form["password"]

        if usuario_ingresado == USUARIO_CORRECTO and password_ingresado == PASSWORD_CORRECTO:
            session["usuario"] = usuario_ingresado
            return redirect(url_for("inicio"))
        else:
            error = "Usuario o contraseña incorrectos."

    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.pop("usuario", None)
    return redirect(url_for("login"))

# --- MÓDULO DE CLIENTES ---

@app.route("/clientes")
def clientes():
    if "usuario" not in session: 
        return redirect(url_for("login"))
    # Ordenar por nombre alfabéticamente
    lista_clientes = Cliente.query.order_by(Cliente.nombre.asc()).all()
    return render_template("clientes.html", clientes=lista_clientes)

@app.route("/clientes/nuevo", methods=["GET", "POST"])
def nuevo_cliente():
    if "usuario" not in session: 
        return redirect(url_for("login"))
    
    error = None
    if request.method == "POST":
        nombre = request.form["nombre"]
        nit_cedula = request.form["nit_cedula"]
        direccion = request.form["direccion"]
        email = request.form["email"]
        celular = request.form["celular"]

        cliente_existente = Cliente.query.filter_by(nit_cedula=nit_cedula).first()
        if cliente_existente:
            error = "Ya existe un cliente registrado con ese NIT o Cédula."
        else:
            nuevo = Cliente(
                nombre=nombre,
                nit_cedula=nit_cedula,
                direccion=direccion,
                email=email,
                celular=celular
            )
            db.session.add(nuevo)
            db.session.commit()
            return redirect(url_for("clientes"))

    return render_template("nuevo_cliente.html", error=error)

@app.route("/clientes/editar/<int:id>", methods=["GET", "POST"])
def editar_cliente(id):
    if "usuario" not in session: 
        return redirect(url_for("login"))
    
    cliente = Cliente.query.get_or_404(id)
    error = None

    if request.method == "POST":
        nit_nuevo = request.form["nit_cedula"]
        
        # Validar si cambió el NIT y si pertenece a otro cliente registrado
        existente = Cliente.query.filter(Cliente.nit_cedula == nit_nuevo, Cliente.id != id).first()
        if existente:
            error = "Ese NIT o Cédula ya está registrado en otro cliente."
        else:
            cliente.nombre = request.form["nombre"]
            cliente.nit_cedula = nit_nuevo
            cliente.direccion = request.form["direccion"]
            cliente.email = request.form["email"]
            cliente.celular = request.form["celular"]
            
            db.session.commit()
            return redirect(url_for("clientes"))

    return render_template("editar_cliente.html", cliente=cliente, error=error)

# --- RUTAS RESTANTES DE SECCIONES ---

@app.route("/inventario")
def inventario():
    if "usuario" not in session: return redirect(url_for("login"))
    return render_template("seccion.html", titulo="Inventario", contenido="Gestión e historial del inventario de productos.")

@app.route("/ingresar-entrada")
def ingresar_entrada():
    if "usuario" not in session: return redirect(url_for("login"))
    return render_template("seccion.html", titulo="Ingresar Entrada", contenido="Registro de nuevas entradas de mercancía.")

@app.route("/ingresar-venta")
def ingresar_venta():
    if "usuario" not in session: return redirect(url_for("login"))
    return render_template("seccion.html", titulo="Ingresar Venta", contenido="Registro de nuevas ventas.")

@app.route("/utilidad")
def utilidad():
    if "usuario" not in session: return redirect(url_for("login"))
    return render_template("seccion.html", titulo="Utilidad", contenido="Reporte de ganancias y utilidades.")

@app.route("/total-ventas")
def total_ventas():
    if "usuario" not in session: return redirect(url_for("login"))
    return render_template("seccion.html", titulo="Total Ventas", contenido="Resumen total del volumen de ventas.")

@app.route("/total-entradas")
def total_entradas():
    if "usuario" not in session: return redirect(url_for("login"))
    return render_template("seccion.html", titulo="Total Entradas", contenido="Resumen total de las entradas registradas.")

@app.route("/ABONOS")
def ABONOS():
    if "usuario" not in session: return redirect(url_for("login"))
    return render_template("seccion.html", titulo="Total Abonos", contenido="Resumen total de los abonos registrados.")

if __name__ == "__main__":
    app.run(debug=True)
