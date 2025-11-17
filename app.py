from flask import Flask, render_template, request, redirect, url_for, session, flash 
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime

app = Flask(__name__, template_folder='flask_mongo_crud_alumnos/templates')
app.secret_key = "clave_super_secreta"

# ------------------ CONEXIÓN A MONGODB ------------------
client = MongoClient("mongodb+srv://walmart:go2675566a@cluster0.eqregid.mongodb.net/walmart")
db = client["walmart"]
usuarios = db["usuarios"]
productos = db["productos"]
pagos = db["pagos"]

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
                session["carrito"] = []
                return redirect(url_for("inicio"))
            else:
                mensaje = "⚠️ Contraseña incorrecta"
        else:
            mensaje = "⚠️ Usuario no encontrado"

    return render_template("login.html", mensaje=mensaje)

# ---------------------------------------------------------
# REGISTRO
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
            return redirect(url_for("login"))

    return render_template("registro.html", mensaje=mensaje)

# ---------------------------------------------------------
# INICIO - LISTA DE PRODUCTOS
# ---------------------------------------------------------
@app.route("/inicio")
def inicio():
    if "usuario" not in session:
        return redirect(url_for("login"))

    productos_list = list(productos.find())
    return render_template("inicio.html", productos=productos_list, usuario=session["usuario"])

# ---------------------------------------------------------
# BUSCADOR
# ---------------------------------------------------------
@app.route("/buscar")
def buscar():
    if "usuario" not in session:
        return redirect(url_for("login"))

    q = request.args.get("q", "").strip()

    productos_list = list(productos.find({
        "name": {"$regex": q, "$options": "i"}
    }))

    if not productos_list:
        flash("No se encontraron productos para tu búsqueda.")

    return render_template("inicio.html",
                           productos=productos_list,
                           usuario=session["usuario"],
                           busqueda=q)

# ---------------------------------------------------------
# FILTRO POR CATEGORÍA
# ---------------------------------------------------------
@app.route("/categoria/<category>")
def categoria(category):
    if "usuario" not in session:
        return redirect(url_for("login"))

    productos_list = list(productos.find({"category": category}))

    if not productos_list:
        flash("No hay productos en esta categoría aún.")

    return render_template("inicio.html",
                           productos=productos_list,
                           usuario=session["usuario"],
                           categoria=category)

# ---------------------------------------------------------
# DETALLE DE PRODUCTO
# ---------------------------------------------------------
@app.route("/producto/<producto_id>")
def producto_detalle(producto_id):
    if "usuario" not in session:
        return redirect(url_for("login"))

    producto = productos.find_one({"_id": ObjectId(producto_id)})
    return render_template("producto.html", producto=producto, usuario=session["usuario"])

# ---------------------------------------------------------
# AGREGAR AL CARRITO
# ---------------------------------------------------------
@app.route("/agregar_carrito/<producto_id>", methods=["POST"])
def agregar_carrito(producto_id):
    if "usuario" not in session:
        return redirect(url_for("login"))

    producto = productos.find_one({"_id": ObjectId(producto_id)})
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
            "img": producto.get("img", ""),
            "cantidad": 1
        })

    session["carrito"] = carrito
    return redirect(url_for("carrito"))

# ---------------------------------------------------------
# CARRITO
# ---------------------------------------------------------
@app.route("/carrito")
def carrito():
    carrito = session.get("carrito", [])
    total = sum(item["price"] * item["cantidad"] for item in carrito)
    return render_template("carrito.html", carrito=carrito, total=total, usuario=session.get("usuario"))

# ---------------------------------------------------------
# ELIMINAR PRODUCTO DEL CARRITO
# ---------------------------------------------------------
@app.route("/eliminar_carrito/<producto_id>", methods=["POST"])
def eliminar_carrito(producto_id):
    carrito = session.get("carrito", [])
    carrito = [item for item in carrito if item["_id"] != producto_id]
    session["carrito"] = carrito
    return redirect(url_for("carrito"))

# ---------------------------------------------------------
# VACIAR CARRITO
# ---------------------------------------------------------
@app.route("/vaciar_carrito", methods=["POST"])
def vaciar_carrito():
    session["carrito"] = []
    return redirect(url_for("carrito"))

# ---------------------------------------------------------
# PAGO
# ---------------------------------------------------------
@app.route("/pago", methods=["GET", "POST"])
def pago():
    if "usuario" not in session:
        return redirect(url_for("login"))

    carrito = session.get("carrito", [])
    total = sum(item["price"] * item["cantidad"] for item in carrito)

    if request.method == "POST":
        nombre = request.form["nombre"]
        tarjeta = request.form["tarjeta"]
        cvv = request.form["cvv"]
        fecha = request.form["fecha"]

        pagos.insert_one({
            "usuario": session["usuario"],
            "carrito": carrito,
            "total": total,
            "nombre_tarjeta": nombre,
            "numero_tarjeta": tarjeta,
            "cvv": cvv,
            "fecha_exp": fecha,
            "fecha_compra": datetime.now()
        })

        session["carrito"] = []

        return render_template("pago_exitoso.html", total=total)

    return render_template("pago.html", carrito=carrito, total=total)

# ---------------------------------------------------------
# LOGOUT
# ---------------------------------------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
