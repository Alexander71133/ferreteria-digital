import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
import urllib.parse

app = Flask(__name__)

# Configuración básica
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('ferreteria.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS productos 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, precio REAL, imagen TEXT, stock INTEGER)''')
    conn.commit()
    conn.close()

init_db()

# --- RUTA PÚBLICA (EL CATÁLOGO) ---
@app.route('/')
def home():
    search = request.args.get('search')
    conn = sqlite3.connect('ferreteria.db')
    conn.row_factory = sqlite3.Row
    
    if search:
        productos_db = conn.execute("SELECT * FROM productos WHERE nombre LIKE ?", ('%' + search + '%',)).fetchall()
    else:
        productos_db = conn.execute('SELECT * FROM productos').fetchall()
    conn.close()
    
    productos = []
    for row in productos_db:
        p = dict(row)
        # RECUERDA: Cambia el número abajo por tu WhatsApp real
        msg = urllib.parse.quote(f"Hola, me interesa el {p['nombre']}")
        p['link_ws'] = f"https://wa.me/573000000000?text={msg}"
        productos.append(p)
    
    return render_template('index.html', productos=productos, busqueda=search)

# --- RUTA ADMIN (EL PANEL) ---
@app.route('/admin')
def admin_panel():
    conn = sqlite3.connect('ferreteria.db')
    conn.row_factory = sqlite3.Row
    productos = conn.execute('SELECT * FROM productos').fetchall()
    conn.close()
    return render_template('admin.html', productos=productos)

# --- ACCIÓN: AGREGAR PRODUCTO ---
@app.route('/admin/add', methods=['POST'])
def add_product():
    file = request.files['foto']
    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        img_path = f'/static/uploads/{filename}'
        
        conn = sqlite3.connect('ferreteria.db')
        conn.execute('INSERT INTO productos (nombre, precio, imagen, stock) VALUES (?, ?, ?, ?)',
                     (request.form['nombre'], request.form['precio'], img_path, request.form['stock']))
        conn.commit()
        conn.close()
    return redirect(url_for('admin_panel'))

# --- ACCIÓN: ELIMINAR PRODUCTO ---
@app.route('/admin/delete/<int:id>')
def delete_product(id):
    conn = sqlite3.connect('ferreteria.db')
    p = conn.execute('SELECT imagen FROM productos WHERE id = ?', (id,)).fetchone()
    if p:
        try:
            # Borra la foto de la carpeta static/uploads
            path_a_borrar = p[0].lstrip('/')
            os.remove(os.path.join(os.getcwd(), path_a_borrar))
        except:
            pass
    
    conn.execute('DELETE FROM productos WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_panel'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)