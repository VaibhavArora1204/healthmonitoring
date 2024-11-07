from flask import Flask, render_template, request, redirect, session
import sqlite3 as ms
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)  # Initializing Flask app
app.secret_key = 'vivaproj'  # Secret key for session management

# Database setup
def mysql_db():
    conn = ms.connect('health_monitoring.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR,
            email TEXT UNIQUE,
            password VARCHAR
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS health_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date TEXT,
            heart_rate INTEGER,
            blood_pressure VARCHAR,
            weight REAL,
            steps_walked INTEGER,
            calories_burned REAL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()

# Call this to ensure tables are created
mysql_db()

# User Registration Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        with ms.connect('health_monitoring.db') as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)", (name, email, password))
                conn.commit()
                return redirect('/login')
            except ms.IntegrityError:
                return "Registration failed. Email might already be registered."
    
    return render_template('register.html')  # This will load register.html

# User Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        with ms.connect('health_monitoring.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            user = cursor.fetchone()
            if user and check_password_hash(user[3], password):
                session['user_id'] = user[0]
                session['name'] = user[1]
                return redirect('/dashboard')
            else:
                return "Login failed. Check email or password."
    
    return render_template('login.html')  # This will load login.html

# User Dashboard Route
@app.route('/dashboard')
def dashboard():
    if 'user_id' in session:
        with ms.connect('health_monitoring.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM health_metrics WHERE user_id = ?", (session['user_id'],))
            data = cursor.fetchall()

        return render_template('dashboard.html', data=data, name=session['name'])  # Load dashboard.html

    return redirect('/login')

# Input Vitals Route
@app.route('/input_vitals', methods=['GET', 'POST'])
def input_vitals():
    if request.method == 'POST':
        user_id = session['user_id']
        heart_rate = request.form['heart_rate']
        blood_pressure = request.form['blood_pressure']
        weight = request.form['weight']
        steps_walked = request.form['steps_walked']
        calories_burned = request.form['calories_burned']
        date = request.form['date']

        with ms.connect('health_monitoring.db') as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''INSERT INTO health_metrics (user_id, date, heart_rate, blood_pressure, weight, steps_walked, calories_burned) 
                VALUES (?, ?, ?, ?, ?, ?, ?)''', 
                (user_id, date, heart_rate, blood_pressure, weight, steps_walked, calories_burned)
            )
            conn.commit()

        return redirect('/dashboard')

    return '''
    <form method="post">
        Date: <input type="date" name="date"><br>
        Heart Rate: <input type="number" name="heart_rate"><br>
        Blood Pressure: <input type="text" name="blood_pressure"><br>
        Weight: <input type="number" name="weight" step="0.1"><br>
        Steps Walked: <input type="number" name="steps_walked"><br>
        Calories Burned: <input type="number" name="calories_burned" step="0.1"><br>
        <input type="submit" value="Submit Vitals">
    </form>
    '''  # Keep this simple form for now

# Logout Route
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('name', None)
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True, port=8000)

