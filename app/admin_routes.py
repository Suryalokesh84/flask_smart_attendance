from flask import Blueprint, render_template, request, redirect, url_for, flash

admin = Blueprint('admin', __name__)

@admin.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Simple static admin credentials
        if username == "admin" and password == "123":
            return redirect(url_for('admin.dashboard'))
        else:
            flash("Invalid credentials", "error")

    return render_template('admin_login.html')  # ✅ Corrected template name

@admin.route('/dashboard')
def dashboard():
    return render_template('admin_dashboard.html')

@admin.route('/students')
def students():
    return "<h2>Student Records Page</h2>"

@admin.route('/attendance_records')
def attendance_records():
    return "<h2>View Attendance Records Page</h2>"

@admin.route('/mark_attendance')
def mark_attendance():
    return "<h2>Manual Attendance Marking Page</h2>"

@admin.route('/edit_students')
def edit_students():
    return "<h2>Edit Student Records Page</h2>"
