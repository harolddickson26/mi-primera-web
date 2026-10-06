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

# ==========================================
# MÓDULO PRODUCTOS
# ==========================================

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

# ==========================================
# MÓDULO VENTAS
# ==========================================

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
            
            tipo_pago = request.form.get("tipo_pago", "CONTADO")
            if tipo_pago == "CREDITO":
                entidad_pago = None
            else:
                entidad_pago = request.form.get("entidad_pago", "Efectivo")

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
                tipo_pago=tipo_pago,
                entidad_pago=entidad_pago,
                fecha_venta=fecha_venta
            )
            db.session.add(nueva_venta)
            db.session.commit()
            return redirect(url_for("total_ventas"))
        except Exception as e:
            db.session.rollback()
            error = f"Error al registrar la venta: {str(e)}"

    lista_clientes = Cliente.query.order_by(Cliente.nombre.asc()).all()
    lista_productos = Producto.query.order_by(Producto.nombre.asc()).all()
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    return render_template("ingresar_venta.html", clientes=lista_clientes, productos=lista_productos, fecha_hoy=fecha_hoy, error=error)

@app.route("/ventas/editar/<int:id>", methods=["GET", "POST"])
def editar_venta(id):
    if "usuario" not in session: 
        return redirect(url_for("login"))
    
    venta = Venta.query.get_or_404(id)
    error = None

    if request.method == "POST":
        try:
            venta.cliente_nombre = request.form.get("cliente_nombre", "Público General")
            producto_id = request.form.get("producto_id")
            if producto_id:
                venta.producto_id = int(producto_id)
            
            venta.codigo_producto = request.form["codigo_producto"]
            venta.nombre_producto = request.form["nombre_producto"]
            venta.embalaje = request.form.get("embalaje", "")
            venta.cantidad = float(request.form["cantidad"])
            venta.costo_unitario = float(request.form["costo_unitario"])
            venta.precio_unitario = float(request.form["precio_unitario"])
            venta.total_venta = venta.cantidad * venta.precio_unitario
            venta.total_costo = venta.cantidad * venta.costo_unitario
            
            nuevo_tipo = request.form.get("tipo_pago", "CONTADO")
            venta.tipo_pago = nuevo_tipo
            
            if nuevo_tipo == "CREDITO":
                venta.entidad_pago = None
            else:
                venta.entidad_pago = request.form.get("entidad_pago", "Efectivo")

            fecha_venta_str = request.form["fecha_venta"]
            venta.fecha_venta = datetime.strptime(fecha_venta_str, "%Y-%m-%d").date()

            db.session.commit()
            return redirect(url_for("total_ventas"))
        except Exception as e:
            db.session.rollback()
            error = f"Error al actualizar la venta: {str(e)}"

    lista_clientes = Cliente.query.order_by(Cliente.nombre.asc()).all()
    lista_productos = Producto.query.order_by(Producto.nombre.asc()).all()
    return render_template("editar_venta.html", venta=venta, clientes=lista_clientes, productos=lista_productos, error=error)

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

# ==========================================
# MÓDULO ENTRADAS
# ==========================================

@app.route("/total-entradas")
def total_entradas():
    if "usuario" not in session: return redirect(url_for("login"))
    
    lista_entradas = Entrada.query.order_by(Entrada.fecha.desc(), Entrada.id.desc()).all()
    
    total_registros = len(lista_entradas)
    suma_costos_total = sum(e.costo_total_final or e.costo_total or 0 for e in lista_entradas)
    suma_unidades = sum(e.cant_unidades or 0 for e in lista_entradas)

    return render_template(
        "total_entradas.html",
        entradas=lista_entradas,
        total_registros=total_registros,
        suma_costos_total=suma_costos_total,
        suma_unidades=suma_unidades
    )

@app.route("/ingresar-entrada", methods=["GET", "POST"])
def ingresar_entrada():
    if "usuario" not in session: return redirect(url_for("login"))
    
    if request.method == "POST":
        try:
            data = request.get_json()
            fecha_str = data.get("fecha")
            fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
            proveedor = data.get("proveedor", "")
            factura = data.get("factura", "")
            items = data.get("items", [])
            
            if not items:
                return {"success": False, "error": "Debe agregar al menos un producto."}, 400

            import re
            for item in items:
                codigo = item.get("codigo")
                producto = item.get("producto")
                embalaje_str = item.get("embalaje", "1")
                
                match = re.search(r'(\d+[\.,]?\d*)', embalaje_str)
                factor_embalaje = float(match.group(1).replace(',', '.')) if match else 1.0

                cant_paquetes = float(item.get("cant_paquetes", 0))
                cant_unidades = cant_paquetes * factor_embalaje
                
                costo = float(item.get("costo", 0))
                tipo_iva = item.get("tipo_iva", "sin_iva")
                
                if tipo_iva == "sin_iva":
                    costo_iva = costo * 1.19
                    costo_unit_placa = costo * 1.19
                    costo_unit_paca = costo * 1.19
                else:
                    costo_iva = costo
                    costo_unit_placa = costo
                    costo_unit_paca = costo
                    
                costo_total = cant_paquetes * costo_unit_paca
                costo_unitario = (costo_total / cant_unidades) if cant_unidades > 0 else 0
                precio_sugerido = costo_unit_paca * 1.10
                
                nueva_entrada = Entrada(
                    fecha=fecha,
                    proveedor=proveedor,
                    factura=factura,
                    codigo=codigo,
                    producto=producto,
                    embalaje=embalaje_str,
                    cant_paquetes=cant_paquetes,
                    cant_unidades=cant_unidades,
                    costo=costo,
                    costo_iva=costo_iva,
                    costo_unit_placa=costo_unit_placa,
                    costo_unit_paca=costo_unit_paca,
                    costo_total=costo_total,
                    costo_unitario=costo_unitario,
                    precio_sugerido=precio_sugerido,
                    costo_x_cantidad=costo_total,
                    costo_total_final=costo_total
                )
                db.session.add(nueva_entrada)
            
            db.session.commit()
            return {"success": True, "redirect": url_for("total_entradas")}
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}, 400

    lista_productos = Producto.query.order_by(Producto.nombre.asc()).all()
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    return render_template("ingresar_entrada.html", productos=lista_productos, fecha_hoy=fecha_hoy)

# ==========================================
# RUTAS AUXILIARES / PENDIENTES
# ==========================================

@app.route("/inventario")
def inventario():
    if "usuario" not in session: return redirect(url_for("login"))
    return render_template("seccion.html", titulo="Inventario", contenido="Gestión e historial del inventario de productos.")

@app.route("/utilidad")
def utilidad():
    if "usuario" not in session: return redirect(url_for("login"))
    return render_template("seccion.html", titulo="Utilidad", contenido="Reporte de ganancias y utilidades.")

@app.route("/ABONOS")
def ABONOS():
    if "usuario" not in session: return redirect(url_for("login"))
    return render_template("seccion.html", titulo="Total Abonos", contenido="Resumen total de los abonos registrados.")

if __name__ == "__main__":
    app.run(debug=True)
