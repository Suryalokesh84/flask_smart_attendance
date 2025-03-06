from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import json
import os
from datetime import datetime, date
import smtplib
from email.mime.text import MIMEText

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

# ✅ Attendance Records Page
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

# ✅ Manual Attendance Marking Page
@admin.route("/mark_attendance", methods=["GET", "POST"])
def mark_attendance():
    students = []
    selected_branch = None

    if request.method == "POST":
        selected_branch = request.form.get("branch")
        if selected_branch:
            students = get_students_by_branch(selected_branch)

    return render_template("mark_attendance.html", students=students, today_date=date.today(), selected_branch=selected_branch)

# ✅ Edit Student Records Page
@admin.route('/edit_students')
def edit_students():
    return render_template('edit_students.html')

# ✅ Load Students from JSON
def load_students():
    user_data_folder = "user_data"
    students = []
    
    if os.path.exists(user_data_folder):
        for filename in os.listdir(user_data_folder):
            if filename.endswith(".json"):
                file_path = os.path.join(user_data_folder, filename)
                with open(file_path, "r") as f:
                    student_data = json.load(f)
                    students.append(student_data)
    
    return students

# ✅ Get Students by Branch
def get_students_by_branch(branch):
    students = load_students()
    return [s for s in students if s.get("branch") == branch]  # Filter by branch

# ✅ Save Attendance to JSON
def save_attendance(attendance_data):
    with open('attendance.json', 'a') as file:
        json.dump(attendance_data, file)
        file.write('\n')

# ✅ Send Attendance Email
def send_email(absent_students):
    sender_email = "your_email@gmail.com"
    password = os.getenv("EMAIL_PASSWORD")  # ✅ Secure method: Use environment variable
    
    for student_email in absent_students:
        subject = "Attendance Notification"
        body = "Dear user, you are marked absent."
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = sender_email
        msg['To'] = student_email
        
        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(sender_email, password)
            server.sendmail(sender_email, student_email, msg.as_string())
            server.quit()
        except Exception as e:
            print("Error sending email:", e)

# ✅ Edit Attendance Page
@admin.route('/edit_attendance', methods=['GET', 'POST'])
def edit_attendance():
    attendance_data = session.get('attendance_data', {})
    
    if request.method == 'POST':
        updated_records = {}
        absent_students = []
        
        for student_name, status in attendance_data['records'].items():
            new_status = 'Present' if request.form.get(student_name) else 'Absent'
            updated_records[student_name] = new_status
            
            if new_status == 'Absent' and status != 'Absent':
                absent_students.append(student_name)
        
        attendance_data['records'] = updated_records
        save_attendance(attendance_data)
        session['attendance_data'] = attendance_data
        
        if absent_students:
            send_email(absent_students)
        
        flash("Attendance updated successfully!", "info")
        return redirect(url_for('admin.mark_attendance'))
    
    return render_template('edit_attendance.html', attendance_data=attendance_data)


import threading
import smtplib
import datetime
import json
import os
from flask import flash, request, redirect, url_for
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email_notification(name, roll_number, branch, email, status, date, time):
    """ Send email notification after successful attendance """

    subject = "Attendance Update"
    body = f"""
    Dear {name},

    Your attendance has been recorded.

    - Roll Number: {roll_number}
    - Branch: {branch}
    - Date: {date}
    - Time: {time}
    - Status: {"✅ Present" if status.lower() == "present" else "❌ Absent"}


    Best regards,
    Attendance System
    """

    message = MIMEMultipart()
    message["From"] = "smart.attendance.alerts@gmail.com"
    message["To"] = email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    try:
        ob = smtplib.SMTP('smtp.gmail.com', 587)
        ob.starttls()
        ob.login('smart.attendance.alerts@gmail.com', 'zqke rwhz pcoi shep')
        ob.sendmail('smart.attendance.alerts@gmail.com', email, message.as_string())
        ob.quit()
        print(f"Email sent successfully to {email} ({status})!")
    except Exception as e:
        print(f"Failed to send email to {email}. Error: {e}")

@admin.route("/submit_attendance", methods=["POST"])
def submit_attendance():
    """Handles form submission for marking attendance."""
    if request.method == "POST":
        branch = request.form.get("branch")

        # Get current date and time automatically
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.datetime.now().strftime("%H:%M:%S")

        selected_students = request.form.getlist("students")  # List of present students

        # Load all students
        students = get_students_by_branch(branch)

        # Prepare attendance data
        attendance_data = []
        present_count = 0
        absent_count = 0
        email_threads = []

        for student in students:
            status = "Present" if student["rollNumber"] in selected_students else "Absent"
            if status == "Present":
                present_count += 1
            else:
                absent_count += 1

            attendance_data.append({
                "name": student["name"],
                "rollNumber": student["rollNumber"],
                "branch": student["branch"],
                "date": current_date,
                "time": current_time,
                "status": status
            })

            # Send emails asynchronously using threading
            if "email" in student:  # Ensure email exists in the student record
                email_thread = threading.Thread(
                    target=send_email_notification,
                    args=(student["name"], student["rollNumber"], student["branch"], student["email"], status, current_date, current_time)
                )
                email_thread.start()
                email_threads.append(email_thread)

        # Save to JSON file
        if os.path.exists("attendance_records.json"):
            with open("attendance_records.json", "r") as file:
                existing_data = json.load(file)
        else:
            existing_data = []

        existing_data.extend(attendance_data)

        with open("attendance_records.json", "w") as file:
            json.dump(existing_data, file, indent=4)

        total_students = len(students)

        # Flash success message and attendance stats separately
        flash("Attendance marked successfully!", "success")
        flash(f"Total Students: {total_students}", "info")
        flash(f"Present: {present_count}", "info")
        flash(f"Absent: {absent_count}", "info")

        return redirect(url_for("admin.mark_attendance"))

    flash("Invalid request", "error")
    return redirect(url_for("admin.mark_attendance"))
