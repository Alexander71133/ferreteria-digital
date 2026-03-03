import os
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, session # Agrega session aquí
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_ferreteria'  # Necesaria para usar session

# Configuración de Base de Datos
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ferreteria.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
db = SQLAlchemy(app)

# Modelo de Producto
class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    precio = db.Column(db.Float)
    stock = db.Column(db.Integer)
    imagen = db.Column(db.String(200))

# Crear la base de datos al iniciar
with app.app_context():
    db.create_all()

# --- RUTA PRINCIPAL (CLIENTES) ---
@app.route('/')
def index():
    productos = Producto.query.all()
    return render_template('index.html', productos=productos)

# --- RUTA ADMINISTRADOR ---
@app.route('/admin')
def admin():
    productos = Producto.query.all()
    return render_template('admin.html', productos=productos)

# --- RUTA PARA CARGA MASIVA ---
@app.route('/importar', methods=['POST'])
def importar():
    file = request.files['archivo_excel']
    if file:
        try:
            # Leemos el CSV
            df = pd.read_csv(file)
            for _, row in df.iterrows():
                nuevo_p = Producto(
                    nombre=row['nombre'],
                    precio=row['precio'],
                    stock=row['stock'],
                    imagen='default.jpg'
                )
                db.session.add(nuevo_p)
            db.session.commit()
        except Exception as e:
            print(f"Error al importar: {e}")
    return redirect(url_for('admin'))

@app.route('/eliminar/<int:id>')
def eliminar(id):
    producto = Producto.query.get(id)
    if producto:
        db.session.delete(producto)
        db.session.commit()
    return redirect(url_for('admin'))

@app.route('/editar/<int:id>', methods=['POST'])
def editar(id):
    producto = Producto.query.get(id)
    if producto:
        producto.nombre = request.form.get('nombre')
        producto.precio = float(request.form.get('precio'))
        producto.stock = int(request.form.get('stock'))
        db.session.commit()
    return redirect(url_for('admin'))

@app.route('/agregar_al_carrito/<int:id>')
def agregar_al_carrito(id):
    producto = Producto.query.get(id)
    if not producto:
        return redirect(url_for('index'))
    
    # Si no hay carrito, creamos uno vacío
    if 'carrito' not in session:
        session['carrito'] = []
    
    # Guardamos los datos básicos del producto
    carrito = session['carrito']
    carrito.append({
        'id': producto.id,
        'nombre': producto.nombre,
        'precio': producto.precio
    })
    session['carrito'] = carrito
    return redirect(url_for('index'))

@app.route('/vaciar_carrito')
def vaciar_carrito():
    session.pop('carrito', None)
    return redirect(url_for('index'))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)






