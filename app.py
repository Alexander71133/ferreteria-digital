import os
import pandas as pd # Necesitaremos instalar esta librería
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Configuración de Base de Datos
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ferreteria.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
db = SQLAlchemy(app)

class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    precio = db.Column(db.Float)
    stock = db.Column(db.Integer)
    imagen = db.Column(db.String(200))

# --- RUTA PARA CARGA MASIVA ---
@app.route('/importar', methods=['POST'])
def importar():
    file = request.files['archivo_excel']
    if file:
        # Leemos el Excel o CSV
        df = pd.read_csv(file) # O pd.read_excel si prefieres .xlsx
        for _, row in df.iterrows():
            nuevo_p = Producto(
                nombre=row['nombre'],
                precio=row['precio'],
                stock=row['stock'],
                imagen='default.jpg' # Las fotos las subes luego manualmente
            )
            db.session.add(nuevo_p)
        db.session.commit()
    return redirect(url_for('admin'))

# ... (El resto de tus rutas de index y admin se mantienen igual)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)



