import os
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash, session
from datetime import datetime
import sqlite3
import uuid
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

DB_PATH = '/home/jimmy/inspectiontool/db.sqlite3'

# Initialize database
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS inspections (id INTEGER PRIMARY KEY AUTOINCREMENT, inspector_name TEXT NOT NULL, location TEXT NOT NULL, inspection_date TEXT NOT NULL, installation_name TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP)")
    cursor.execute("CREATE TABLE IF NOT EXISTS checklist_items (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL)")
    cursor.execute("INSERT OR IGNORE INTO checklist_items (name) VALUES ('Check electrical wiring'), ('Check plumbing'), ('Check fire safety'), ('Check electrical safety'), ('Check water pressure'), ('Check drainage'), ('Check structural integrity'), ('Check emergency exits'), ('Check fire extinguishers'), ('Check ventilation')")
    cursor.execute("CREATE TABLE IF NOT EXISTS inspection_photos (id INTEGER PRIMARY KEY AUTOINCREMENT, inspection_id INTEGER NOT NULL, photo_path TEXT NOT NULL, comment TEXT, resolved INTEGER DEFAULT 0, uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP)")
    cursor.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'user', logo_path TEXT)")

    # Add default admin user
    hashed_password = generate_password_hash('admin')
    cursor.execute("INSERT OR IGNORE INTO users (username, password_hash, role) VALUES ('admin', ?, 'admin')", (hashed_password,))

    conn.commit()
    conn.close()

init_db()

# Set up static folders
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
app.config['PDF_FOLDER'] = os.path.join(app.root_path, 'static', 'pdf')
app.config['LOGO_FOLDER'] = os.path.join(app.root_path, 'static', 'logo')

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PDF_FOLDER'], exist_ok=True)
os.makedirs(app.config['LOGO_FOLDER'], exist_ok=True)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['role'] = user[3]
            # Store logo path for current user in session
            cursor.execute("SELECT logo_path FROM users WHERE username = ?", (username,))
            logo_path = cursor.fetchone()[0] if cursor.fetchone() else None
            session['user_logo_path'] = logo_path
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password')
            return render_template('login.html')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form.get('role', 'user')
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            flash('Username already exists')
            return redirect(url_for('register'))
        hashed_password = generate_password_hash(password)
        cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", (username, hashed_password, role))
        conn.commit()
        conn.close()
        flash('Registration successful!')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('role', None)
    session.pop('user_logo_path', None)
    return redirect(url_for('index'))

@app.route('/admin')
def admin():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('admin.html')

@app.route('/admin/users')
def admin_users():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('index'))
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    conn.close()
    return render_template('admin_users.html', users=users)

@app.route('/admin/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('index'))
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_users'))

@app.route('/admin/logo', methods=['GET', 'POST'])
def admin_logo():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('index'))
    if request.method == 'POST':
        if 'logo' in request.files:
            file = request.files['logo']
            if file.filename == '':
                flash('No selected file')
                return redirect(url_for('admin_users'))
            filename = f'logo_{uuid.uuid4().hex}.png'
            logo_path = os.path.join(app.config['LOGO_FOLDER'], filename)
            file.save(logo_path)

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET logo_path = ? WHERE username = 'admin'", (logo_path,))
            conn.commit()
            conn.close()

            flash('Logo uploaded successfully')
            return redirect(url_for('admin_users'))
    return render_template('admin_logo.html')

@app.route('/')
def index():
    conn = sqlite3.connect(DB_PATH)
    inspections = conn.execute("SELECT * FROM inspections ORDER BY inspection_date DESC").fetchall()
    conn.close()
    return render_template('index.html', inspections=inspections)

@app.route('/new', methods=['GET', 'POST'])
def new_inspection():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        inspector_name = request.form['inspector_name']
        location = request.form['location']
        inspection_date = request.form['inspection_date']
        installation_name = request.form['installation_name']

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO inspections (inspector_name, location, inspection_date, installation_name) VALUES (?, ?, ?, ?)",
                      (inspector_name, location, inspection_date, installation_name))
        conn.commit()
        conn.close()

        return redirect(url_for('view_inspection', id=cursor.lastrowid))

    return render_template('new_inspection.html')

@app.route('/view/<int:id>')
def view_inspection(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM inspections WHERE id = ?", (id,))
    inspection = cursor.fetchone()

    cursor.execute("SELECT * FROM inspection_photos WHERE inspection_id = ?", (id,))
    photos = cursor.fetchall()

    cursor.execute("SELECT * FROM checklist_items")
    checklist_items = cursor.fetchall()

    conn.close()

    return render_template('inspection.html', inspection=inspection, photos=photos, checklist_items=checklist_items)

@app.route('/upload/<int:id>', methods=['POST'])
def upload_photo(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if 'photo' not in request.files:
        flash('No file part')
        return redirect(url_for('view_inspection', id=id))

    file = request.files['photo']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('view_inspection', id=id))

    filename = f'photo_{uuid.uuid4().hex}.jpg'
    photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(photo_path)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO inspection_photos (inspection_id, photo_path, comment) VALUES (?, ?, ?)",
                  (id, filename, request.form.get('comment', '')))
    conn.commit()
    conn.close()

    flash('Photo uploaded successfully')
    return redirect(url_for('view_inspection', id=id))

@app.route('/generate_pdf/<int:id>', methods=['GET'])
def generate_pdf(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM inspections WHERE id = ?", (id,))
    inspection = cursor.fetchone()

    cursor.execute("SELECT * FROM inspection_photos WHERE inspection_id = ?", (id,))
    photos = cursor.fetchall()

    cursor.execute("SELECT * FROM checklist_items")
    checklist_items = cursor.fetchall()

    conn.close()

    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib import utils
    from reportlab.lib.utils import ImageReader

    pdf_path = os.path.join(app.config['PDF_FOLDER'], f'report_{id}.pdf')
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()

    elements = []
    elements.append(Paragraph(f"Inspection Report - {inspection[1]}", styles['Heading1']))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Inspector: {inspection[1]}", styles['Normal']))
    elements.append(Paragraph(f"Location: {inspection[2]}", styles['Normal']))
    elements.append(Paragraph(f"Date: {inspection[3]}", styles['Normal']))
    elements.append(Paragraph(f"Installation: {inspection[4]}", styles['Normal']))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("Checklist", styles['Heading2']))
    for item in checklist_items:
        elements.append(Paragraph(f"- {item[1]}", styles['Normal']))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("Photos", styles['Heading2']))
    for photo in photos:
        elements.append(Paragraph(f"Photo {photo[0]}: {photo[2]}", styles['Normal']))
        elements.append(Spacer(1, 4))

    # Add logo if available
    logo_path = session.get('user_logo_path')
    if logo_path:
        try:
            logo = ImageReader(logo_path)
            logo_width = 100
            logo_height = 100
            elements.append(Paragraph(f"Logo: {logo_path}", styles['Normal']))
            # Add logo to PDF
            doc.build(elements)
        except Exception as e:
            print(f"Error adding logo: {e}")
    else:
        doc.build(elements)

    return send_from_directory(app.config['PDF_FOLDER'], f'report_{id}.pdf', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)