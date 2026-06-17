from flask import Flask, render_template, request, redirect
import sqlite3
import csv
import random
otp = ""
app = Flask(__name__)

# ---------------- GLOBAL STATE ----------------
ride_status = "Not Booked"
sos_flag = False
driver_name = ""
vehicle_no = ""


# ---------------- DATABASE INIT ----------------
def init_db():

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # USERS TABLE
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        age TEXT,
        location TEXT,
        mobile TEXT,
        gender TEXT      
    )
    ''')

    # DRIVERS TABLE
    c.execute('''
    CREATE TABLE IF NOT EXISTS drivers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        age TEXT,
        location TEXT,
        mobile TEXT,
        gender TEXT,
        id_proof TEXT,
        status TEXT
    )
    ''')

    conn.commit()
    conn.close()


# ---------------- HOME ----------------
@app.route('/')
def home():
    return render_template('home.html')


# ================= USER MODULE =================

# -------- REGISTER --------
@app.route('/user/register', methods=['GET', 'POST'])
def user_register():
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        location = request.form['location']
        mobile = request.form['mobile']
        gender = request.form['gender']

        if gender.lower() != "female":
            return "❌ Only female users allowed!"

        conn = sqlite3.connect('database.db')
        c = conn.cursor()

        c.execute("INSERT INTO users (name, age, location, mobile) VALUES (?, ?, ?, ?)",
                  (name, age, location, mobile))

        conn.commit()
        conn.close()

        return redirect('/user/login')

    return render_template('user/user_register.html')


# -------- LOGIN --------
@app.route('/user/login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        return redirect('/user/book')
    return render_template('user/user_login.html')


# -------- BOOK RIDE --------
@app.route('/user/book', methods=['GET', 'POST'])
def book_ride():
    global ride_status

    if request.method == 'POST':
        ride_status = "🔍 Searching for driver..."
        return redirect('/map')

    return render_template('user/book_ride.html')


# -------- MAP VIEW --------
@app.route('/map')
def map_view():
    return render_template(
        'user/map.html',
        status=ride_status,
        driver_name=driver_name,
        vehicle_no=vehicle_no
    )


# -------- DRIVER ASSIGN (CSV) --------
@app.route('/simulate')
def simulate():
    global ride_status, driver_name, vehicle_no

    driver_name = "Anjali"
    vehicle_no = "TS09AB1234"
    ride_status = "👩 Driver Assigned"

    print("DRIVER SET:", driver_name)

    return redirect('/map')

# -------- START RIDE --------
@app.route('/start')
def start_ride():
    global ride_status
    ride_status = "🚗 Ride Started"
    return redirect('/map')


# -------- COMPLETE RIDE --------
@app.route('/complete')
def complete_ride():
    global ride_status
    ride_status = "✅ Ride Completed"
    return redirect('/map')


# -------- SOS --------
@app.route('/user/sos')
def sos():
    global sos_flag
    sos_flag = True
    return "🚨 SOS Alert Sent!"


# ================= ADMIN =================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        return redirect('/admin/dashboard')
    return render_template('admin/admin_login.html')


@app.route('/admin/dashboard')
def admin_dashboard():
    return render_template('admin/admin_dashboard.html', status=ride_status)


@app.route('/admin/sos')
def admin_sos():
    return render_template('admin/sos_alerts.html', sos=sos_flag)

# ================= DRIVER MODULE =================

@app.route('/driver/register', methods=['GET', 'POST'])
def driver_register():
    if request.method == 'POST':

        name = request.form.get('name')
        age = request.form.get('age')
        location = request.form.get('location')
        mobile = request.form.get('mobile')
        gender = request.form.get('gender')
        file = request.files.get('id_proof')

        # 🔴 Only female allowed
        if gender.lower() != "female":
            return "❌ Only female drivers allowed!"

        # 🔴 ID proof required
        if not file or file.filename == "":
            return "❌ Upload ID proof!"

        filepath = "uploads/" + file.filename
        file.save(filepath)

        # Save in DB (status = pending)
        conn = sqlite3.connect('database.db')
        c = conn.cursor()

        c.execute("INSERT INTO drivers (name, age, location, mobile, id_proof, status) VALUES (?, ?, ?, ?, ?, ?)",
                  (name, age, location, mobile, filepath, "pending"))

        conn.commit()
        conn.close()

        return "✅ Registration submitted! Wait for admin approval."

    return render_template('driver/driver_register.html')


@app.route('/driver/login', methods=['GET', 'POST'])
def driver_login():

    if request.method == 'POST':

        name = request.form.get('name').strip()
        gender = request.form.get('gender').lower()

        if gender != "female":
            return "❌ Only female drivers allowed!"

        conn = sqlite3.connect('database.db')
        c = conn.cursor()

        c.execute("SELECT * FROM drivers WHERE LOWER(name)=LOWER(?)", (name,))
        driver = c.fetchone()

        conn.close()

        if driver:
            return redirect('/driver/dashboard')

        else:
            return "❌ Driver not found!"

    return render_template('driver/driver_login.html')


@app.route('/driver/dashboard')
def driver_dashboard():
    return render_template('driver/driver_dashboard.html')

@app.route('/admin/drivers')
def view_drivers():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("SELECT * FROM drivers")
    drivers = c.fetchall()

    conn.close()

    return render_template('admin/drivers.html', drivers=drivers)

@app.route('/admin/approve/<int:id>')
def approve_driver(id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("UPDATE drivers SET status='approved' WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect('/admin/drivers')

@app.route('/send_otp')
def send_otp():
    global otp
    otp = str(random.randint(1000, 9999))
    print("OTP:", otp)
    return "OTP sent (check terminal)"

@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    user_otp = request.form.get('otp')

    if user_otp == otp:
        return "✅ Verified!"
    else:
        return "❌ Invalid OTP"
# ---------------- RUN ----------------
init_db()
if __name__ == '__main__':
    
    app.run(debug=True)