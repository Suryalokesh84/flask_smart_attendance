from flask import Blueprint, render_template, request, redirect, url_for, flash
import json
import os
from datetime import datetime

# Define the admin blueprint
admin = Blueprint('admin', __name__)

# Admin Login Route
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

    return render_template('admin_login.html')

# Admin Dashboard Route
@admin.route('/dashboard')
def dashboard():
    return render_template('admin_dashboard.html')

# Student Records Page
@admin.route('/students')
def students():
    return render_template('students.html')

# ✅ Move Attendance Records to Admin Dashboard
@admin.route('/attendance_records')
def attendance_records():
    """Displays attendance records under /admin/attendance_records."""
    
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    branch = request.args.get('branch')
    search_term = request.args.get('search_term')
    sort = request.args.get('sort')

    attendance_data = []

    if os.path.exists('attendance_records.json'):
        with open('attendance_records.json', 'r') as f:
            attendance_data = json.load(f)

    # Filter by date range
    if start_date:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        attendance_data = [record for record in attendance_data if datetime.strptime(record['date'], "%Y-%m-%d") >= start_date]
    if end_date:
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
        attendance_data = [record for record in attendance_data if datetime.strptime(record['date'], "%Y-%m-%d") <= end_date]
    
    # Filter by branch
    if branch:
        attendance_data = [record for record in attendance_data if record['branch'].lower() == branch.lower()]
    
    # Search term filter
    if search_term:
        search_term = search_term.lower()
        attendance_data = [record for record in attendance_data if search_term in record['name'].lower() or search_term in record['rollNumber'].lower()]

    # Sort by roll number
    if sort == 'rollNumber':
        attendance_data = sorted(attendance_data, key=lambda x: x['rollNumber'])

    return render_template('attendance_records.html', attendance_data=attendance_data)

# Manual Attendance Marking Page
@admin.route('/mark_attendance')
def mark_attendance():
    return render_template('mark_attendance.html')

# Edit Student Records Page
@admin.route('/edit_students')
def edit_students():
    return render_template('edit_students.html')
