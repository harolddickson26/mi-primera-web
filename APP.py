from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
# Clave secreta requerida por Flask para manejar sesiones seguras
app.secret_key = "clave_secreta_super_segura"

# Credenciales de prueba
USUARIO_CORRECTO = "DianaPaulina"
PASSWORD_CORRECTO = "3127835548"

@app.route("/")
def inicio():
    # Si el usuario ya inició sesión, muestra la página principal
    if "usuario" in session:
        return render_template("index.html", usuario=session["usuario"])
    # Si no ha iniciado sesión, redirige al login
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

if __name__ == "__main__":
    app.run(debug=True)