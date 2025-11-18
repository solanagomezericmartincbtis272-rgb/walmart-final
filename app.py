from flask import Flask, render_template, request, redirect, url_for, session, flash 
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
import os

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

    try:
        productos_list = list(productos.find())
        return render_template("inicio.html", productos=productos_list, usuario=session["usuario"])
    except Exception as e:
        print(f"Error en inicio: {e}")
        return "Error interno del servidor", 500

# ---------------------------------------------------------
# BUSCADOR
# ---------------------------------------------------------
@app.route("/buscar")
def buscar():
    if "usuario" not in session:
        return redirect(url_for("login"))

    try:
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
    except Exception as e:
        print(f"Error en buscar: {e}")
        return "Error interno del servidor", 500

# ---------------------------------------------------------
# FILTRO POR CATEGORÍA
# ---------------------------------------------------------
@app.route("/categoria/<category>")
def categoria(category):
    if "usuario" not in session:
        return redirect(url_for("login"))

    try:
        productos_list = list(productos.find({"category": category}))

        if not productos_list:
            flash("No hay productos en esta categoría aún.")

        return render_template("inicio.html",
                               productos=productos_list,
                               usuario=session["usuario"],
                               categoria=category)
    except Exception as e:
        print(f"Error en categoría: {e}")
        return "Error interno del servidor", 500

# ---------------------------------------------------------
# DETALLE DE PRODUCTO
# ---------------------------------------------------------
@app.route("/producto/<producto_id>")
def producto_detalle(producto_id):
    if "usuario" not in session:
        return redirect(url_for("login"))

    try:
        producto = productos.find_one({"_id": ObjectId(producto_id)})
        if not producto:
            flash("Producto no encontrado")
            return redirect(url_for("inicio"))
            
        return render_template("producto.html", producto=producto, usuario=session["usuario"])
    except Exception as e:
        print(f"Error en producto_detalle: {e}")
        return "Error interno del servidor", 500

# ---------------------------------------------------------
# AGREGAR AL CARRITO
# ---------------------------------------------------------
@app.route("/agregar_carrito/<producto_id>", methods=["POST"])
def agregar_carrito(producto_id):
    if "usuario" not in session:
        return redirect(url_for("login"))

    try:
        producto = productos.find_one({"_id": ObjectId(producto_id)})
        if not producto:
            flash("Producto no encontrado")
            return redirect(url_for("inicio"))

        carrito = session.get("carrito", [])
        
        # Asegurar que el producto tenga imagen
        img_url = producto.get("img", "https://via.placeholder.com/120")
        
        # Buscar si el producto ya está en el carrito
        encontrado = False
        for item in carrito:
            if item["_id"] == str(producto["_id"]):
                item["cantidad"] += 1
                encontrado = True
                break
        
        # Si no está, agregarlo
        if not encontrado:
            carrito.append({
                "_id": str(producto["_id"]),
                "name": producto["name"],
                "price": float(producto["price"]),  # Asegurar que sea float
                "img": img_url,
                "cantidad": 1
            })

        session["carrito"] = carrito
        flash(f"✅ {producto['name']} agregado al carrito")
        return redirect(url_for("carrito"))
        
    except Exception as e:
        print(f"Error en agregar_carrito: {e}")
        return "Error interno del servidor", 500

# ---------------------------------------------------------
# CARRITO
# ---------------------------------------------------------
@app.route("/carrito")
def carrito():
    try:
        if "usuario" not in session:
            return redirect(url_for("login"))

        carrito = session.get("carrito", [])
        total = sum(item["price"] * item["cantidad"] for item in carrito)
        
        # Obtener algunos productos para sugerencias
        sugerencias = list(productos.find().limit(3))
        
        return render_template("carrito.html", 
                             carrito=carrito, 
                             total=total, 
                             usuario=session.get("usuario"),
                             sugerencias=sugerencias)
    except Exception as e:
        print(f"Error en carrito: {e}")
        return "Error interno del servidor", 500

# ---------------------------------------------------------
# ACTUALIZAR CANTIDAD DEL CARRITO
# ---------------------------------------------------------
@app.route("/actualizar_cantidad/<producto_id>", methods=["POST"])
def actualizar_cantidad(producto_id):
    if "usuario" not in session:
        return redirect(url_for("login"))

    try:
        nueva_cantidad = int(request.form["cantidad"])
        carrito = session.get("carrito", [])

        for item in carrito:
            if item["_id"] == producto_id:
                item["cantidad"] = max(1, nueva_cantidad)
                break

        session["carrito"] = carrito
        return redirect(url_for("carrito"))
    except Exception as e:
        print(f"Error en actualizar_cantidad: {e}")
        return "Error interno del servidor", 500

# ---------------------------------------------------------
# ELIMINAR PRODUCTO DEL CARRITO
# ---------------------------------------------------------
@app.route("/eliminar_carrito/<producto_id>", methods=["POST"])
def eliminar_carrito(producto_id):
    try:
        carrito = session.get("carrito", [])
        carrito = [item for item in carrito if item["_id"] != producto_id]
        session["carrito"] = carrito
        flash("Producto eliminado del carrito")
        return redirect(url_for("carrito"))
    except Exception as e:
        print(f"Error en eliminar_carrito: {e}")
        return "Error interno del servidor", 500

# ---------------------------------------------------------
# VACIAR CARRITO
# ---------------------------------------------------------
@app.route("/vaciar_carrito", methods=["POST"])
def vaciar_carrito():
    try:
        session["carrito"] = []
        flash("Carrito vaciado")
        return redirect(url_for("carrito"))
    except Exception as e:
        print(f"Error en vaciar_carrito: {e}")
        return "Error interno del servidor", 500

# ---------------------------------------------------------
# PAGO
# ---------------------------------------------------------
@app.route("/pago", methods=["GET", "POST"])
def pago():
    if "usuario" not in session:
        return redirect(url_for("login"))

    try:
        carrito = session.get("carrito", [])
        if not carrito:
            flash("Tu carrito está vacío")
            return redirect(url_for("inicio"))
            
        total = sum(item["price"] * item["cantidad"] for item in carrito)

        if request.method == "POST":
            nombre = request.form["nombre"]
            tarjeta = request.form["tarjeta"]
            cvv = request.form["cvv"]
            fecha = request.form["fecha"]

            # Validaciones básicas
            if not all([nombre, tarjeta, cvv, fecha]):
                flash("Por favor completa todos los campos")
                return render_template("pago.html", carrito=carrito, total=total)

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
            flash("¡Pago realizado con éxito!")

            return render_template("pago_exitoso.html", total=total)

        return render_template("pago.html", carrito=carrito, total=total)
    except Exception as e:
        print(f"Error en pago: {e}")
        return "Error interno del servidor", 500

# ---------------------------------------------------------
# LOGOUT
# ---------------------------------------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ---------------------------------------------------------
# MANEJO DE ERRORES
# ---------------------------------------------------------
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)

