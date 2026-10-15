import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "clave_secreta_super_segura")

db_url = os.environ.get("DATABASE_URL", "sqlite:///" + os.path.join(os.path.abspath(os.path.dirname(__file__)), "inventario.db"))

if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+psycopg://", 1)
elif db_url.startswith("postgresql://") and not db_url.startswith("postgresql+psycopg://"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ==========================================
# MODELOS DE LA BASE DE DATOS
# ==========================================

class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    nit_cedula = db.Column(db.String(50), nullable=False, unique=True)
    direccion = db.Column(db.String(200), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    celular = db.Column(db.String(50), nullable=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.now)

class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), nullable=False, unique=True)
    nombre = db.Column(db.String(150), nullable=False)
    embalaje = db.Column(db.String(100), nullable=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.now)

class Venta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cliente_nombre = db.Column(db.String(100), nullable=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'), nullable=True)
    codigo_producto = db.Column(db.String(50), nullable=False)
    nombre_producto = db.Column(db.String(150), nullable=False)
    embalaje = db.Column(db.String(100), nullable=True)
    cantidad = db.Column(db.Float, nullable=False)
    costo_unitario = db.Column(db.Float, nullable=False)
    precio_unitario = db.Column(db.Float, nullable=False)
    total_costo = db.Column(db.Float, nullable=False)
    total_venta = db.Column(db.Float, nullable=False)
    tipo_pago = db.Column(db.String(50), nullable=True)
    entidad_pago = db.Column(db.String(100), nullable=True)
    fecha_venta = db.Column(db.Date, nullable=False)
    fecha_registro = db.Column(db.DateTime, default=datetime.now)

class Entrada(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date, nullable=False)
    proveedor = db.Column(db.String(150), nullable=True)
    factura = db.Column(db.String(100), nullable=True)
    codigo = db.Column(db.String(50), nullable=True)
    producto = db.Column(db.String(150), nullable=True)
    embalaje = db.Column(db.String(100), nullable=True)
    cant_paquetes = db.Column(db.Float, default=0.0)
    cant_unidades = db.Column(db.Float, default=0.0)
    costo = db.Column(db.Float, default=0.0)
    costo_iva = db.Column(db.Float, default=0.0)
    costo_unit_placa = db.Column(db.Float, default=0.0)
    costo_unit_paca = db.Column(db.Float, default=0.0)
    costo_total = db.Column(db.Float, default=0.0)
    costo_unitario = db.Column(db.Float, default=0.0)
    precio_sugerido = db.Column(db.Float, default=0.0)
    costo_x_cantidad = db.Column(db.Float, default=0.0)
    costo_total_final = db.Column(db.Float, default=0.0)
    fecha_registro = db.Column(db.DateTime, default=datetime.now)

class Abono(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date, nullable=False)
    cliente = db.Column(db.String(100), nullable=False)
    total_abono = db.Column(db.Float, nullable=False)
    medio_abono = db.Column(db.String(50), nullable=False)
    fecha_registro = db.Column(db.DateTime, default=datetime.now)

# Migraciones automáticas de columnas en Postgres / SQLite
with app.app_context():
    db.create_all()
    try:
        db.session.execute(text("ALTER TABLE venta ADD COLUMN IF NOT EXISTS cliente_nombre VARCHAR(100);"))
        db.session.execute(text("ALTER TABLE venta ADD COLUMN IF NOT EXISTS tipo_pago VARCHAR(50);"))
        db.session.execute(text("ALTER TABLE venta ADD COLUMN IF NOT EXISTS entidad_pago VARCHAR(100);"))
        db.session.commit()
    except Exception:
        db.session.rollback()

USUARIO_CORRECTO = "DICKSON"
PASSWORD_CORRECTO = "1234"

# ==========================================
# RUTAS DE AUTENTICACIÓN
# ==========================================

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

# ==========================================
# MÓDULO CLIENTES
# ==========================================

@app.route("/clientes")
def clientes():
    if "usuario" not in session: return redirect(url_for("login"))
    lista_clientes = Cliente.query.order_by(Cliente.nombre.asc()).all()
    return render_template("clientes.html", clientes=lista_clientes)

@app.route("/clientes/nuevo", methods=["GET", "POST"])
def nuevo_cliente():
    if "usuario" not in session: return redirect(url_for("login"))
    error = None
    if request.method == "POST":
        nombre = request.form["nombre"]
        nit_cedula = request.form["nit_cedula"]
        direccion = request.form["direccion"]
        email = request.form["email"]
        celular = request.form["celular"]

        cliente_existente = Cliente.query.filter_by(nit_cedula=nit_
