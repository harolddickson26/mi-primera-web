import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "clave_secreta_super_segura")

# Detectar la base de datos en Render o usar SQLite como respaldo local
db_url = os.environ.get("DATABASE_URL", "sqlite:///" + os.path.join(os.path.abspath(os.path.dirname(__file__)), "inventario.db"))

if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+psycopg://", 1)
elif db_url.startswith("postgresql://") and not db_url.startswith("postgresql+psycopg://"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- MODELOS DE LA BASE DE DATOS ---

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
    fecha_venta = db.Column(db.Date, nullable=False)
    fecha_registro = db.Column(db.DateTime, default=datetime.now)

# Crear o actualizar las tablas en la base de datos de manera segura
with app.app_context():
    db.create_all()
    try:
        # Migración automática para agregar la columna cliente_nombre a la tabla existente si falta
        db.session.execute(text("ALTER TABLE venta ADD COLUMN IF NOT EXISTS cliente_nombre VARCHAR(100);"))
        db.session.commit()
    except Exception:
        db.session.rollback()

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

        cliente_existente = Cliente.query.filter_by(nit_cedula=nit_cedula).first()
        if cliente_existente:
            error = "Ya existe un cliente registrado con ese NIT o Cédula."
        else:
            nuevo = Cliente(nombre=nombre, nit_cedula=nit_cedula, direccion=direccion, email=email, celular=celular)
            db.session.add(nuevo)
            db.session.commit()
            return redirect(url_for("clientes"))
    return render_template("nuevo_cliente.html", error=error)

@app.route("/clientes/editar/<int:id>", methods=["GET", "POST"])
def editar_cliente(id):
    if "usuario" not in session: return redirect(url_for("login"))
    cliente = Cliente.query.get_or_404(id)
    error = None
    if request.method == "POST":
        nit_nuevo = request.form["nit_cedula"]
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

# --- MÓDULO DE PRODUCTOS ---

@app.route("/productos")
def productos():
    if "usuario" not in session: return redirect(url_for("login"))
    lista_productos = Producto.query.order_by(Producto.nombre.asc()).all()
    return render_template("productos.html", productos=lista_productos)

@app.route("/productos/nuevo", methods=["GET", "POST"])
def nuevo_producto():
    if "usuario" not in session: return redirect(url_for("login"))
    error = None
    if request.method == "POST":
        codigo = request.form["codigo"]
        nombre = request.form["nombre"]
        embalaje = request.form["embalaje"]

        producto_existente = Producto.query.filter_by(codigo=codigo).first()
        if producto_existente:
            error = "Ya existe un producto registrado con ese código."
        else:
            nuevo = Producto(codigo=codigo, nombre=nombre, embalaje=embalaje)
            db.session.add(nuevo)
            db.session.commit()
            return redirect(url_for("productos"))
    return render_template("nuevo_producto.html", error=error)

@app.route("/productos/editar/<int:id>", methods=["GET", "POST"])
def editar_producto(id):
    if "usuario" not in session: return redirect(url_for("login"))
    producto = Producto.query.get_or_404(id)
    error = None
    if request.method == "POST":
        codigo_nuevo = request.form["codigo"]
        existente = Producto.query.filter(Producto.codigo == codigo_nuevo, Producto.id != id).first()
        if existente:
            error = "Ese Código de Producto ya pertenece a otro registro."
        else:
            producto.codigo = codigo_nuevo
            producto.nombre = request.form["nombre"]
            producto.embalaje = request.form["embalaje"]
            db.session.commit()
            return redirect(url_for("productos"))
    return render_template("editar_producto.html", producto=producto, error=error)

# --- MÓDULO DE VENTAS ---

@app.route("/ingresar-venta", methods=["GET", "POST"])
def ingresar_venta():
    if "usuario" not in session: return redirect(url_for("login"))
    
    error = None
    if request.method == "POST":
        try:
            cliente_nombre = request.form.get("cliente_nombre", "Público General")
            producto_id = request.form.get("producto_id")
            codigo_producto = request.form["codigo_producto"]
            nombre_producto = request.form["nombre_producto"]
            embalaje = request.form.get("embalaje", "")
            cantidad = float(request.form["cantidad"])
            costo_unitario = float(request.form["costo_unitario"])
            precio_unitario = float(request.form["precio_unitario"])
            total_venta = cantidad * precio_unitario
            total_costo = cantidad * costo_unitario
            fecha_venta_str = request.form["fecha_venta"]
            fecha_venta = datetime.strptime(fecha_venta_str, "%Y-%m-%d").date()

            nueva_venta = Venta(
                cliente_nombre=cliente_nombre,
                producto_id=int(producto_id) if producto_id else None,
                codigo_producto=codigo_producto,
                nombre_producto=nombre_producto,
                embalaje=embalaje,
                cantidad=cantidad,
                costo_unitario=costo_unitario,
                precio_unitario=precio_unitario,
                total_costo=total_costo,
                total_venta=total_venta,
                fecha_venta=fecha_venta
            )
            db.session.add(nueva_venta)
            db.session.commit()
            return redirect(url_for("total_ventas"))
        except Exception as e:
            error = f"Error al registrar la venta: {str(e)}"

    lista_clientes = Cliente.query.order_by(Cliente.nombre.asc()).all()
    lista_productos = Producto.query.order_by(Producto.nombre.asc()).all()
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    return render_template("ingresar_venta.html", clientes=lista_clientes, productos=lista_productos, fecha_hoy=fecha_hoy, error=error)

@app.route("/total-ventas")
def total_ventas():
    if "usuario" not in session: return redirect(url_for("login"))
    
    lista_ventas = Venta.query.order_by(Venta.fecha_venta.desc(), Venta.id.desc()).all()
    
    suma_ventas = sum(v.total_venta for v in lista_ventas)
    suma_costos = sum(v.total_costo for v in lista_ventas)
    utilidad_total = suma_ventas - suma_costos

    return render_template(
        "total_ventas.html", 
        ventas=lista_ventas, 
        suma_ventas=suma_ventas, 
        suma_costos=suma_costos, 
        utilidad_total=utilidad_total
    )

# --- RUTAS RESTANTES ---

@app.route("/inventario")
def inventario():
    if "usuario" not in session: return redirect(url_for("login"))
    return render_template("seccion.html", titulo="Inventario", contenido="Gestión e historial del inventario de productos.")

@app.route("/ingresar-entrada")
def ingresar_entrada():
    if "usuario" not in session: return redirect(url_for("login"))
    return render_template("seccion.html", titulo="Ingresar Entrada", contenido="Registro de nuevas entradas de mercancía.")

@app.route("/utilidad")
def utilidad():
    if "usuario" not in session: return redirect(url_for("login"))
    return render_template("seccion.html", titulo="Utilidad", contenido="Reporte de ganancias y utilidades.")

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
