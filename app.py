from flask import Flask, render_template, request, redirect, url_for, session, flash
from pymongo import MongoClient
from bson import ObjectId

app = Flask(__name__)
app.secret_key = "clave_super_secreta"

app = Flask(__name__, template_folder="walmart_flask_app/templates", static_folder="walmart_flask_app/static")


# ------------------ CONEXIÓN A MONGODB ------------------
client = MongoClient("mongodb+srv://walmart:123456789@cluster0.eqregid.mongodb.net/walmart")
db = client["walmart"]
usuarios = db["usuarios"]
productos = db["productos"]

# ---------------------------------------------------------
# LOGIN
# ---------------------------------------------------------
@app.route("/", methods=["GET", "POST"])
def login():
    mensaje = ""
    if request.method == "POST":
        usuario = request.form["usuario"].strip()
        contrasena = request.form["contrasena"].strip()

        user = usuarios.find_one({"usuario": usuario})
        if user:
            if user["contrasena"] == contrasena:
                session["usuario"] = usuario
                session["carrito"] = []  # inicializar carrito vacío
                return redirect(url_for("inicio"))
            else:
                mensaje = "⚠️ Contraseña incorrecta"
        else:
            mensaje = "⚠️ Usuario no encontrado"

    return render_template("login.html", mensaje=mensaje)

# ---------------------------------------------------------
# ---------------------------------------------------------
# REGISTRO DE USUARIOS
# ---------------------------------------------------------
@app.route("/registro", methods=["GET", "POST"])
def registro():
    mensaje = ""
    if request.method == "POST":
        usuario = request.form["usuario"].strip()
        contrasena = request.form["contrasena"].strip()
        confirmar = request.form["confirmar"].strip()

        if not usuario or not contrasena or not confirmar:
            mensaje = "Por favor completa todos los campos."
        elif contrasena != confirmar:
            mensaje = "Las contraseñas no coinciden."
        elif usuarios.find_one({"usuario": usuario}):
            mensaje = "Este nombre de usuario ya existe."
        else:
            usuarios.insert_one({
                "usuario": usuario,
                "contrasena": contrasena
            })
            mensaje = "✅ Registro exitoso. Ahora puedes iniciar sesión."
            return redirect(url_for("login"))

    return render_template("registro.html", mensaje=mensaje)


# ---------------------------------------------------------
# INICIO (LISTA DE PRODUCTOS)
# ---------------------------------------------------------
@app.route("/inicio")
def inicio():
    if "usuario" not in session:
        return redirect(url_for("login"))

    productos_list = list(productos.find())

    if not productos_list:
        flash("No hay productos en la base de datos aún.", "info")

    return render_template("inicio.html", productos=productos_list, usuario=session["usuario"])

# ---------------------------------------------------------
# DETALLE DE PRODUCTO
# ---------------------------------------------------------
@app.route("/producto/<producto_id>")
def producto_detalle(producto_id):
    if "usuario" not in session:
        return redirect(url_for("login"))

    producto = productos.find_one({"_id": ObjectId(producto_id)})

    if not producto:
        return "Producto no encontrado", 404

    return render_template("producto.html", producto=producto, usuario=session["usuario"])


# ---------------------------------------------------------
# AGREGAR AL CARRITO
# ---------------------------------------------------------
@app.route("/agregar_carrito/<producto_id>", methods=["POST"])
def agregar_carrito(producto_id):
    if "usuario" not in session:
        return redirect(url_for("login"))

    producto = productos.find_one({"_id": ObjectId(producto_id)})
    if not producto:
        flash("Producto no encontrado.", "danger")
        return redirect(url_for("inicio"))

    carrito = session.get("carrito", [])

    for item in carrito:
        if item["_id"] == str(producto["_id"]):
            item["cantidad"] += 1
            break
    else:
        carrito.append({
            "_id": str(producto["_id"]),
            "name": producto["name"],
            "price": producto["price"],
            "img": producto.get("img", "https://via.placeholder.com/200"),
            "cantidad": 1
        })

    session["carrito"] = carrito
    flash(f"✅ {producto['name']} agregado al carrito.", "success")
    return redirect(url_for("carrito"))  # ✅ redirige directamente al carrito

# ---------------------------------------------------------
# VER CARRITO
# ---------------------------------------------------------
@app.route("/carrito")
def carrito():
    if "usuario" not in session:
        return redirect(url_for("login"))

    carrito = session.get("carrito", [])
    total = sum(item["price"] * item["cantidad"] for item in carrito)
    return render_template("carrito.html", carrito=carrito, total=total, usuario=session["usuario"])

# ---------------------------------------------------------
# ELIMINAR PRODUCTO DEL CARRITO
# ---------------------------------------------------------
@app.route("/eliminar_carrito/<producto_id>", methods=["POST"])
def eliminar_carrito(producto_id):
    carrito = session.get("carrito", [])
    carrito = [item for item in carrito if item["_id"] != producto_id]
    session["carrito"] = carrito
    flash("🗑️ Producto eliminado del carrito.", "warning")
    return redirect(url_for("carrito"))

# ---------------------------------------------------------
# VACIAR CARRITO
# ---------------------------------------------------------
@app.route("/vaciar_carrito", methods=["POST"])
def vaciar_carrito():
    session["carrito"] = []
    flash("🛒 Carrito vaciado correctamente.", "info")
    return redirect(url_for("carrito"))

# ---------------------------------------------------------
# LOGOUT
# ---------------------------------------------------------
@app.route("/logout")
def logout():
    session.clear()
    flash("👋 Sesión cerrada correctamente.", "info")
    return redirect(url_for("login"))

# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
