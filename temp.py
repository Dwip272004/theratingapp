from flask import Flask, session, redirect, url_for, request, jsonify, render_template
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'thefalcon'  # Replace this with a secure key

# Database setup
# Database setup
def init_db():
    conn = sqlite3.connect('likes.db')
    cursor = conn.cursor()

    # Create the photos table if not exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS photos (
            id INTEGER PRIMARY KEY,
            photo_name TEXT,  -- Ensure this column exists
            likes INTEGER DEFAULT 0,
            dislikes INTEGER DEFAULT 0
        )
    ''')

    # Create a table to store user ratings
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            photo_id INTEGER,
            action TEXT,
            UNIQUE(email, photo_id) -- Ensures that the user can rate the photo only once
        )
    ''')

    conn.commit()
    conn.close()


# Helper function to add photos to the database
def insert_photos():
    conn = sqlite3.connect('likes.db')
    cursor = conn.cursor()
    folder_path = 'static/images/'
    for filename in os.listdir(folder_path):
        # Check if the photo already exists in the database
        cursor.execute('SELECT * FROM photos WHERE photo_name=?', (filename,))
        if cursor.fetchone() is None:  # If photo is not already in DB
            cursor.execute('INSERT INTO photos (photo_name) VALUES (?)', (filename,))
    conn.commit()
    conn.close()

# Route for logging in with an email
@app.route('/login', methods=['POST'])
def login():
    email = request.json.get('email')
    if not email:
        return jsonify({'status': 'error', 'message': 'Email is required'}), 400

    # Store the email in session
    session['email'] = email
    return jsonify({'status': 'success', 'message': 'Logged in successfully'})

# Home route
@app.route('/')
def index():
    conn = sqlite3.connect('likes.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM photos ORDER BY likes DESC')
    photos = cursor.fetchall()
    conn.close()
    return render_template('index.html', photos=photos)

# Like a photo route
@app.route('/like', methods=['POST'])
def like_photo():
    if 'email' not in session:
        return jsonify({'status': 'error', 'message': 'You must be logged in to like photos'}), 403

    email = session['email']
    data = request.json
    photo_id = data['photo_id']

    conn = sqlite3.connect('likes.db')
    cursor = conn.cursor()

    # Check if the user has already liked or disliked the photo
    cursor.execute('SELECT action FROM user_ratings WHERE email=? AND photo_id=?', (email, photo_id))
    existing_action = cursor.fetchone()

    if existing_action:
        if existing_action[0] == 'like':
            conn.close()
            return jsonify({'status': 'already liked'})
        elif existing_action[0] == 'dislike':
            # If previously disliked, update action to like
            cursor.execute('UPDATE photos SET dislikes = dislikes - 1 WHERE id=?', (photo_id,))
            cursor.execute('UPDATE photos SET likes = likes + 1 WHERE id=?', (photo_id,))
            cursor.execute('UPDATE user_ratings SET action = "like" WHERE email=? AND photo_id=?', (email, photo_id))
    else:
        # Add the new like entry
        cursor.execute('UPDATE photos SET likes = likes + 1 WHERE id=?', (photo_id,))
        cursor.execute('INSERT INTO user_ratings (email, photo_id, action) VALUES (?, ?, "like")', (email, photo_id))

    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

# Dislike a photo route
@app.route('/dislike', methods=['POST'])
def dislike_photo():
    if 'email' not in session:
        return jsonify({'status': 'error', 'message': 'You must be logged in to dislike photos'}), 403

    email = session['email']
    data = request.json
    photo_id = data['photo_id']

    conn = sqlite3.connect('likes.db')
    cursor = conn.cursor()

    # Check if the user has already liked or disliked the photo
    cursor.execute('SELECT action FROM user_ratings WHERE email=? AND photo_id=?', (email, photo_id))
    existing_action = cursor.fetchone()

    if existing_action:
        if existing_action[0] == 'dislike':
            conn.close()
            return jsonify({'status': 'already disliked'})
        elif existing_action[0] == 'like':
            # If previously liked, update action to dislike
            cursor.execute('UPDATE photos SET likes = likes - 1 WHERE id=?', (photo_id,))
            cursor.execute('UPDATE photos SET dislikes = dislikes + 1 WHERE id=?', (photo_id,))
            cursor.execute('UPDATE user_ratings SET action = "dislike" WHERE email=? AND photo_id=?', (email, photo_id))
    else:
        # Add the new dislike entry
        cursor.execute('UPDATE photos SET dislikes = dislikes + 1 WHERE id=?', (photo_id,))
        cursor.execute('INSERT INTO user_ratings (email, photo_id, action) VALUES (?, ?, "dislike")', (email, photo_id))

    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})


if __name__ == '__main__':
    init_db()  # Initialize the database and create the tables
    insert_photos() 
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)