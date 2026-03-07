import os
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename # Nueva para nombres de archivos seguros

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_ferreteria'

# Configuración de Base de Datos y Carpetas
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ferreteria.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# CREAR CARPETA DE FOTOS SI NO EXISTE
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

db = SQLAlchemy(app)

# Modelo de Producto
class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    precio = db.Column(db.Float)
    stock = db.Column(db.Integer)
    imagen = db.Column(db.String(200))

with app.app_context():
    db.create_all()

# --- RUTA PRINCIPAL (CLIENTES) ---
@app.route('/')
def index():
    busqueda = request.args.get('search')
    
    if busqueda:
        # 1. Quitamos espacios y pasamos a MAYÚSCULAS para que coincida con tu DB
        termino = busqueda.strip().upper()
        
        # 2. Buscamos productos que contengan ese término
        productos = Producto.query.filter(Producto.nombre.ilike(f"%{termino}%")).all()
    else:
        productos = Producto.query.all()
        
    return render_template('index.html', productos=productos, busqueda=busqueda)

# --- RUTA ADMINISTRADOR (ACTUALIZADA PARA RECIBIR FOTOS) ---
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        precio = float(request.form.get('precio'))
        stock = int(request.form.get('stock'))
        
        # Procesar la foto del teléfono
        file = request.files.get('imagen_archivo')
        url_final_imagen = "default.jpg" # Imagen por defecto

        if file and file.filename != '':
            filename = secure_filename(file.filename)
            # Añadimos el nombre del producto al archivo para que sea único
            filename = f"{nombre.replace(' ', '_')}_{filename}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            url_final_imagen = f"uploads/{filename}" # Se guarda la ruta relativa

        nuevo_p = Producto(
            nombre=nombre, 
            precio=precio, 
            stock=stock, 
            imagen=url_final_imagen
        )
        db.session.add(nuevo_p)
        db.session.commit()
        return redirect(url_for('admin'))

    # Si es GET, solo mostramos la lista
    productos = Producto.query.all()
    return render_template('admin.html', productos=productos)

# --- LAS DEMÁS RUTAS (Importar, Eliminar, Editar, Carrito) SE MANTIENEN IGUAL ---

@app.route('/importar', methods=['POST'])
def importar():
    file = request.files['archivo_excel']
    if file:
        try:
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
    
    if 'carrito' not in session:
        session['carrito'] = []
    
    carrito = session['carrito']
    
    # Revisamos si ya está para sumar cantidad, si no, lo añadimos con 1
    encontrado = False
    for item in carrito:
        if item['id'] == producto.id:
            item['cantidad'] = item.get('cantidad', 0) + 1
            encontrado = True
            break
            
    if not encontrado:
        carrito.append({
            'id': producto.id,
            'nombre': producto.nombre,
            'precio': producto.precio,
            'cantidad': 1
        })
    
    session['carrito'] = carrito
    session.modified = True
    return redirect(url_for('index'))

@app.route('/vaciar_carrito')
def vaciar_carrito():
    session.pop('carrito', None)
    return redirect(url_for('index'))

@app.route('/modificar_cantidad/<int:id>/<accion>')
def modificar_cantidad(id, accion):
    carrito = session.get('carrito', [])
    for item in carrito:
        if item['id'] == id:
            if accion == 'sumar':
                item['cantidad'] = item.get('cantidad', 1) + 1
            elif accion == 'restar' and item.get('cantidad', 1) > 1:
                item['cantidad'] -= 1
            break
    session['carrito'] = carrito
    session.modified = True
    return redirect(url_for('index'))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)












