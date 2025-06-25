import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, send_from_directory

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Create upload folder if not exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Connect to SQLite database
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Get notes with optional filters
def get_notes_from_db(subject=None, semester=None):
    conn = get_db_connection()
    if subject and semester:
        notes = conn.execute("SELECT * FROM notes WHERE subject LIKE ? AND semester LIKE ?",
                             ('%' + subject + '%', '%' + semester + '%')).fetchall()
    else:
        notes = conn.execute("SELECT * FROM notes").fetchall()
    conn.close()
    return notes

@app.route('/')
def index():
    subject = request.args.get('subject')
    semester = request.args.get('semester')
    notes = get_notes_from_db(subject, semester)

    # Fetch all comments
    conn = get_db_connection()
    comments_data = conn.execute('SELECT * FROM comments').fetchall()
    conn.close()

    # Organize comments by note_id
    comments = {}
    for comment in comments_data:
        note_id = comment['note_id']
        if note_id not in comments:
            comments[note_id] = []
        comments[note_id].append(comment)

    return render_template('index.html', notes=notes, comments=comments)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        title = request.form['title']
        subject = request.form['subject']
        semester = request.form['semester']
        file = request.files['file']

        if file and title and subject and semester:
            filename = file.filename
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            conn = get_db_connection()
            conn.execute("INSERT INTO notes (title, subject, semester, filename, likes) VALUES (?, ?, ?, ?, 0)",
                         (title, subject, semester, filename))
            conn.commit()
            conn.close()
            return redirect(url_for('index'))
    return render_template('upload.html')

@app.route('/like/<int:note_id>', methods=['POST'])
def like(note_id):
    conn = get_db_connection()
    conn.execute('UPDATE notes SET likes = likes + 1 WHERE id = ?', (note_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/comment/<int:note_id>', methods=['POST'])
def comment(note_id):
    text = request.form['comment']
    if text:
        conn = get_db_connection()
        conn.execute('INSERT INTO comments (note_id, text) VALUES (?, ?)', (note_id, text))
        conn.commit()
        conn.close()
    return redirect(url_for('index'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
