from flask import Blueprint, render_template, request, redirect, url_for, flash, Response
import cv2
import mediapipe as mp
import face_recognition
import numpy as np
import json
import os
from datetime import datetime, timedelta
from scipy.spatial import distance as dist

from .attendance import load_user_data, preload_encodings, save_attendance_record
from .train import process_frame, save_images

main = Blueprint('main', __name__)

mp_face_mesh = mp.solutions.face_mesh

def eye_aspect_ratio(eye):
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    C = dist.euclidean(eye[0], eye[3])
    ear = (A + B) / (2.0 * C)
    return ear

def detect_blink(face_landmarks, img_width, img_height):
    left_eye_landmarks = [33, 160, 158, 133, 153, 144]
    right_eye_landmarks = [362, 385, 387, 263, 373, 380]
    left_eye = [(face_landmarks.landmark[i].x * img_width, face_landmarks.landmark[i].y * img_height) for i in left_eye_landmarks]
    right_eye = [(face_landmarks.landmark[i].x * img_width, face_landmarks.landmark[i].y * img_height) for i in right_eye_landmarks]
    
    left_ear = eye_aspect_ratio(left_eye)
    right_ear = eye_aspect_ratio(right_eye)

    EAR_THRESHOLD = 0.21
    if left_ear < EAR_THRESHOLD and right_ear < EAR_THRESHOLD:
        return True
    return False

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user_details = {
            'name': request.form['name'],
            'rollNumber': request.form['rollNumber'],
            'email': request.form['email'],
            'branch': request.form['branch']
        }
        cap = cv2.VideoCapture(0)
        known_face_encodings = []
        training_complete = False
        captured_frames = []
        face_encodings = []
        frame_count = 0

        while cap.isOpened() and not training_complete:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame, is_valid, face_encoding = process_frame(frame, known_face_encodings)
            if is_valid:
                frame_count += 1
                captured_frames.append(frame)
                face_encodings.append(face_encoding)
                if frame_count >= 10:
                    save_images(captured_frames, user_details, face_encodings)
                    training_complete = True
                    flash("Training completed successfully!")
            else:
                flash(face_encoding)
        
        cap.release()
        return redirect(url_for('main.index'))
    
    return render_template('register.html')

@main.route('/capture-attendance', methods=['GET'])
def capture_attendance():
    user_data = load_user_data()
    known_face_encodings, known_face_names, known_face_roll_numbers, known_face_branches = preload_encodings(user_data)
    
    cap = cv2.VideoCapture(0)
    attendance_recorded = False
    name = "Unknown"
    roll_number = "Unknown"
    branch = "Unknown"
    blink_count = 0
    last_blink_time = datetime.now()

    with mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True, min_detection_confidence=0.5) as face_mesh:
        while cap.isOpened() and not attendance_recorded:
            ret, frame = cap.read()
            if not ret:
                break

            img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(img_rgb)
            
            if results.multi_face_landmarks:
                face_landmarks = results.multi_face_landmarks[0]
                img_height, img_width, _ = frame.shape

                if detect_blink(face_landmarks, img_width, img_height):
                    current_time = datetime.now()
                    if (current_time - last_blink_time) >= timedelta(seconds=0.5):
                        blink_count += 1
                        last_blink_time = current_time
                        print(f"Blink detected! Blink count: {blink_count}")

                if blink_count >= 4:
                    face_locations = face_recognition.face_locations(frame)
                    face_encodings = face_recognition.face_encodings(frame, face_locations)

                    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                        matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.4)
                        face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                        best_match_index = np.argmin(face_distances)
                        if matches[best_match_index]:
                            name = known_face_names[best_match_index]
                            roll_number = known_face_roll_numbers[best_match_index]
                            branch = known_face_branches[best_match_index]
                            attendance_recorded = True
                            save_attendance_record(name, roll_number, branch)
                            flash(f"Attendance recorded for {name} ({branch})")
                            break
        
            if attendance_recorded:
                break

    cap.release()
    return redirect(url_for('main.index'))

@main.route('/attendance-records')
def view_attendance_records():
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
        attendance_data = [record for record in attendance_data if record['branch'] == branch]
    
    # Search term filter
    if search_term:
        search_term = search_term.lower()
        attendance_data = [record for record in attendance_data if search_term in record['name'].lower() or search_term in record['rollNumber'].lower() or search_term in record['branch'].lower()]

    # Sort by roll number
    if sort == 'rollNumber':
        attendance_data = sorted(attendance_data, key=lambda x: x['rollNumber'])

    return render_template('attendance_records.html', attendance_data=attendance_data)

@main.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

def gen_frames():
    cap = cv2.VideoCapture(0)
    while True:
        success, frame = cap.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    cap.release()
